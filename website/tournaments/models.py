import datetime
import math
from django.db import models

class Bot(models.Model):
  name = models.CharField(max_length=100)
  wins = models.IntegerField()
  losses = models.IntegerField()
  draws = models.IntegerField()

  class Meta:
    ordering = ['name']

  def __unicode__(self):
    return self.name


class Tournament(models.Model):
  STATUS_CHOICES = (
    (u'NS', u'Not Started'),
    (u'IP', u'In Progress'),
    (u'F', u'Finished'), 
  )
  date_played = models.DateTimeField(auto_now_add=True)
  duration = models.IntegerField() 
  status = models.CharField(max_length=2, choices=STATUS_CHOICES)
  bots = models.ManyToManyField(Bot, through='Participant')

  class Meta:
    ordering = ['-date_played']
  
  def __unicode__(self):
    return str(self.date_played)

  def get_name(self):
    return self.date_played.strftime('%Y-%m-%d%p')
  get_name.short_description = 'Name'

  def was_played_today(self):
    return self.date_played.date() == datetime.date.today()
  was_played_today.short_description = 'Played today?'

  def number_of_bots(self):
    return self.bots.count()
  number_of_bots.short_description = '# Bots'

  def get_participants(self):
    return Participant.objects.filter(tournament__id=self.id).order_by('bot__name')

  def get_matrix(self):
    bots = list(self.bots.order_by('name'))
    matrix = [None for j in range(len(bots))]
    for game in self.game_set.all():
      y = bots.index(game.white)
      x = bots.index(game.black)
      if not matrix[y]:
        matrix[y] = dict()
        matrix[y]['bot'] = game.white
        matrix[y]['games'] = [None for i in range(len(bots))]
      matrix[y]['games'][x] = game
    return matrix


class Participant(models.Model):
  tournament = models.ForeignKey(Tournament)
  bot = models.ForeignKey(Bot)
  wins = models.IntegerField()
  losses = models.IntegerField()
  draws = models.IntegerField()

  def get_games_as_white(self):
    return self.tournament.game_set.filter(white__id=self.bot.id).order_by('black__name')

class Game(models.Model):
  WINNER_CHOICES = (
    (u'w', u'white'),
    (u'b', u'black'),
    (u'd', u'draw'),
  )
  tournament = models.ForeignKey(Tournament)
  result_file = models.FileField(
      upload_to=lambda game,filename: 'tournaments/results/%s/%s_vs_%s.txt' % (game.tournament.get_name(), game.white.name, game.black.name))
  white = models.ForeignKey(Bot, related_name='games_as_white')
  black = models.ForeignKey(Bot, related_name='games_as_black')
  winner = models.CharField(max_length=1, choices=WINNER_CHOICES)

  def __unicode__(self):
    return self.white.name + ' v. ' + self.black.name

  def get_score(self):
    if self.winner == Game.WINNER_CHOICES[0]:
      return '1 - 0'
    if self.winner == Game.WINNER_CHOICES[1]:
      return '0- 1'
    return '1/2 - 1/2'


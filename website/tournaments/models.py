import datetime
import math
from django.db import models

class Bot(models.Model):
  is_deleted = models.IntegerField(default=0)
  name = models.CharField(max_length=100)
  wins = models.IntegerField(default=0)
  losses = models.IntegerField(default=0)
  draws = models.IntegerField(default=0)

  class Meta:
    ordering = ['name']

  def __unicode__(self):
    return self.name

  def delete(self, *args, **kwargs):
    self.is_deleted = 1
    self.save()


class Tournament(models.Model):
  STATUS_CHOICES = (
    (u'NS', u'Not Started'),
    (u'IP', u'In Progress'),
    (u'F', u'Finished'), 
  )
  is_deleted = models.IntegerField(default=0)
  date_played = models.DateTimeField(auto_now_add=True)
  duration = models.IntegerField(default=0.0) 
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

  def delete(self, *args, **kwargs):
    self.is_deleted = 1
    self.save()


class Participant(models.Model):
  tournament = models.ForeignKey(Tournament)
  bot = models.ForeignKey(Bot)
  wins = models.IntegerField(default=0)
  losses = models.IntegerField(default=0)
  draws = models.IntegerField(default=0)
  number_of_moves = models.IntegerField(default=0)
  time = models.FloatField(default=0.0)
  errors = models.IntegerField(default=0)
  
  def get_average_number_of_moves(self):
    games = self.wins + self.losses + self.draws
    if games == 0:
      return 0.0
    return round((self.moves / games), 1);
  get_average_number_of_moves.short_description = 'Moves (Avg)'

  def get_average_time_per_move(self):
    if self.number_of_moves == 0:
      return 0.0
    return round((self.time / self.number_of_moves), 1);
  get_average_time_per_move.short_description = 'Time Per Move (Avg)'
  
  def get_winning_percentage(self):
    games = self.wins + self.losses + self.draws
    if games == 0:
      return 0.0
    return round((self.wins / games), 3);
  get_winning_percentage.short_description = 'Winning Pct'

  def get_games_as_white(self):
    return self.tournament.game_set.filter(white__id=self.bot.id).order_by('black__name')


class Game(models.Model):
  WINNER_CHOICES = (
    (u'w', u'white'),
    (u'b', u'black'),
    (u'd', u'draw'),
  )
  tournament = models.ForeignKey(Tournament)
  date_played = models.DateTimeField(auto_now_add=True)
  duration = models.FloatField(default=0.0)
  number_of_moves = models.IntegerField(default=0)
  result_file = models.FileField(
      upload_to=lambda game,filename: 'tournaments/results/%s/%s_vs_%s.txt' % (game.tournament.get_name(), game.white.name, game.black.name))
  white = models.ForeignKey(Bot, related_name='games_as_white')
  black = models.ForeignKey(Bot, related_name='games_as_black')
  winner = models.CharField(max_length=1, choices=WINNER_CHOICES)

  def __unicode__(self):
    return self.white.name + ' v. ' + self.black.name


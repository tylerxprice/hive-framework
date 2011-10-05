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
  bots = models.ManyToManyField(Bot)

  class Meta:
    ordering = ['-date_played']
  
  def __unicode__(self):
    return self.date_played

  def was_played_today(self):
    return self.date_played.date() == datetime.date.today()
  was_played_today.short_description = 'Played today?'

  def number_of_bots(self):
    return len(self.bot_set)
  number_of_bots.short_description = '# Bots'


class Game(models.Model):
  WINNER_CHOICES = (
    (u'w', u'white'),
    (u'b', u'black'),
    (u'd', u'draw'),
  )
  tournament = models.ForeignKey(Tournament)
  result_file = models.FileField(upload_to='/tournaments/results/')
  white = models.ForeignKey(Bot, related_name='games_as_white')
  black = models.ForeignKey(Bot, related_name='games_as_black')
  winner = models.CharField(max_length=1, choices=WINNER_CHOICES)

  def __unicode__(self):
    return self.white.name + ' v. ' + self.black.white


# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Bot'
        db.create_table('tournaments_bot', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('wins', self.gf('django.db.models.fields.IntegerField')()),
            ('losses', self.gf('django.db.models.fields.IntegerField')()),
            ('draws', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('tournaments', ['Bot'])

        # Adding model 'Tournament'
        db.create_table('tournaments_tournament', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date_played', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('duration', self.gf('django.db.models.fields.IntegerField')()),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=2)),
        ))
        db.send_create_signal('tournaments', ['Tournament'])

        # Adding model 'Participant'
        db.create_table('tournaments_participant', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('tournament', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tournaments.Tournament'])),
            ('bot', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tournaments.Bot'])),
            ('wins', self.gf('django.db.models.fields.IntegerField')()),
            ('losses', self.gf('django.db.models.fields.IntegerField')()),
            ('draws', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('tournaments', ['Participant'])

        # Adding model 'Game'
        db.create_table('tournaments_game', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('tournament', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tournaments.Tournament'])),
            ('result_file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('white', self.gf('django.db.models.fields.related.ForeignKey')(related_name='games_as_white', to=orm['tournaments.Bot'])),
            ('black', self.gf('django.db.models.fields.related.ForeignKey')(related_name='games_as_black', to=orm['tournaments.Bot'])),
            ('winner', self.gf('django.db.models.fields.CharField')(max_length=1)),
        ))
        db.send_create_signal('tournaments', ['Game'])


    def backwards(self, orm):
        
        # Deleting model 'Bot'
        db.delete_table('tournaments_bot')

        # Deleting model 'Tournament'
        db.delete_table('tournaments_tournament')

        # Deleting model 'Participant'
        db.delete_table('tournaments_participant')

        # Deleting model 'Game'
        db.delete_table('tournaments_game')


    models = {
        'tournaments.bot': {
            'Meta': {'ordering': "['name']", 'object_name': 'Bot'},
            'draws': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'losses': ('django.db.models.fields.IntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'wins': ('django.db.models.fields.IntegerField', [], {})
        },
        'tournaments.game': {
            'Meta': {'object_name': 'Game'},
            'black': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'games_as_black'", 'to': "orm['tournaments.Bot']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'result_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'tournament': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tournaments.Tournament']"}),
            'white': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'games_as_white'", 'to': "orm['tournaments.Bot']"}),
            'winner': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'tournaments.participant': {
            'Meta': {'object_name': 'Participant'},
            'bot': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tournaments.Bot']"}),
            'draws': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'losses': ('django.db.models.fields.IntegerField', [], {}),
            'tournament': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tournaments.Tournament']"}),
            'wins': ('django.db.models.fields.IntegerField', [], {})
        },
        'tournaments.tournament': {
            'Meta': {'ordering': "['-date_played']", 'object_name': 'Tournament'},
            'bots': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['tournaments.Bot']", 'through': "orm['tournaments.Participant']", 'symmetrical': 'False'}),
            'date_played': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'duration': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        }
    }

    complete_apps = ['tournaments']

# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Tournament.is_deleted'
        db.add_column('tournaments_tournament', 'is_deleted', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Adding field 'Bot.is_deleted'
        db.add_column('tournaments_bot', 'is_deleted', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Tournament.is_deleted'
        db.delete_column('tournaments_tournament', 'is_deleted')

        # Deleting field 'Bot.is_deleted'
        db.delete_column('tournaments_bot', 'is_deleted')


    models = {
        'tournaments.bot': {
            'Meta': {'ordering': "['name']", 'object_name': 'Bot'},
            'draws': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'losses': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'wins': ('django.db.models.fields.IntegerField', [], {'default': '0'})
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
            'draws': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'errors': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'losses': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'number_of_moves': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'time': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'tournament': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tournaments.Tournament']"}),
            'wins': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'tournaments.tournament': {
            'Meta': {'ordering': "['-date_played']", 'object_name': 'Tournament'},
            'bots': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['tournaments.Bot']", 'through': "orm['tournaments.Participant']", 'symmetrical': 'False'}),
            'date_played': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'duration': ('django.db.models.fields.IntegerField', [], {'default': '0.0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        }
    }

    complete_apps = ['tournaments']

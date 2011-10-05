from tournaments.models import Bot, Game, Tournament
from django.contrib import admin

# class GameInline(admin.TabularInline):
#   model = Game
#   extra = 1
#   
#
# class TournamentAdmin(admin.ModelAdmin):
#   fieldsets = [
#     (None,  {'fields': ['duration', 'status']}),
#     ('Date information', {'fields': ['date_played'], 'classes': ['collapse']})
#   ]
#   inlines = [GameInline]
#   list_display = ('date_played', 'duration', 'number_of_bots', 'get_status_display')
#   list_filter = ['pub_date']
#   #search_fields = ['question']
#   #date_hierarchy = 'pub_date'
#

admin.site.register(Bot)
admin.site.register(Tournament)


from django.contrib import admin

from unfold.admin import ModelAdmin

from voter.models import Voter, Vote


@admin.register(Voter)
class VoterAdmin(ModelAdmin):
    pass


@admin.register(Vote)
class VoteAdmin(ModelAdmin):
    pass

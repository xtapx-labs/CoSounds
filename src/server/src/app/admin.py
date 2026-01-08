import json

from django.contrib import admin
from django.apps import apps as django_apps
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from django_file_form.model_admin import FileFormAdmin
from unfold.admin import ModelAdmin
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import FieldTextFilter
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from app.models import Cosound, Sound, Player, Vote
from app.forms import SoundForm

model = django_apps.get_model("django_file_form", "TemporaryUploadedFile")
admin.site.unregister(model)


@admin.register(Sound)
class SoundAdmin(FileFormAdmin, ModelAdmin):  # type: ignore
    form = SoundForm

    class Media:
        js = ("https://cdn.jsdelivr.net/npm/chart.js",)

    def nvec_radar_chart(self, obj):
        if not obj or not obj.nvec:
            return "No Natural Vector data available."

        data = {
            "rain": obj.nvec.rain,
            "sea_waves": obj.nvec.sea_waves,
            "thunderstorm": obj.nvec.thunderstorm,
            "wind": obj.nvec.wind,
            "crackling_fire": obj.nvec.crackling_fire,
        }

        html = render_to_string(
            "admin/app/sound/nvec_chart.html", {"nvec_data": json.dumps(data)}
        )
        return mark_safe(html)

    nvec_radar_chart.short_description = "Natural Vector Classification"  # type: ignore

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["nvec_radar_chart"]
        return []


@admin.register(Player)
class PlayerAdmin(ModelAdmin):
    pass


@admin.register(Cosound)
class CosoundAdmin(ModelAdmin):
    pass


@admin.register(Vote)
class VoteAdmin(ModelAdmin):
    pass

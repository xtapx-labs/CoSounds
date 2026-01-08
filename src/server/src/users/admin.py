from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import FieldTextFilter
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from users.models import Client, Voter, User


admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):

    class Meta:
        model = User
        verbose_name = "Usersfsf"

    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    list_filter_submit = True
    list_filter = [("email", FieldTextFilter)]


@admin.register(Client)
class ClientAdmin(ModelAdmin):
    list_display = ("name", "user", "token")
    readonly_fields = ("token",)


@admin.register(Voter)
class VoterAdmin(ModelAdmin):
    pass

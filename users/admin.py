from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.models import Account, Server

# Register your models here.

class AccountAdmin(UserAdmin):
    list_display = ('email', 'date_joined', 'last_login', 'is_admin', 'is_staff')
    list_filter = ['date_joined']
    search_fields = ('email', 'username',)
    readonly_fields = ('date_joined', 'last_login')

    filter_horizontal = ()
    fieldsets = ()


admin.site.register(Account, AccountAdmin)
admin.site.register(Server)

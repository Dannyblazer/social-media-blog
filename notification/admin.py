from django.contrib import admin

# Register your models here.

from notification.models import Notification

class NotificationAdmin(admin.ModelAdmin):
    list_filter     = ['content_type']
    list_display    = ['target', 'content_type', 'timestamp']
    search_fields   = ['target__username', 'target__email']

    class Meta:
        model = Notification

admin.site.register(Notification, NotificationAdmin)
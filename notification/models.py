from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
# Create your models here.

class Notification(models.Model):
    # Who receives the notification
    target          = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # User who intitiated the notifiction
    from_user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="from_user")
    # Url for each notification to target user acc.
    redirect_url    = models.URLField(max_length=255, null=True, unique=False, blank=True, help_text="The URL to redirect to when clicked")
    # Statement describing the notification (ex: Daniel sent you a friend request.)
    verb            = models.CharField(max_length=100, unique=False, blank=True, null=True)
    timestamp       = models.DateTimeField(auto_now_add=True)
    read            = models.BooleanField(default=False)
    content_type    = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id       = models.PositiveIntegerField()
    content_object  = GenericForeignKey()

    def __str__(self):
        return self.verb

    def get_content_object_type(self):
        return str(self.content_object.get_cname) 


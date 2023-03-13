from django.db import models
from django.conf import settings

# Create your models here.


class PrivateChatRoom(models.Model):
    """
    Private chat between two users (friends)"""
    
    user1       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user1")
    user2       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user2")
    is_active   = models.BooleanField(default=True)

    def __str__(self):
        return "A chat between {} and {}".format(self.user1, self.user2)
    
    @property
    def group_name(self):
        """ Return the channels group name that sockets should subscribe to receive private chat messages (pair-wise) """
        
        return f"PrivateChatRoom-{self.id}"
    
class RoomChatMessageManager(models.Manager):
    def by_room(self, room):
        qs = RoomChatMessage.objects.filter(room=room).order_by("-timestamp")
        return qs

class RoomChatMessage(models.Model):
    """ Chat message created by a user within a room (pair-wise) """

    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    room        = models.ForeignKey(PrivateChatRoom, on_delete=models.CASCADE)
    timestamp   = models.DateTimeField(auto_now_add=True)
    content     = models.TextField(unique=False, blank=False)

    objects = RoomChatMessageManager()

    def __st__(self):
        return self.content




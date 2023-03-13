from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import PrivateChatRoom, RoomChatMessage
from django.core.paginator import Paginator
from django.core.cache import cache
from django.db import models

# Register your models here.

class PrivateChatRoomAdin(admin.ModelAdmin):
    list_display = ['id', 'user1', 'user2']
    search_fields = ['id', 'user1', 'user2']
    readonly_fields = ['id']
    

    class Meta:
        model = PrivateChatRoom

admin.site.register(PrivateChatRoom, PrivateChatRoomAdin)


# Resource: Http://masnum.rocks/2017/03/20/django-admin-expensive-count-all-queries/
class CachingPaginator(Paginator):
    def _get_count(self):

        if not hasattr(self, "_count"):
            self._count = None

        if self._count is None:
            try:
                key = "adm:{0}:count".format(hash(self.object_list.query.__str__()))
                self._count = cache.get(key, -1)
                if self._count == -1:
                    self._count = super().count
                    cache.set(key, self._count, 3600)

            except:
                self._count = len(self.object_list)
        return self._count

    count = property(_get_count)    


class RoomChatMessageAdmin(admin.ModelAdmin):
    list_filter = ['room', 'user', 'timestamp']
    list_display = ['room', 'user', 'timestamp', 'content']
    search_fields = ['user', 'content']
    readonly_fields = ['id', 'user', 'room', 'timestamp']

    show_full_result_count = False
    paginator = CachingPaginator

    class Meta:
        model = RoomChatMessage

admin.site.register(RoomChatMessage, RoomChatMessageAdmin)


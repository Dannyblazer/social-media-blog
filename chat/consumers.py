from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.serializers import serialize
from django.utils import timezone
from django.core.paginator import Paginator

import json
import asyncio

from chat.models import RoomChatMessage, PrivateChatRoom
from friend.models import FriendList
#from users.utils import LazyAccountEncoder
from chat.utils import calculate_timestamp, LazyRoomChatMessageEncoder
from public_chat.consumers import ClientError
from public_chat.constants import *
from users.models import Account


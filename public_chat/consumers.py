from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json
from django.conf import settings
from django.core.serializers.python import Serializer
from django.core.paginator import Paginator
from channels.db import database_sync_to_async
from django.utils import timezone
from chat.utils import *
from notification.utils import *
from notification.constants import *
from chat.constants import *
from public_chat.models import PublicChatRoom, PublicRoomChatMessage, PublicRoomChatMessage
from public_chat.constants import *

class PublicChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        """Called during socket handshaking"""
        await self.accept()
        self.room_id = None

    async def disconnect(self, close_code):
        # Leave room group
        try:
            if self.room_id != None:
                await self.leave_room(self.room_id)
        except Exception:
            pass

    # Receive message from WebSocket
    async def receive_json(self, content):
        command = content.get("command", None)
        try:
            if command == "send":
                if len(content["message"].lstrip()) == 0:
                    raise ClientError(422, "You can't send an empty message!")
                    # Send message to room group via send_message()
                await self.send_room(content["room_id"], content["message"])
            elif command == "join":
                await self.join_room(content["room"])
            elif command == "leave":
                await self.leave_room(content['room_id'])
            elif command == "get_room_chat_messages":
                await self.display_progress_bar(True)
                room = await get_room_or_error(content['room_id'])
                payload = await get_room_chat_messages(room, content['page_number'])
                if payload != None:
                    payload = json.loads(payload)
                    await self.send_messages_payload(payload['messages'], payload['new_page_number'])
                else:
                    raise ClientError(204, "Something went wrong retriving chatroom messages.")
                await self.display_progress_bar(False)
        except ClientError as e:
            await self.display_progress_bar(False)
            await self.handle_client_error(e)

    
    async def send_room(self, room_id, message):
        """Called by receive_json when someone messages a room"""
        if self.room_id != None:
            if str(room_id) != str(self.room_id):
                raise ClientError("ROOM ACCESS DENIED", "Room access denied")
            if not is_authenticated(self.scope['user']):
                raise ClientError("AUTH_ERROR", "You must be authenticated to chat")
        else:
            raise ClientError("ROOM_ACCESS_DENIED", "Room access denied.")
        
        room = await get_room_or_error(room_id)
        await create_public_room_chat_message(room, self.scope['user'], message)

        await self.channel_layer.group_send(
            room.group_name, 
            {
                "type": "chat.message",
                "profile_image": self.scope['user'].profile_image.url,
                "username": self.scope['user'].username,
                "user_id": self.scope['user'].id,
                'message': message,
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]

        timestamp = calculate_timestamp(timezone.now())
        # Send message to WebSocket
        await self.send_json({
            'msg_type': MSG_TYPE_MESSAGE,
            "profile_image": event['profile_image'],
            "username": event['username'],
            "user_id": event['user_id'],
            "message": event['message'],
            "naturalday": timestamp,
        },)

    async def send_messages_payload(self, messages, new_page_number):
        """Sends a payload of messages to the UI"""
        await self.send_json({
            "messages_payload": "messages_payload",
            "messages": messages,
            "new_page_number": new_page_number,
        })
    
    async def join_room(self, room_id):
        """Called by receive_json when someone sent a JOIN command"""
        is_auth = is_authenticated(self.scope['user'])
        try:
            room = await get_room_or_error(room_id)
        except ClientError as e:
            await self.handle_client_error(e)

        # Add user from users list
        if is_auth:
            await connect_user(room, self.scope['user'])

        # store that we are in the room
        self.room_id = room_id
        # Send a join response to client socket
        await self.send_json({
            "join":"join",
            "room_id": room_id,
            "user": self.scope['user'].username,
        })
        # Add from the group
        await self.channel_layer.group_add(
            room.group_name, self.channel_name
        )
        # Payload sent to update connected users UI
        num_connected_users = await get_num_connected_users(room)
        await self.channel_layer.group_send(
            room.group_name,
            {
                "type": "connected_user_count",
                "connected_user_count": num_connected_users
            }
        )

    async def handle_client_error(self, e):
        """Called when clientError is raised. Send err to UI"""
        errorData = {}
        errorData['error'] = e.code
        if e.message:
            errorData['message'] = e.message
            await self.send_json(errorData)
        return

    
    async def leave_room(self, room_id):
        """Called by receive_json when someone sent a LEAVE command"""
        is_auth = is_authenticated(self.scope['user'])
        try:
            room = await get_room_or_error(room_id)
        except ClientError as e:
            await self.handle_client_error(e)

        # Remove user from users list
        if is_auth:
            await disconnect_user(room, self.scope['user'])

        # Remove from the group
        await self.channel_layer.group_discard(
            room.group_name, self.channel_name
        )
        # Payload sent when a user leaves the group
        num_connected_users = await get_num_connected_users(room)
        await self.channel_layer.group_send(
            room.group_name,
            {
                "type": "connected_user_count",
                "connected_user_count": num_connected_users
            }
        )
        print("Someone left: " + str(num_connected_users))

    async def display_progress_bar(self, is_displayed):
        """Payload sent whenever there's a message payload being sent"""
        await self.send_json({
            "display_progress_bar": is_displayed
        })

    async def connected_user_count(self, event):
        """Called to send the number of connected users to the group chat"""
        await self.send_json({
            "msg_type": MSG_TYPE_CONNECTED_USER_COUNT,
            "connected_user_count": event['connected_user_count']
        })

@database_sync_to_async
def get_num_connected_users(room):
    if room.users:
        return len(room.users.all())
    else:
        return 0
        
def is_authenticated(user):
    if user.is_authenticated:
        return True
    return False

@database_sync_to_async
def connect_user(room, user):
    return room.connect_user(user)

@database_sync_to_async
def disconnect_user(room, user):
    return room.disconnect_user(user)

@database_sync_to_async
def create_public_room_chat_message(room, user, message):
    return PublicRoomChatMessage.objects.create(room=room, user=user, content=message)

@database_sync_to_async
def get_room_or_error(room_id):
    """ Tried to fetch a room for the user"""
    try:
        room = PublicChatRoom.objects.get(pk=room_id)
    except PublicChatRoom.DoesNotExist:
        raise ClientError("ROOM_INVALID", "Invalid room")
    return room

class ClientError(Exception):
    """
    Custom exception class that is caught by the webscoket receive()
    handler and translated into a send back to the client
    """
    def __init__(self, code, message):
        super().__init__(code)
        self.code = code
        if message:
            self.message = message


@database_sync_to_async
def get_room_chat_messages(room, page_number):
    try:
        qs = PublicRoomChatMessage.objects.filter(room=room).order_by("-timestamp")
        p = Paginator(qs, DEFAULT_ROOM_CHAT_MESSAGE_PAGE_SIZE)
        
        payload = {}
        new_page_number =int(page_number)
        if new_page_number <= p.num_pages:
            new_page_number = new_page_number + 1
            s = LazyRoomChatMessageEncoder()
            payload['messages'] = s.serialize(p.page(page_number).object_list)
        else:
            payload['messages'] = "None"
        payload['new_page_number'] = new_page_number
        return json.dumps(payload)    
    except Exception as e:
        print("EXCEPTION bottom: " + str(e))
        return None

class LazyRoomChatMessageEncoder(Serializer):
    def get_dump_object(self, obj):
        dump_object = {}
        dump_object.update({'msg_type': MSG_TYPE_MESSAGE})
        dump_object.update({'user_id': str(obj.user.id)})
        dump_object.update({'msg_id': str(obj.id)})
        dump_object.update({'message': str(obj.content)})
        dump_object.update({'username': str(obj.user.username)})
        dump_object.update({'profile_image': str(obj.user.profile_image.url)})
        dump_object.update({'naturalday': str(calculate_timestamp(obj.timestamp))})
        return dump_object


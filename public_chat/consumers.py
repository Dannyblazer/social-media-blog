from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json
from users.utils import LazyAccountEncoder
from django.core.serializers.python import Serializer
from django.core.paginator import Paginator
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from chat.utils import *
from chat.constants import *
from friend.models import FriendList
from chat.models import PrivateChatRoom, RoomChatMessage
from public_chat.models import PublicChatRoom, PublicRoomChatMessage, PublicRoomChatMessagesManager
from public_chat.constants import *

user = get_user_model()

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






# Private Chat Room consumer


class ChatConsumer(AsyncJsonWebsocketConsumer):

	async def connect(self):
		"""
		Called when the websocket is handshaking as part of initial connection.
		"""
		print("ChatConsumer: connect: " + str(self.scope["user"].username))

		# let everyone connect. But limit read/write to authenticated users
		await self.accept()

		# the room_id will define what it means to be "connected". If it is not None, then the user is connected.
		self.room_id = None


	async def receive_json(self, content):
		"""
		Called when we get a text frame. Channels will JSON-decode the payload
		for us and pass it as the first argument.
		"""
		# Messages will have a "command" key we can switch on
		print("ChatConsumer: receive_json")
		command = content.get("command", None)
		try:
			if command == "join":
				print("Join Command detected!")
				await self.join_room(content['room'])
			elif command == "leave":
				# Leave the room
				await self.leave_room(content['room'])
			elif command == "send":
				if len(content['message'].lstrip()) != 0:
					await self.send_room(content['room'], content['message'])
			elif command == "get_room_chat_messages":
				print("ASking for messages!")
				await self.display_progress_bar(True)
				room = await get_room_or_error2(content['room_id'], self.scope['user'])
				payload = await get_room_chat_messages2(room, content['page_number'])
				if payload != None:
					payload = json.loads(payload)
					await self.send_messages_payload(payload['messages'], payload['new_page_number'])
				else:
					raise Exception("Something went wrong retrieving the chatroom messages.")
				await self.display_progress_bar(False)
			elif command == "get_user_info":
				await self.display_progress_bar(True)
				room = await get_room_or_error2(content['room_id'], self.scope["user"])
				payload = get_user_info(room, self.scope["user"])
				if payload != None:
					payload = json.loads(payload)
					await self.send_user_info_payload(payload['user_info'])
				else:
					raise Exception("Something went wrong retrieving the other users account details.")
		except Exception as e:
			pass


	async def disconnect(self, code):
		"""
		Called when the WebSocket closes for any reason.
		"""
		# Leave the room
		print("ChatConsumer: disconnect")
		try:
			if self.room_id != None:
				await self.leave_room(self.room_id)
		except Exception as e:
			pass

	async def join_room(self, room_id):
		"""
		Called by receive_json when someone sent a join command.
		"""
		# The logged-in user is in our scope thanks to the authentication ASGI middleware (AuthMiddlewareStack)
		print("ChatConsumer: join_room: " + str(room_id))
		try:
			room = await get_room_or_error2(room_id, self.scope['user'])
		except Exception as e:
			return
        
        #store that we're in the room
		self.room_id = room.id
        # Add them to the group, so that they get room messages
		await self.channel_layer.group_add(
            room.group_name,
            self.channel_name
        )

		await self.send_json({
            "join": str(room.id)
        })
		

		# Add them to the group so they get room messages

		# Instruct their client to finish opening the room

	async def leave_room(self, room_id):
		"""
		Called by receive_json when someone sent a leave command.
		"""
		# The logged-in user is in our scope thanks to the authentication ASGI middleware
		print("ChatConsumer: leave_room")
		
		room = await get_room_or_error2(room_id, self.scope['user'])

		# Notify the group that someone left
		await self.channel_layer.group_send(
            room.group_name,
            {
                "type": "chat.leave", # chat_leave function
                "room_id": room_id,
                "profile_image": self.scope['user'].profile_image.url,
                "username": self.scope['user'].username,
                "user_id": self.scope['user'].id,
            }
        )

		# Remove that we're in the room
		self.room_id = None

		# Remove them from the group so they no longer get room messages
		await self.channel_layer.group_discard(
            room.group_name,
            self.channel_name
        )
        
		# Instruct their client to finish closing the room
		


	async def send_room(self, room_id, message):
		"""
		Called by receive_json when someone sends a message to a room.
		"""
		print("ChatConsumer: send_room")
		# Check they are in this room
		if self.room_id != None:
			if str(room_id) != str(self.room_id):
				print("CLIENT ERRROR 1")
				raise ClientError("ROOM_ACCESS_DENIED", "Room access denied")
		else:
			print("CLIENT ERRROR 2")
			raise ClientError("ROOM_ACCESS_DENIED", "Room access denied")
		room = await get_room_or_error2(room_id, self.scope['user'])

		await create_room_chat_message(room, self.scope['user'], message)
		await self.channel_layer.group_send(
            room.group_name,
            {
                "type": "chat.message", # chat_message async function
                "profile_image": self.scope['user'].profile_image.url,
                "username": self.scope['user'].username,
                "user_id": self.scope['user'].id,
                "message": message,
            }
        )




	# These helper methods are named by the types we send - so chat.join becomes chat_join
	async def chat_join(self, event):
		"""
		Called when someone has joined our chat.
		"""
		# Send a message down to the client
		print("ChatConsumer: chat_join: " + str(self.scope["user"].id))
		if event["username"]:
			await self.send_json(
				{
					"msg_type": MSG_TYPE_ENTER2,
					"room": event["room_id"],
					"profile_image": event["profile_image"],
					"username": event["username"],
					"user_id": event["user_id"],
					"message": event["username"] + " connected.",
				},
			)

	async def chat_leave(self, event):
		"""
		Called when someone has left our chat.
		"""
		# Send a message down to the client
		pass


	async def chat_message(self, event):
		"""
		Called when someone has messaged our chat.
		"""
		# Send a message down to the client
		print("ChatConsumer: chat_message")

		timestamp = calculate_timestamp(timezone.now())
		
		await self.send_json({
            "msg_type": MSG_TYPE_MESSAGE2,
            "username": event['username'],
            "user_id": event['user_id'],
            "profile_image": event['profile_image'],
            "message": event['message'],
            "natural_timestamp": timestamp,

        })
    
	async def send_messages_payload(self, messages, new_page_number):
		"""
 		Send a payload of messages to the client sockets"""        
		print("ChatConsumer: send_messages_payload. ")
		await self.send_json({
			"messages_payload": "messages_payload",
			"messages": messages,
            "new_page_number": new_page_number,
		})
		

	async def send_user_info_payload(self, user_info):
		"""
		Send a payload of user information to the ui
		"""
		print("ChatConsumer: send_user_info_payload. ")
		await self.send_json(
			{
				"user_info": user_info,
			},
		)

	async def display_progress_bar(self, is_displayed):
		"""
		1. is_displayed = True
		- Display the progress bar on UI
		2. is_displayed = False
		- Hide the progress bar on UI
		"""
		print("DISPLAY PROGRESS BAR: " + str(is_displayed))
		await self.send_json(
			{
				"display_progress_bar": is_displayed
			}
		)


	async def handle_client_error(self, e):
		"""
		Called when a ClientError is raised.
		Sends error data to UI.
		"""
		errorData = {}
		errorData['error'] = e.code
		if e.message:
			errorData['message'] = e.message
			await self.send_json(errorData)
		return

@database_sync_to_async
def get_room_or_error2(room_id, user):
    """
     Tries to fetch a room for the user, checking permissions along the way
    """
    try:
        room = PrivateChatRoom.objects.get(pk=room_id)
    except PrivateChatRoom.DoesNotExist:
        raise Exception("Invalid Room.")

    # Is this user allowed into this room?
    if user != room.user1 and user != room.user2:
        raise Exception("You do not have permission to join this room.")

    # Are the users in the room friend?
    friend_list = FriendList.objects.get(user=user).friends.all()
    if not room.user1 in friend_list:
        if not room.user2 in friend_list:
             raise Exception("You must be friends to chat.")
    return room

import json

def get_user_info(room, user):
    """
    Retrieve the user info for the user you're chatting with.
    """
    try:
        # Determine who is who
        other_user = room.user1 if room.user1 != user else room.user2
        s = LazyAccountEncoder()
        final = s.serialize([other_user])[0]
        payload = {'user_info': final}
        # Using dumps() instead of dump() to return JSON as a string
        return json.dumps(payload, indent=4, sort_keys=True, default=str)

    except Exception as e:
        print("EXCEPTION: " + str(e))
        return None

    
@database_sync_to_async
def create_room_chat_message(room, user, message):
     return RoomChatMessage.objects.create(user=user, room=room, content=message)

@database_sync_to_async
def get_room_chat_messages2(room, page_number):
    try:
        qs = RoomChatMessage.objects.by_room(room)
        p = Paginator(qs, DEFAULT_ROOM_CHAT_MESSAGE_PAGE_SIZE1)

        payload = {}
        new_page_number = int(page_number)
        if new_page_number <= p.num_pages:
            new_page_number = new_page_number + 1
            s = LaxyRoomChatMessageEncoder2()
            payload['messages'] = s.serialize(p.page(page_number).objects_list)
        else:
            payload['messages'] = None
        payload['new_page_number'] = new_page_number
        return json.dumps(payload)
    except Exception as e:
        print("EXCEPTION last: " + str(e))
    return None



from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json
from django.contrib.auth import get_user_model

user = get_user_model()


class PublicChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        '''
        Called when the websocket is handshaking as part of initial connection
        '''
        print("PublicChatConsumer: Connect: " + str(self.scope['user']))
        await self.accept()

    async def disconnect(self, code):
        """
        Called when the websocket closes for any reason
        """
        print("PublicChatConsumer: disconnect")
        pass

    async def receive(self, content):
        """
        Called when we get a text frame. Channels will JSON-decode the payload for us and pass is as the first argument
        """
        command = content.get("command", None)
        print("PublicChatConsumer: receiver_json: " + str(command))



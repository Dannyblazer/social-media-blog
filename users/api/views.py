from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from users.api.serializers import RegistrationSerializer, AccountPropertiesSerializer
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['POST', ])
def registration_view(request):
	if request.method=='POST':
		data = {}
		serializer = RegistrationSerializer(data=request.data)
		if serializer.is_valid():
			account = serializer.save()
			data['response'] = 'Successfully registered a new user'
			data['email'] = account.email
			data['username'] = account.username
			token = Token.objects.get(user=account).key
			data['token'] = token
		else:
			data = serializer.errors
		return Response(data)


@api_view(['GET',])
@permission_classes((IsAuthenticated,))
def account_properties_view(request):
	try:
		account = request.user
	except Account.DoesNotExist:
		return Response(status=status.HTTP_400_NOT_FOUND)
	
	if request.method == 'GET':
		serializer = AccountPropertiesSerializer(account)
		return Response(serializer.data)

@api_view(['PUT',])
@permission_classes((IsAuthenticated,))
def update_account_view(request):
	try:
		account = request.user
	except Account.DoesNotExist:
		return Response(status=status.HTTP_400_NOT_FOUND)
	
	if request.method == 'PUT':
		serializer = AccountPropertiesSerializer(account, data=request.data)
		data = {}
		if serializer.is_valid():
			serializer.save()
			data['response'] = "Account update success"
			return Response(data=data)
		return Response(serializer.error, status=status.HTTP_404_BAD_REQUEST)


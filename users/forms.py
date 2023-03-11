from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate

from users.models import Account, Server

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(max_length=60)
    required_css_class = 'bold'

    class Meta:
        model = Account
        fields = {"email", "username", "password1", "password2"}
    
    field_order = ['email', 'username',]

    

class AccountAuthenticationForm(forms.ModelForm):
    password = forms.CharField(label='password', widget=forms.PasswordInput)

    class Meta:
        model = Account
        fields = ('email', 'password')

    def clean(self):
        if self.is_valid():
            email = self.cleaned_data['email']
            password = self.cleaned_data['password']
            if not authenticate(email=email, password=password):
                raise forms.ValidationError("Invalid login")

class AccountUpdateForm(forms.ModelForm):
    
    class Meta:
        model = Account
        fields = ('email', 'username', 'first_name', 'last_name', 'bio', 'role', 'profile_image', 'hide_email')
    
    def clean_email(self):
        if self.is_valid():
            email = self.cleaned_data['email']
            try:
                account = Account.objects.exclude(pk=self.instance.pk).get(email=email)
            except Account.DoesNotExist:
                return email
            raise forms.ValidationError("Email {} is already in use.".format(email))
    
    def clean_username(self):
        if self.is_valid():
            username = self.cleaned_data['username']
            try:
                account = Account.objects.exclude(pk=self.instance.pk).get(username=username)
            except Account.DoesNotExist:
                return username
            raise forms.ValidationError("Username {} is already in use.".format(username))
    
    def save(self, commit=True):
        account = super(AccountUpdateForm, self).save(commit=False)
        account.username = self.cleaned_data['username']
        account.email = self.cleaned_data['email']
        account.first_name = self.cleaned_data['first_name']
        account.last_name = self.cleaned_data['last_name']
        account.bio = self.cleaned_data['bio']
        account.role = self.cleaned_data['role']
        account.profile_image = self.cleaned_data['profile_image']
        account.hide_email = self.cleaned_data['hide_email']
        if commit:
            account.save()
        return account
    
class ServerRegistrationForm(forms.ModelForm):

    class Meta:
        model = Server
        fields = {'ip', 'port'}


'''class ProfileForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = {'first_name', 'last_name', 'bio', 'role'}
        exclude = ("user", "follows", )
  
    def save(self, commit=True):
        prof = self.instance
        prof.first_name = self.cleaned_data['first_name']
        prof.last_name = self.cleaned_data['last_name']
        prof.bio = self.cleaned_data['bio']
        prof.role = self.cleaned_data['role']

        if self.cleaned_data['image']:
            prof.image = self.cleaned_data['image']
        
        if commit:
            prof.save()
        return prof'''
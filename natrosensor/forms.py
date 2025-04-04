from django import forms 
from .models import User

class SignupForm(forms.ModelForm):
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    first_name = forms.CharField()
    last_name = forms.CharField()
    institution = forms.CharField()

    email.widget.attrs.update({'id': 'email_signup', 'x-model': 'inputs.email', 'autocomplete': 'off'})
    password1.widget.attrs.update({'id': 'password_signup', 'x-model': 'inputs.password1'})
    password2.widget.attrs.update({'id': 'password_confirm', 'x-model': 'inputs.password2'})
    first_name.widget.attrs.update({'id': 'fname_signup', 'x-model': 'inputs.first_name', 'autocomplete': 'off'})
    last_name.widget.attrs.update({'id': 'lname_signup', 'x-model': 'inputs.last_name', 'autocomplete': 'off'})
    institution.widget.attrs.update({'id': 'inst_signup', 'x-model': 'inputs.institution', 'autocomplete': 'off'})

    class Meta:
        model = User
        fields = ['email', 'password1', 'password2', 'first_name', 'last_name', 'institution']

class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    email.widget.attrs.update({'id': 'email_login', 'placeholder': ''})
    password.widget.attrs.update({'id': 'password_login', 'placeholder': ''})


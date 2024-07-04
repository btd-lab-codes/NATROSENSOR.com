from django import forms 
from .models import User

class SignupForm(forms.ModelForm):
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    first_name = forms.CharField()
    last_name = forms.CharField()
    institution = forms.CharField()

    email.widget.attrs.update({'id': 'email_signup', 'placeholder': ''})
    password1.widget.attrs.update({'id': 'password_signup', 'placeholder': ''})
    password2.widget.attrs.update({'id': 'password_confirm', 'placeholder': ''})
    first_name.widget.attrs.update({'id': 'fname_signup', 'placeholder': ''})
    last_name.widget.attrs.update({'id': 'lname_signup', 'placeholder': ''})
    institution.widget.attrs.update({'id': 'inst_signup', 'placeholder': ''})

    class Meta:
        model = User
        fields = ['email', 'password1', 'password2', 'first_name', 'last_name', 'institution']

class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    email.widget.attrs.update({'id': 'email_login', 'placeholder': ''})
    password.widget.attrs.update({'id': 'password_login', 'placeholder': ''})


from django import forms
from django.contrib.auth.models import User


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Parol kiriting'}))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Parolni tasdiqlang'}))

    class Meta:
        model = User
        fields = ['username']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Foydalanuvchi nomini tanlang'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'Parollar bir-biriga mos kelmadi.')
        return cleaned_data

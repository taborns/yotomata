from django import forms
from yoto import  models
  
class ChannelForm(forms.ModelForm):
    class Meta:
        model = models.Channel
        fields = '__all__'

        widgets = {
            'name' : forms.TextInput(
                attrs={
                    'class' : 'form-control',
                    'placeholder' : 'Channel Name'
                    }
            ),
            'access_token' : forms.HiddenInput(
                attrs={'class' : 'form-control'}
            ),
            'refresh_token' : forms.HiddenInput(
                attrs={'class' : 'form-control'}
            ),
            'logo' : forms.FileInput(
                attrs={'class' : 'form-control'}
            ),
            'intro' : forms.FileInput(
                attrs={'class' : 'form-control'}
            )
        }


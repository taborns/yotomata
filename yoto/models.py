# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from oauth2client.client import OAuth2Credentials
# Create your models here.

class Channel(models.Model):
    name = models.CharField(max_length=200)
    access_token = models.CharField(max_length=300)
    refresh_token = models.CharField(max_length=300)
    logo = models.FileField(upload_to='logos/')
    intro = models.FileField(blank=True, null=True, upload_to='intros/')

    def getCredential(self, data ):
        required_keys = ['client_id', 'client_secret', 'token_uri']
        new_data = {}
        for key in data:
            if  key in required_keys:
                new_data[key] = data[key]

        new_data.update({
            "access_token" : self.access_token,
            "refresh_token" : self.refresh_token,
            "user_agent" : None,
            "token_expiry" : None
        })
        return OAuth2Credentials(**new_data)
        

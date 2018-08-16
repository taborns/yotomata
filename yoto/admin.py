# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from yoto import models
from django.contrib import admin

class ChannelModel(admin.ModelAdmin):
    verbose_name = "Channel"
    list_display="name",
    exclude = "access_token", 'refresh_token'
# Register your models here.
admin.site.register(models.Channel, ChannelModel)
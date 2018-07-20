# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os 
import json
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from yoto import forms
from yoto import models
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from moviepy.editor import *

import urllib2
import httplib
import httplib2
import os
import random
import sys
import time
import requests

from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser
import google.oauth2.credentials
import google_auth_oauthlib.flow

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, httplib.NotConnected,
  httplib.IncompleteRead, httplib.ImproperConnectionState,
  httplib.CannotSendRequest, httplib.CannotSendHeader,
  httplib.ResponseNotReady, httplib.BadStatusLine)

RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

CLIENT_SECRETS_FILE = BASE_DIR + "/yoto/client_secret.json"

# This OAuth 2.0 access scope allows an application to upload files to the
# authenticated user's YouTube channel, but doesn't allow other types of access.
YOUTUBE_UPLOAD_SCOPE = ["https://www.googleapis.com/auth/youtube.upload"]
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the Developers Console
https://console.developers.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))

VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")
DOMAIN = "http://localhost:8000"

def login_sys(request):
  if request.method=='POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username,password=password);

        if user and user.is_active:
            login(request, user)

            return HttpResponseRedirect("/upload/")
        errors = "Invalid username/password"

  return render(request, "login.html")

def log_out(request):
    logout(request)
    return HttpResponseRedirect("/login/")

@login_required
def get_authenticated_service(request):
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE,
      scopes=YOUTUBE_UPLOAD_SCOPE)

    flow.redirect_uri = DOMAIN + '/callback/'
    authorization_url, state = flow.authorization_url(
      # Enable offline access so that you can refresh an access token without
      # re-prompting the user for permission. Recommended for web server apps.
      access_type='offline',
      # Enable incremental authorization. Recommended as a best practice.
      include_granted_scopes='true')

    return render(request, "loginprompt.html", locals())
@login_required 
def upload(request):

  if request.method == "POST":
    local_file_name = download(request.POST['url'])
    
    start_time = getTime(request.POST['start_time'])
    end_time =getTime(request.POST['end_time'])

    #get channel
    channel = models.Channel.objects.get(id=request.POST.get('channel', None))
    configs = json.load( open(os.path.abspath(os.path.join(os.path.dirname(__file__),CLIENT_SECRETS_FILE)), "r") )
    
    #edit video
    logo = os.path.join(BASE_DIR, 'yoto/media/' + str( channel.logo))
    intro = os.path.join(BASE_DIR, 'yoto/media/' + str( channel.intro))
    
    new_video = editVideo( intro, logo, local_file_name, start_time, end_time)
    new_video.write_videofile('videome.mp4')

    credentials = channel.getCredential ( configs['web'] )
    youtube = build(
      YOUTUBE_API_SERVICE_NAME, 
      YOUTUBE_API_VERSION,
      http=credentials.authorize(httplib2.Http())
    )
    options = request.POST.copy()
    options['file'] = local_file_name
    
    #initialize_upload(youtube, options)

    # initialize_upload(youtube, request.POST)
  channels = models.Channel.objects.all()
  return render( request, "add_video.html", locals())
@login_required
def oauthCallback(request):
  if request.method == "POST":
    #print request.POST, request.FILES
    channelForm = forms.ChannelForm( request.POST, request.FILES)
    if channelForm.is_valid():
      channelForm.save();
      return HttpResponseRedirect("/channels/")
    else:
      print channelForm.errors
      return render(request, "callbackprompt.html", locals())

  code, state = request.GET['code'], request.GET.get("state")
  
  flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=YOUTUBE_UPLOAD_SCOPE, state=state)
  
  flow.redirect_uri = DOMAIN + '/callback/'

  flow.fetch_token(authorization_response=request.get_full_path())
  #credentials = {
  #  "access_token" : "ya29.Glv9BV1iPcc_38h83wpuab20VXsAP4O35tVMyA58eSrGDH5_uO3Fnzh0Fn0xSTLawyfZrEDtxN7zZAt5OlEY2boespQxCU4TT3sTw5frqMORfRjTbZIDRBjnMxdW",
  #  "refresh_token" : "1/hLEscGY2Ipwy9_cxHF_LwKxiWqQ_o6z4nJBAAhyYDzEdCay5Y2trfSs6BVH73qBd"
  #}#
  credentials = credentials_to_dict(flow.credentials)
  channelForm = forms.ChannelForm( credentials)
  return render(request, "callbackprompt.html", locals())

def credentials_to_dict(credentials):
  return {'access_token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}
@login_required
def channels(request):
  channels = models.Channel.objects.all()
  return render(request, "channels.html", locals())

def initialize_upload(youtube, options):
  print options, "OPTIONS"
  tags = None
  if options.get('tags'):
    tags = options['tags'].split(",")

  body=dict(
    snippet=dict(
      title=options['title'],
      description=options['description'],
      tags=tags,
      categoryId=options['category']
    ),
    status=dict(
      privacyStatus=options['privacyStatus']
    )
  )

  # Call the API's videos.insert method to create and upload the video.
  insert_request = youtube.videos().insert(
    part=",".join(body.keys()),
    body=body,
    media_body=MediaFileUpload(options['file'], chunksize=-1, resumable=True)
  )

  resumable_upload(insert_request)

def getTime(time_str):
  timeParts = time_str.split(":")
  for timepart in timeParts:
    try:
      int(timepart)
    except:
      return 0

  h = 0
  m = 0
  s = 0
  if ( len(timeParts) == 3):
    h,m,s = timeParts
  elif ( len(timeParts) == 2):
    m,s = timeParts
  
  elif ( len(timeParts)==1):
    s, = timeParts
  totalSeconds = int(h) * 3600 + int(m) * 60 + int(s)
  print totalSeconds, "TOTAL SECS"
  return int(totalSeconds)

def editVideo(intro_video, logo, new_video, startTime, endTime):
  
  intro_clip = VideoFileClip(intro_video)
  new_clip = VideoFileClip(new_video)
  endTime = new_clip.duration if startTime >= endTime else endTime
  new_clip_subclipped = new_clip.subclip(startTime, endTime)

  waterMark = ImageClip(logo).set_duration(new_clip_subclipped.duration).resize(height=50).margin(right=1,top=1, opacity=0).set_pos((0,new_clip_subclipped.size[0]-50))

  watermarked_video = CompositeVideoClip([new_clip_subclipped, waterMark])
  final_video = concatenate_videoclips([intro_clip, watermarked_video])
  return final_video
  

# This method implements an exponential backoff strategy to resume a
# failed upload.
def resumable_upload(insert_request):
  response = None
  error = None
  retry = 0
  while response is None:
    try:
      print "Uploading file..."
      status, response = insert_request.next_chunk()
      if 'id' in response:
        print "Video id '%s' was successfully uploaded." % response['id']
      else:
        exit("The upload failed with an unexpected response: %s" % response)
    except HttpError, e:
      if e.resp.status in RETRIABLE_STATUS_CODES:
        error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status,
                                                             e.content)
      else:
        raise
    except RETRIABLE_EXCEPTIONS, e:
      error = "A retriable error occurred: %s" % e

    if error is not None:
      print error
      retry += 1
      if retry > MAX_RETRIES:
        exit("No longer attempting to retry.")

      max_sleep = 2 ** retry
      sleep_seconds = random.random() * max_sleep
      print "Sleeping %f seconds and then retrying..." % sleep_seconds
      time.sleep(sleep_seconds)

def download(url):
  final_url = getDownloadLink(url);
  if not final_url:
    return final_url

  response = requests.get(final_url, stream=True)
  random.randint(1000, 1000000)
  file_name = random.choice(['filie_','tabo_','youtu_','video_'])
  file_name += str( random.randint(100, 100000000) )
  file_name += ".mp4"

  with open(file_name, 'wb') as f:
    for chunk in response.iter_content(chunk_size=1024): 
      if chunk: # filter out keep-alive new chunks
        f.write(chunk)

  return file_name

def getDownloadLink(url):
  endpoint = "https://www.saveitoffline.com/process/?url=youtube-url&type=json".replace("youtube-url", url)
  
  
  
  try:
    response = requests.get(endpoint)
    jsonResponse = response.json()
  except:
    print "ERROR"
    return None
  
  
  videoQualites = ['1080p', '720p','360p', ]
  urls = jsonResponse['urls']
  highest = len(videoQualites)
  final_url = None
  
  for url in urls:
    for ind, qaulity in enumerate(videoQualites):
      if qaulity in url["label"] and (not "no sound" in url['label']):
        if ind <= highest:
          highest = ind
          final_url = url["id"]
  
  #// the stated qualities are not found 
  if not final_url:
    return False
  return final_url


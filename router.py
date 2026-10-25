#!/usr/bin/env python3

# We can't really switch over to this until clubhousemedia is in its final
# home and we have a key pair in place. 

from datetime import datetime
from pathlib import Path
import subprocess
import time

def www_upload(filename):
  command = [
    '/usr/bin/scp',
    filename, 
    'flyfunston@209.182.236.182:/var/www/html/flyfunston/old-website/newwebcam',
  ]
  
  subprocess.run(command)

def stream_upload(filename):
  command = [
    '/usr/bin/scp',
    filename,
    'flyfunston@clubhousemedia:/home/flyfunston/',
  ]

def both_upload(filename):
  stream_upload(filename)
  www_upload(filename)

watchdogs = [
  {
    'mod_time': 0,
    'action': lambda x: www_upload(x),
    'filename': 'clubhouse_2d.html',
  },
  {
    'mod_time': 0,
    'action': lambda x: www_upload(x),
    'filename': 'windsock_2d.html',
  },
  {
    'mod_time': 0,
    'action': lambda x: www_upload(x), # and stream_upload(x),
    'filename': 'windsock_2d.png',
  },
  #{
    #'mod_time': 0,
    #'action': lambda x: stream_upload(x),
    #'filename': 'live_overlay.png',
  #},
]

for i in range(len(watchdogs)):
  watchdogs[i]['path'] = Path(watchdogs[i]['filename'])

while True:
  for i in range(len(watchdogs)):
    wd = watchdogs[i]
    mod_time = wd['path'].stat().st_mtime
    if mod_time != wd['mod_time']:
      print('applying action to ' + wd['filename'])
      wd['action'](wd['filename'])
      wd['mod_time'] = mod_time

  time.sleep(0.25)

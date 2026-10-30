#!/usr/bin/env python3

import io
import os
from PIL import Image, ImageDraw, ImageFont
import select
from sys import argv, stderr
import time

FONT_WIDTH = 12
FONT_HEIGHT = 20
NUM_ROWS = 6
NUM_COLUMNS = 13
IMG_WIDTH = FONT_WIDTH * NUM_COLUMNS
IMG_HEIGHT = FONT_HEIGHT * NUM_ROWS + 4 # extra 4 for decenders (like 'g' in Hg)
BACKGROUND_COLOR = (0,0,0,196)

def deg_to_compass(deg):
  deg = deg % 360
  rose = ['N', 'NNE', 'NNE', 'NE', 'NE', 'ENE', 'ENE', 'E',
          'E', 'ESE', 'ESE', 'SE', 'SE', 'SSE', 'SSE', 'S',
          'S', 'SSW', 'SSW', 'SW', 'SW', 'WSW', 'WSW', 'W',
          'W', 'WNW', 'WNW', 'NW', 'NW', 'NNW', 'NNW', 'N']
  return rose[int(deg/11.25)]
  
def justify(str):
  return (' ' * (NUM_COLUMNS - len(str))) + str

img = Image.new('RGBA', (IMG_WIDTH, IMG_HEIGHT), BACKGROUND_COLOR)
draw = ImageDraw.Draw(img)
font = ImageFont.truetype('DejaVuSansMono.ttf', size=20)

#TODO: This will eventually consume both conditions files and do both renders,
#      to avoid needing two separate services - one for each. 
with open('conditions_windsock.txt') as fd:
  fd.seek(0, io.SEEK_END)

  fileno = fd.fileno()

  while True:
    # No matter what you set the timeout to, EOF will cause select
    # to return with fd's read descriptor.... so we have to implement
    # our own blocking, since we are inherently living at the end
    # of the file.
    r, w, x = select.select([fileno], [], [], )

    line = fd.readline()
    if(not line):
      time.sleep(0.5)
    else:
      fields = [f for f in line.split(' ') if f!= '']
      timestamp, wind_speed, wind_dir, temp, humidity, dewpoint, inHg_absolute = fields

      wind_speed = float(wind_speed)
      wind_dir = int(wind_dir)
      temp = float(temp)
      humidity = float(humidity)
      dewpoint = float(dewpoint)
      inHg_absolute = float(inHg_absolute)

      # clear the render buffer - I tried doing this w/img.paste, but it won't
      # take an rgba:  
      img.paste(BACKGROUND_COLOR, [0, 0, IMG_WIDTH, IMG_HEIGHT])

      wind_speed_text = justify('%.1fmph' % wind_speed)
      draw.text(text='vel:', xy=(0,0*FONT_HEIGHT), font=font, fill='white')
      draw.text(text=wind_speed_text, xy=(0,0*FONT_HEIGHT), font=font, fill='white')

      wind_dir_text = justify('%d°' % wind_dir)
      draw.text(text=deg_to_compass(wind_dir), xy=(0,1*FONT_HEIGHT), font=font, fill='white')
      draw.text(text=wind_dir_text, xy=(0,1*FONT_HEIGHT), font=font, fill='white')

      temp_text = justify('%.1f°F' % temp)
      draw.text(text='temp:', xy=(0,2*FONT_HEIGHT), font=font, fill='white')
      draw.text(text=temp_text, xy=(0,2*FONT_HEIGHT), font=font, fill='white')

      dewpoint_text = justify('%.1f°F' % dewpoint)
      draw.text(text='DewPt:', xy=(0,3*FONT_HEIGHT), font=font, fill='white')
      draw.text(text=dewpoint_text, xy=(0,3*FONT_HEIGHT), font=font, fill='white')

      humidity_text = justify(('%.1f' % humidity) + '%')
      draw.text(text='Hum:', xy=(0,4*FONT_HEIGHT), font=font, fill='white')
      draw.text(text=humidity_text, xy=(0,4*FONT_HEIGHT), font=font, fill='white')

      inHg_absolute_text = justify('%.1f"' % inHg_absolute)
      draw.text(text='inHg:', xy=(0,5*FONT_HEIGHT), font=font, fill='white')
      draw.text(text=inHg_absolute_text, xy=(0,5*FONT_HEIGHT), font=font, fill='white')

      img.save('live_overlay.png', 'png')
      print('saved live_overlay.png')

      json_str = (
        '{' +
        f'"speed": {wind_speed}, "wind_dir": {wind_dir}, "temp": {temp}, "dewpoint": {dewpoint}, ' +
        f'"humidity": {humidity}, "inHG_absolute": {inHg_absolute}' +
        '}'
      )
      with open('live.json', 'w') as json_fd:
        json_fd.write(json_str)
      print('saved live.json')

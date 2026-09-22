#!/usr/bin/env python3

import json
from pathlib import Path
import pprint
import requests
import socket
import sys
import time

#TODO(P2) Have the process auto-truncate output files to the last 8 hours of 
#         data every hour or so.

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# listen on the socket we're about to bind, but don't claim the port
# exclusively, allowing other processes to use it, as well.

sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
sock.bind(("", 22222))

file_path = Path(__file__).parent
print(file_path)

instrument_names = [None, 'clubhouse', 'windsock']
outputs = [
  None,
  open(file_path.joinpath(f'conditions_{instrument_names[1]}.txt'), 'a'),
  open(file_path.joinpath(f'conditions_{instrument_names[2]}.txt'), 'a'),
]

last_davis_http_timestamp = 0.0
last_davis_response = None
davis_http_frequency = 15.0
last_bar_absolute = 29.92

# It's an absolute bullshit design, but the Davis receiver only sends out
# certain data via udp - most of it completely useless aggregation info.
# By listening on UDP, I HOPE that I get a 1-to-1 of source data to logged
# data. 
while True:
  data, addr = sock.recvfrom(1024*16)
  print(addr, flush=True)
  weather_json = data.decode('utf-8', errors='ignore')
  weather = json.loads(weather_json)

  now = time.time()

  if not last_davis_response or now - davis_http_frequency > last_davis_http_timestamp:
    try:
      print('  updating temp, humidity, pressure via http...', flush=True)
      response = requests.get(f'http://{addr[0]}/v1/current_conditions', timeout=2.0)
      if response.status_code == 200:
        last_davis_response = [None] * 3
        for conditions in response.json()['data']['conditions']:
          if conditions['data_structure_type'] == 1:
            last_davis_response[conditions['txid']] = conditions
          elif conditions['data_structure_type'] == 3:
            last_bar_absolute = conditions['bar_absolute']
      last_davis_http_timestamp = now
    except Exception as e:
      print('  http exception', e, flush=True)
    finally:
      print('  done', flush=True)
      pass

  for sample in weather['conditions']:
    txid = sample['txid']

    data_buff = (f'{now:.2f} {sample["wind_speed_last"]:5.2f} '
                 f'{sample["wind_dir_last"]}')
    if last_davis_response:
      data_buff += (
          f' {last_davis_response[txid]["temp"]} ' +
          f'{last_davis_response[txid]["hum"]} ' +
          f'{last_davis_response[txid]["dew_point"]} '
          f'{last_bar_absolute}'
      )
    data_buff += '\n'
    print(f'  {instrument_names[txid]:9} {data_buff}', end='', flush=True)
    outputs[txid].write(data_buff)
    outputs[txid].flush()

  # Why the fuck isn't this data in the udp report?

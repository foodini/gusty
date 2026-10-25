#!/usr/bin/bash

echo killing running udp listeners...
for pid in `ps aux | grep listen_on_udp_22222.py | grep -v grep | cut -w -f2`; do
  echo killing udp listener pid $pid
  kill -9 $pid
done
echo killing running plot uploaders...
for pid in `ps aux | grep upload_wind_plots.sh | grep -v grep | cut -w -f2`; do
  echo killing uploader pid $pid
  kill -9 $pid
done
echo killing running overlay processes...
for pid in `ps aux | grep live_overlay.py | grep -v grep | cut -w -f2`; do
  echo killing overlay pid $pid
  kill -9 $pid
done
echo done

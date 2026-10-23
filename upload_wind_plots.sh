#!/bin/bash

cd $HOME/Funston/gusty

NEXT_RENDER_TIME=`date +%s`
NEXT_RENDER_TIME=$(( $NEXT_RENDER_TIME + 300 ))

while true; do
  ./renderer.py
  sftp -b upload_wind_plots.sftp flyfunston@209.182.236.182
  SLEEP_TIME=$(( $NEXT_RENDER_TIME - $(date +%s) ))
  echo sleep_time: $SLEEP_TIME
  sleep $SLEEP_TIME
  NEXT_RENDER_TIME=$(( $NEXT_RENDER_TIME + 300 ))
  echo NEXT_RENDER_TIME + 300 = $NEXT_RENDER_TIME
done

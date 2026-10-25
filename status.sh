#!/usr/bin/bash

ps aux | head -1
ps aux | grep listen_on_udp_22222.py | grep -v grep
ps aux | grep upload_wind_plots.sh | grep -v grep
ps aux | grep live_overlay.py | grep -v grep

echo done

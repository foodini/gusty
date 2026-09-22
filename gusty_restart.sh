#!/usr/bin/bash
kill -9 `ps aux | grep listen_on_udp_22222.py | grep -v grep | cut -d ' ' -f 2`
rm nohup.out
tail -12000 conditions_clubhouse.txt > /tmp/conditions.txt
mv /tmp/conditions.txt conditions_clubhouse.txt
tail -12000 conditions_windsock.txt > /tmp/conditions.txt
mv /tmp/conditions.txt conditions_windsock.txt
sleep 1
nohup ./listen_on_udp_22222.py &

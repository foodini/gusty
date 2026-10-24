#!/usr/bin/bash

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
cd $SCRIPT_DIR
source $SCRIPT_DIR/bin/activate

if [[ ! -d archive ]]; then
  mkdir archive
fi
DATE_STRING=`date +%Y.%m.%d`

./stop.sh

echo archiving conditions data...
cp conditions_clubhouse.txt "archive/"$DATE_STRING"_conditions_clubhouse.txt"
cp conditions_windsock.txt "archive/"$DATE_STRING"_conditions_windsock.txt"

echo truncating conditions data to the last 8 hours...
tail -12000 conditions_clubhouse.txt > /tmp/conditions.txt
mv /tmp/conditions.txt conditions_clubhouse.txt
tail -12000 conditions_windsock.txt > /tmp/conditions.txt
mv /tmp/conditions.txt conditions_windsock.txt

echo starting udp listener...
nohup ./listen_on_udp_22222.py >> listen_on_udp_22222.out 2>&1 &

echo starting uploader...
nohup ./upload_wind_plots.sh >> upload_wind_plots.out 2>&1 &

echo starting raw_overlay...
nohup ./raw_overlay.py conditions_windsock.txt >> raw_overlay.out 2>&1 &

echo done

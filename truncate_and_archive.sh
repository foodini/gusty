#!/usr/bin/bash

gusty_dir=/home/flyfunston/gusty

/usr/bin/tail -10000 $gusty_dir/renderer.out > /tmp/renderer.out
/usr/bin/mv /tmp/renderer.out $gusty_dir/renderer.out

today=$(/usr/bin/date +%Y.%m.%d)

#Note that there is a chance of losing a measurement here if one is appended to the conditions file
#in between the creation of the temporary file and the overwrite.
/usr/bin/tail -34560 $gusty_dir/conditions_windsock.txt > /tmp/conditions_windsock.txt
mv /tmp/conditions_windsock.txt $gusty_dir
cp $gusty_dir/conditions_windsock.txt $gusty_dir/archive/$today'_windsock.txt'

/usr/bin/tail -34560 $gusty_dir/conditions_clubhouse.txt > /tmp/conditions_clubhouse.txt
mv /tmp/conditions_clubhouse.txt $gusty_dir/archive/$today'_clubhouse.txt'

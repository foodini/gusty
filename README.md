 # gusty, A weather visualization tool

Creates an 8-hour history graph of telemetry gathered from our Davis
Instruments weather stations.

![Sample rendering](https://github.com/foodini/gusty/blob/main/example_2d.png?raw=true)

## Dependencies
Definitely do this in a virtual environment
``` 
python3 -m venv .
source bin/activate
python3 -m pip install numpy
python3 -m pip install pillow
python3 -m pip install plotly
python3 -m pip install requests
python3 -m pip install --upgrade 'kaleido>=1'
```

## How it works

There are three separate parts to gusty. All three can be stopped, started, or
checked as a group with ./stop.sh, ./start.sh, or ./status.sh.

The first component is the listener (listen_on_udp_22222.py,) which picks up
the UDP broadcasts from the Davis base station and queues the data into a pair
of files, one for the windsock and one for the clubhouse. 

upload_wind_plots triggers the renderer every 5 minutes or so, which creates
the 8-hour history graph seen above, as well as the .png that is used in the
YouTube Livestream. The 8-hour history graph is uploaded to flyfunston.org
for general access. The .png will be copied to where OBS Studio expects to find
it. 

live_overlay.py also watches the conditions_windsock.txt file and, every time
it changes, renders one of these:

![Sample raw](https://github.com/foodini/gusty/blob/main/example_raw.png?raw=true)

This happens roughly every 2.5 seconds because that's how often the Davis base
station broadcasts.

I'm not a fan of the fact that the uploader is currently calling the renderer. I
should have one process that watches for changes to any of the generated assets
and sends them to their proper destinations, keeping the renderer and the uploader
separate. It makes more sense that way now that the live_overlay renderer exists.

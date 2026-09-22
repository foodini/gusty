#!/usr/bin/env python3

from datetime import datetime
import math
import numpy as np
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import threading
import time

#TODO(P0): Get rid of all the repeated magic numbers (colors, mostly.)
#TODO(P1): Add a rolling average to direction and speed? 5m, 15m, 1h? 
#          Write an aggregator class to keep running totals.
#TODO(P1): Cap temp/dewpoint to the min and max displayed on the chart.
#TODO(P1): Get some help with setting up a more palletable ( =] ) color scheme.
#TODO(P1): Get rid of the time-axis hard-coding so the script can generate
#          charts with different timespans based upon a command-line.
#TODO(P2): When we come back from a data loss, gust computation generates
#          artificial spikes.

file_path = Path(__file__).parent

GUST_TIME_WINDOW = 90
HIGHEST_REASONABLE_TEMP = 100
LOWEST_REASONABLE_TEMP = 30

class Renderer(object):
  def __init__(self, instrument_name, wind_band_offset):
    self.instrument_name = instrument_name
    self.wind_band_offset = wind_band_offset
    self.dl_timestamps = []
    self.dl_directions = []
    self.dl_speeds = []
    self.sc_timestamps = []
    self.sc_directions = []
    self.sc_speeds = []
    self.sc_gust_energies = []
    self.sc_temperatures = []
    self.sc_humidities = []
    self.sc_dewpoints = []
    self.sc_bar_absolute = []
    self.gust_energy_trailing_position = -1
    self.trailing_position_timestamp = 0.0
    self.gust_energy_rolling_total = 0.0
    self.latest_time = 0.0
    # Yes. Trig lookup tables are still faster, even today. (About 2x difference.)
    self.sin_table = list(math.sin(math.radians(x)) for x in range(0,361))
    self.cos_table = list(math.cos(math.radians(x)) for x in range(0,361))

  def timestamp_map(self, timestamps):
    return list(map(lambda x: None if not x else x - self.latest_time, timestamps))

  def deg_to_compass(self, deg):
    deg = deg % 360
    rose = ['N', 'NNE', 'NNE', 'NE', 'NE', 'ENE', 'ENE', 'E', 
            'E', 'ESE', 'ESE', 'SE', 'SE', 'SSE', 'SSE', 'S',
            'S', 'SSW', 'SSW', 'SW', 'SW', 'WSW', 'WSW', 'W',
            'W', 'WNW', 'WNW', 'NW', 'NW', 'NNW', 'NNW', 'N']
    return rose[int(deg/11.25)]

  def get_hms(self, timestamp):
    dt = datetime.fromtimestamp(timestamp)
    return f'{dt.hour:02}:{dt.minute:02}:{dt.second:02}'

  def render(self):
    self.latest_time = time.time()
    self.trailing_position_timestamp = self.latest_time - GUST_TIME_WINDOW
    print('max gust factor:', max(self.sc_gust_energies))
    self.render_2d()
    self.render_3d()

  def render_2d(self):
    fig = go.Figure()

    ts_map = self.timestamp_map(self.sc_timestamps)
    hms = list(map(lambda t: self.get_hms(t), self.sc_timestamps))
    hover_texts = [
      f'Time: {t}<br>' + 
      f'Speed: {s:.1f}mph<br>' +
      f'Dir: {d}({self.deg_to_compass(d)})<br>' +
      f'Gust Factor: {g:.2f}<br>' +
      f'Temp: {tmp:.1f}°F<br>' +
      f'Dewpoint: {dew:.1f}°F<br>' +
      f'Humidity: {h:.1f}%<br>' +
      f'Pressure: {p:.3f}(bar)<br>'
      for t, s, d, g, tmp, h, dew, p in zip (
          hms, self.sc_speeds, self.sc_directions, self.sc_gust_energies, self.sc_temperatures,
          self.sc_humidities, self.sc_dewpoints, self.sc_bar_absolute)
    ]

    # It's nearly impossible for dewpoint to be higher than temperature, so we can
    # save ourselves some iterating in getting the temperature boundaries by just
    # taking max of temp and min of dewpoint.
    min_temp = min(self.sc_dewpoints)
    max_temp = min(self.sc_temperatures)

    # I don't want to show an entire graph range of, say 30 degrees to 100 degrees. It compacts
    # the temp and dewpoint lines into nearly flat, frequently coincident lines. However, I want
    # temps in the high 90s to show near the top of the graph and temps in the low 30s to be at
    # the bottom.

    temp_mid = (max_temp + min_temp) / 2.0
    temp_span = max_temp - min_temp
    temp_graph_span = max(15, temp_span)
    temp_graph_border_span = temp_graph_span - temp_span
    max_ratio = (max_temp - LOWEST_REASONABLE_TEMP) / (HIGHEST_REASONABLE_TEMP - LOWEST_REASONABLE_TEMP)
    temp_graph_top = max_temp + (1.0 - max_ratio) * temp_graph_border_span
    temp_graph_bottom = min_temp - max_ratio * temp_graph_border_span
    temp_graph_top = int(temp_graph_top/5.0) * 5 + 5
    temp_graph_bottom = int(temp_graph_bottom/5.0) * 5
    #print(temp_graph_bottom, min_temp, temp_mid, max_temp, temp_graph_top)

    '''
    if(
        len(self.sc_directions) != len(self.sc_speeds) or
        len(self.sc_directions) != len(self.sc_timestamps) or
        len(self.sc_directions) != len(self.sc_gust_energies)):
      import ipdb; ipdb.set_trace()
    '''

    fig.add_trace(
      go.Scatter(
        x = ts_map,
        y = self.sc_speeds,
        xaxis = 'x',
        yaxis = 'y',
        mode = 'markers',
        marker = dict(
          size = 3,
          color = self.sc_gust_energies,
          colorscale = 'Turbo',
          opacity = 0.45,
          cauto = False,
          cmin = -2,
          cmax = 20,
        ),
        name = 'Wind Speed',
        customdata = hover_texts,
        hovertemplate = '%{customdata}<extra></extra>'
      )
    )

    fig.add_trace(
      go.Scatter(
        x = ts_map,
        y = self.sc_directions,
        xaxis = 'x',
        yaxis = 'y2',
        mode = 'markers',
        marker = dict(
          size = 3,
          color = self.sc_gust_energies,
          colorscale = 'Turbo',
          opacity = 0.45,
          cauto = False,
          cmin = -2,
          cmax = 20,
        ),
        name = 'Wind Direction',
        customdata = hover_texts,
        hovertemplate = '%{customdata}<extra></extra>'
      )
    )

    fig.add_trace(
      go.Scatter(
        x = ts_map,
        y = self.sc_temperatures,
        xaxis = 'x',
        yaxis = 'y3',
        mode = 'markers',
        marker = dict(
          size = 2,
          color = '#ff6060',
          opacity = 0.45,
        ),
        name = 'Temperature',
        customdata = hover_texts,
        hovertemplate = '%{customdata}<extra></extra>'
      )
    )

    fig.add_trace(
      go.Scatter(
        x = ts_map,
        y = self.sc_dewpoints,
        xaxis = 'x',
        yaxis = 'y3',
        mode = 'markers',
        marker = dict(
          size = 2,
          color = '#888888',
          opacity = 0.45,
        ),
        name = 'Dewpoint',
        hovertemplate = '<extra></extra>'
      )
    )

    fig.add_trace(
      go.Scatter(
        x = ts_map,
        y = self.sc_humidities,
        xaxis = 'x',
        yaxis = 'y4',
        mode = 'markers',
        marker = dict(
          size = 2,
          color = '#6060ff',
          opacity = 0.45,
        ),
        name = 'Humidity',
        hovertemplate = '<extra></extra>'
      )
    )

    page_title = f'Fort Funston {self.instrument_name.capitalize()} - {datetime.now().ctime()}'

    # synchronize crosshairs, tooltips, and styling
    fig.update_layout(
      title = page_title,
      template='plotly_dark',
      paper_bgcolor='#0b0f19',
      plot_bgcolor='#0b0f19',
      #height = 1200,
      hovermode = 'x',
      hoverlabel = dict(
        bgcolor = '#0b0f19',
        bordercolor = '#334155',
        font = dict(
          family = 'monospace',
          size = 16,
          color = '#f8fafc',
        ),
      ),
      showlegend = False,
      margin = dict(l=80, r=80, b=40, t=50),

      xaxis = dict(
        range = [-8*3600, 0],
        tickvals = [-28800, -21600, -14400, -7200, 0],
        ticktext = ['-8h', '-6h', '-4h', '-2h', 'Now'],
        tickfont = dict(color='#94a3b8'),
        gridcolor = '#1e293b',
        showgrid = True,

        showspikes = True,
        spikemode = 'across',
        spikesnap = 'cursor',
        spikethickness = 1,
        spikecolor = '#f8fafc',
        spikedash = 'dot',
        hoverformat = '', #kills the '-123.4k' bullshit from hovertext
      ),


      yaxis = dict(
        domain = [0.65, 1.0], # Controls how much vertical screen space this axis gets.
        title = dict(text='Speed(mph)', font=dict(color='#cbd5e1')),
        range = [0, 40],
        gridcolor = '#1e293b',
        tickfont = dict(color='#94a3b8'),
      ),

      yaxis2 = dict(
        domain = [0.30, 0.60],
        title = dict(text='Direction', font=dict(color='#cbd5e1')),
        range = [0, 360],
        tickvals = [0, 90, 180, 270, 360],
        ticktext = ['N', 'E', 'S', 'W', 'N'],
        gridcolor = '#1e293b',
        tickfont = dict(color='#94a3b8'),
      ),

      yaxis3 = dict(
        domain = [0.0, 0.25],
        title = dict(text='Dewpoint & Temp', font=dict(color='#ff6060')),
        range = [temp_graph_bottom-1, temp_graph_top+1],
        tickvals = list(range(temp_graph_bottom,temp_graph_top+5,5)),
        gridcolor = '#1e293b',
        tickfont = dict(color='#ff6060'),
      ),

      yaxis4 = dict(
        domain = [0.0, 0.25],
        side = 'right',
        overlaying = 'y3',
        title = dict(text='Humidity', font=dict(color='#6060ff')),
        range = [29, 101],
        tickvals = list(range(30,110,10)),
        ticktext = [f'{x}%' for x in range(30,110,10)],
        tickfont = dict(color='#6060ff'),
        showgrid = False,
      ),
    )

    for mn, mx in [(18,20), (16,22), (14,24), (12,26)]:
      fig.add_hrect(
        y0 = mn + self.wind_band_offset,
        y1 = mx + self.wind_band_offset,
        yref = 'y',
        fillcolor = '#a0a0a0',
        opacity = 0.06,
        layer = 'below',
        line_width = 0,
      )

    for dd in [10, 20, 30, 45]:
      fig.add_hrect(
        y0 = 260 - dd,
        y1 = 260 + dd,
        yref = 'y2',
        fillcolor = '#a0a0a0',
        opacity = 0.04 + dd/1000.0,
        layer = 'below',
        line_width = 0,
      )

    html_filename = self.instrument_name + '_2d.html'
    print(f'writing {len(self.sc_speeds)} data points to {html_filename}...', flush=True)
    # add full_html=False to make an embeddable chunk.
    fig.write_html(
      str(file_path.joinpath(html_filename)),
      include_plotlyjs='cdn')
    print(f'done writing {html_filename}', flush=True)

    '''
    png_filename = self.instrument_name + '_2d.png'
    print(f'writing {len(self.sc_speeds)} data points to {png_filename}...', flush=True)
    raw_data = fig.to_image(format='png', width=1400, height=900, scale=1.5)
    with open(png_filename, 'wb') as out:
      out.write(raw_data)
    print(f'done writing {png_filename}', flush=True)
    '''

  def render_3d(self):
    fig = go.Figure() # go figure...

    fig.add_trace(
      go.Scatter3d(
        x=self.timestamp_map(self.dl_timestamps),
        y=self.dl_directions,
        z=self.dl_speeds,
        mode='lines',
        line=dict(color='#38bdf8', width=2),
        opacity=0.45,
        hoverinfo='skip',
        showlegend=False
      )
    )

    fig.add_trace(
      go.Scatter3d(
        x=self.timestamp_map(self.sc_timestamps),
        y=self.sc_directions,
        z=self.sc_speeds,
        mode='markers',
        marker=dict(
          size=3,
          color=self.sc_speeds,
          colorscale='Turbo',
          opacity=0.25
        ),
        hoverinfo='text',
        text=[
          f'Time: {self.get_hms(t)}<br>' +
          f'Dir: {d}° ({self.deg_to_compass(d)})<br>' +
          f'Speed: {s:.1f} mph'
          for t, d, s in zip(
            self.sc_timestamps, self.sc_directions, self.sc_speeds
          )
        ],
        showlegend=True,
        name='Please contact Ron w/ questions/ideas/bugs'
      )
    )
    
    fig.update_layout(
      template='plotly_dark',
      paper_bgcolor='#0b0f19',
      scene=dict(
        camera=dict(
          projection=dict(
            type='orthographic'
          ),
          eye=dict(
            x=1.7, y=-1.7, z=1.3,
          )
        ),
        aspectmode='manual',
        aspectratio=dict(x=2.5, y=1.0, z=0.8),
        xaxis=dict(
          title=dict(text='Time', font=dict(color='#cbd5e1')),
          range=[-8*3600, 0],
          tickvals=[-28800, -21600, -14400, -7200, 0],
          ticktext=['-8h', '-6h', '-4h', '-2h', 'now'],
          tickfont=dict(color='#94a3b8'),
          gridcolor='#1e293b',
          zerolinecolor='#334155'
        ),
        yaxis=dict(
          title=dict(text='Direction', font=dict(color='#cbd5e1')),
          range=[0, 360],
          tickvals=list(range(0, 361, 90)),
          ticktext=['N', 'E', 'S', 'W', 'N'],
          tickfont=dict(color='#94a3b8'),
          gridcolor='#1e293b',
          zerolinecolor='#334155'
        ),
        zaxis=dict(
          title=dict(text='Speed (mph)', font=dict(color='#cbd5e1')),
          range=[0, round(max(self.sc_speeds)+9, -1)],
          tickfont=dict(color='#94a3b8'),
          gridcolor='#1e293b',
          zerolinecolor='#334155'
        ),
        bgcolor='#0b0f19'
      ),
      #TODO(P3) necessary?
      margin=dict(l=0, r=0, b=0, t=0)
    )

    filename = self.instrument_name + '_3d.html'
    print(f'writing {len(self.sc_speeds)} data points to {filename}...', flush=True)
    fig.write_html(
      str(file_path.joinpath(filename)),
      include_plotlyjs='cdn')
    print(f'done writing {filename}', flush=True)


  def magnitude_of_vector_difference(self, speed0, dir0, speed1, dir1):
    x0 = self.sin_table[dir0] * speed0
    y0 = self.cos_table[dir0] * speed0
    x1 = self.sin_table[dir0] * speed1
    y1 = self.cos_table[dir1] * speed1
    dx = x1-x0
    dy = y1-y0
    return math.sqrt(dx*dx+dy*dy)

  def append_datapoint(self, datapoint_dict):
    timestamp =     datapoint_dict['timestamp']
    wind_speed =    datapoint_dict['wind_speed']
    wind_dir =      datapoint_dict['wind_dir']

    trailing_position_timestamp = timestamp - 60
    if not self.sc_gust_energies:
      self.gust_energy_rolling_total = 0.0
      self.sc_gust_energies.append(0.0)
      self.gust_energy_trailing_position = -1
    else:
      while (
          self.sc_timestamps[self.gust_energy_trailing_position] < trailing_position_timestamp and
          self.gust_energy_trailing_position < -1):
        self.gust_energy_rolling_total -= self.sc_gust_energies[self.gust_energy_trailing_position]
        self.gust_energy_trailing_position += 1
      magnitude = self.magnitude_of_vector_difference(
        self.sc_speeds[-1], self.sc_directions[-1], wind_speed, wind_dir)
      # kinetic energy is porportional to the square of velocity. Technically, it's 1/2 mv^2, but
      # the mass of air at the fort doesn't change sufficiently to affect the display and it's
      # relative, so the 1/2 is irrelevant.
      magnitude *= magnitude
      self.gust_energy_rolling_total += magnitude
      current_window_width = timestamp - self.sc_timestamps[self.gust_energy_trailing_position]
      self.sc_gust_energies.append(self.gust_energy_rolling_total / current_window_width)
      self.gust_energy_trailing_position -= 1
          
    self.sc_timestamps.append(timestamp)
    self.sc_directions.append(wind_dir)
    self.sc_speeds.append(wind_speed)
    self.sc_temperatures.append(datapoint_dict['temp'])
    self.sc_humidities.append(datapoint_dict['humidity'])
    self.sc_dewpoints.append(datapoint_dict['dewpoint'])
    self.sc_bar_absolute.append(datapoint_dict['bar_absolute'])
    if not self.dl_timestamps or timestamp > self.dl_timestamps[-2] + 180:
      self.dl_timestamps.extend([timestamp, timestamp, timestamp, None])
      self.dl_directions.extend([wind_dir, wind_dir, 360, None])
      self.dl_speeds.extend([0, wind_speed, wind_speed, None])

  def get_lines(self):
    with open(file_path.joinpath(f'conditions_{self.instrument_name}.txt')) as infd:
      while True:
        line = infd.readline()
        if not line:
          self.render()
          return
        else:
          now = time.time()
          line = line.strip()
          fields = [f for f in line.split(' ') if f != '']
          if len(fields) > 3:
            timestamp, wind_speed, wind_dir, temp, humidity, dewpoint, bar_absolute = fields
          else:
            timestamp, wind_speed, wind_dir = fields
            temp, humidity, dewpoint, bar_absolute = (0.0, 0.0, 0.0, 0.0)
            
          if float(timestamp) > now - 8*3600:
            datapoint_dict = dict(
              timestamp =    float(timestamp),
              wind_speed =   float(wind_speed),
              wind_dir =     int(wind_dir),
              temp =         float(temp),
              humidity =     float(humidity),
              dewpoint =    float(dewpoint),
              bar_absolute = float(bar_absolute),
            )

            yield datapoint_dict
  

#TODO(P1): This is a shit way to parse-and-render. The iteration should be in the class,
#          by having get_lines just take over and render when it feels like it.
def process_input(instrument_name, wind_band_offset):
  print('Creating renderer for ' + instrument_name, flush=True)
  renderer = Renderer(instrument_name, wind_band_offset)
  for datapoint_dict in renderer.get_lines():
    renderer.append_datapoint(datapoint_dict)

process_input('windsock', 0)
process_input('clubhouse', -5)

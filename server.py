import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import bokeh
import folium
from flask import Flask, render_template, request

from flask import Flask

import folium

app = Flask(__name__)

def get_data(data_name):
    url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-{data_name}.csv'.format(data_name = data_name)
    # Get data to dataframe
    data = pd.read_csv(url)
    # Reshape data frame
    data = pd.melt(data, id_vars= data.columns[:4], value_vars= data.columns[5:data.shape[1]], var_name= 'Day', value_name= data_name)
    data[data_name].astype('int64')
    return data

confirmed = get_data('Confirmed')
recovered = get_data('Recovered')
deaths = get_data('Deaths')

key = ['Province/State', 'Country/Region', 'Lat', 'Long', 'Day']
data = confirmed
data = data.merge(recovered, on= key, how= 'inner')
data = data.merge(deaths, on= key, how= 'inner')
data['Day'] = pd.to_datetime(data['Day'])
data = data[data.Confirmed != 0]
del confirmed, deaths, recovered, key

data['Province/State_Country/Region'] = data['Province/State'].fillna('')
data['Province/State_Country/Region'] = data['Province/State_Country/Region'].apply(lambda x: x if x == '' else x + ' - ')
data['Province/State_Country/Region'] = data['Province/State_Country/Region'] + data['Country/Region']

data_current_update = data[data.Day == data.Day.max()]
data_current_update.sort_values(by= 'Confirmed', ascending= True, inplace= True)

lat, lon = 40, 5
zoom = 1.5
map = folium.Map(location=[lat, lon], zoom_start= zoom,
                 control_scale=True,
                 tiles= 'cartodbdark_matter')


update_day = data.Day.max().strftime('%B %d %Y')
prefix = 'Data source: JHU CSSE. Update day: {update_day}.<br>Coordinates:'.format(update_day= update_day)
# Add mouse position
from folium.plugins import MousePosition
formatter = "function(num) {return L.Util.formatNum(num, 3) + '&#176';};"
MousePosition(
    position='topright',
    separator=' | ',
    empty_string='',
    lng_first=True,
    num_digits=20,
    prefix= prefix,
    lat_formatter=formatter,
    lng_formatter=formatter,
).add_to(map)


from bokeh.plotting import figure
from bokeh.models.formatters import DatetimeTickFormatter
from bokeh.models.tools import HoverTool
from bokeh.models import Legend
from bokeh.embed import file_html
from bokeh.resources import INLINE

def create_plot(plot_table):
    plot_table['Day_str'] = plot_table['Day'].dt.strftime('%B %d %Y')
    plot_table['Existing'] = plot_table['Confirmed'] - plot_table['Recovered'] - plot_table['Deaths']
    plot_table['Confirmed_plot'] = plot_table['Confirmed'] / 2

    colors = ["#FF5733", "#047d38", "#c2b804"]

    tools = "crosshair,pan,reset, save"
    
    tooltip = '''
                <p style="text-align: center;"><span style="color: #0000ff;"><strong>@Day_str</strong></span></p>
                <ul>
                <li style="color: #c2b804;">Deaths: @Deaths</li>
                <li style="color: #047d38;">Recovered: @Recovered</li>
                <li style="color: #ff5733;">Existing: @Existing</li>
                </ul>
            '''

    hover = HoverTool(tooltips=tooltip, mode='vline')
    title = 'Covid-19 Cases in {} Over Time'.format(plot_table['Province/State_Country/Region'].iloc[0])

    p = figure(tools = [hover, tools], toolbar_location= None,
               x_axis_type= "datetime", plot_width=600, plot_height=200, title= title)

    names = ['Existing', 'Recovered', 'Deaths']
    v= p.varea_stack(stackers= names, x='Day', color= colors, source= plot_table, alpha=0.7)
    legend = Legend(items=[
        ("Deaths",   [v[2]]),
        ("Recovered",   [v[1]]),
        ("Existing",   [v[0]]),],
        location=(0, 0))

    p.add_layout(legend, 'right')

    p.circle(y= 'Confirmed_plot', x= 'Day', size=8, source= plot_table,
                  fill_color=None, hover_fill_color=None,
                  fill_alpha=None, hover_alpha=None,
                  line_color=None, hover_line_color=None)

    p.xaxis.formatter=DatetimeTickFormatter(days=["%d/%m"])
    from math import pi
    p.xaxis.major_label_orientation = pi/3

    p.y_range.start = 0
    p.x_range.range_padding = 0.1
    p.xgrid.grid_line_color = None
    p.axis.minor_tick_line_color = None
    p.outline_line_color = None
    
    html = file_html(p, INLINE, "my plot")
    return html
from folium import IFrame
for i in range(data_current_update.shape[0]):
    lat = data_current_update.Lat.iloc[i]
    long = data_current_update.Long.iloc[i]
    radius = 3 * data_current_update.Confirmed.iloc[i] ** 0.22
    
    # Format toolstip
    tooltip = '''
                <p style="text-align: center;"><strong>{state}</strong></p>
                <p style="text-align: left;">{confirmed}&nbsp;cases confirmed:</p>
                <ul>
                <li style="color: #c2b804 ;">Deaths: {deaths}</li>
                <li style="color: #047d38;">Recovered: {recovered}</li>
                <li style="color: #ff5733;">Existing: {existing}</li>
                </ul>
            '''
    
    if pd.isna(data_current_update['Province/State'].iloc[i]):
        state = data_current_update['Country/Region'].iloc[i]
    else:
        state = data_current_update['Province/State'].iloc[i] + ' - ' + data_current_update['Country/Region'].iloc[i]
    
    confirmed = data_current_update['Confirmed'].iloc[i]
    recovered = data_current_update['Recovered'].iloc[i]
    deaths = data_current_update['Deaths'].iloc[i]
    existing = confirmed - recovered - deaths
    
    tooltip = tooltip.format(state= state.upper(), confirmed= confirmed,
                             recovered= recovered, deaths= deaths,
                             existing= existing)
    
    # Create pop-up
    plot_table = data.loc[data['Province/State_Country/Region'] == data_current_update['Province/State_Country/Region'].iloc[i]]

    html = create_plot(plot_table)
    iframe = IFrame(html=html, width=500, height=200)
    popup = folium.Popup(iframe, max_width=600, max_height= 250)

    # Create circle
    circle = folium.CircleMarker(
          location=[lat,long],
          tooltip = tooltip,
          popup= popup,
          radius= radius,
          color= '#F7F7F7',
          weight= 0.2,
          fill= True,
          fill_color= '#ff0000',
          fillOpacity = 1)
    circle.add_to(map)

from folium import plugins
from folium.plugins import MiniMap
full_screen = plugins.Fullscreen(
    position='topright',
    title='Expand me',
    title_cancel='Exit me',
    force_separate_button=True)
full_screen.add_to(map)
minimap = MiniMap(tiles= 'cartodbdark_matter', toggle_display=True)
minimap.add_to(map)


@app.route('/')
def index():
    return map._repr_html_()

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 5001)

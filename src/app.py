import os
import time

import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import altair as alt
import geopandas as gpd
import pandas as pd
from datetime import datetime, date

import json

import plotly.express as px

from enum import Enum
class SelectionMode(Enum):
    World = 1
    Regions = 2
    Countries = 3

def is_perCapita(key):
    """
    Check if Per Capita mode is selected

    Parameters
    ----------
    key : str 
        value of option selectected (absolute or per capita)

    Returns
    -------
    boolean
        True if key is "Per Capita", else False 
    """
    return key == "Per Capita"

def calculate_continent_daywise(countries_daywise_df):
    """
    Calculate the statistics on a continent level for every single day

    Parameters
    ----------
    countries_daywise_df : df 
        A dataframe of daily observations for all countries

    Returns
    -------
    continents_df
        A dataframe of continent's daily statistics
    """
    return calculate_continent_statistics(countries_daywise_df, 'Date')

def calculate_continent_statistics(countries_df, group_col):
    """
    Calculate the statistics on a continent level based on a particular time interval grouping.
    Aggegrating method is default to be 'mean' as of now.

    Parameters
    ----------
    countries_df : df 
        A dataframe of countries
    group_col : str 
        The column to group the data

    Returns
    -------
    continents_df
        A dataframe of continent's statistics
    """
    continents_df = countries_df.drop(drop_cols, axis=1).groupby([group_col, 'WHO Region']).agg('mean').reset_index()
    continents_df['Country/Region'] = continents_df['WHO Region']
    continents_df['Population'] = population_data['Population'].sum()

    return continents_df

def calculate_world_daywise(countries_daywise_df):
    """
    Calculate the statistics for the whole world for every single day

    Parameters
    ----------
    countries_daywise_df : df 
        A dataframe of daily observations

    Returns
    -------
    world_df
        A dataframe of the whole world's daily statistics
    """
    return calculate_world_statistics(countries_daywise_df, 'Date')

def calculate_world_statistics(countries_df, group_col):
    """
    Calculate the statistics for the whole world based on a particular time interval grouping.
    Aggegrating method is default to be 'mean' as of now.

    Parameters
    ----------
    countries_df : df 
        A dataframe of countries
    group_col : str 
        The column to group the data

    Returns
    -------
    world_df
        A dataframe of the world's statistics
    """
    world_df = countries_df.drop(drop_cols, axis=1).groupby(group_col).agg('mean').reset_index()
    world_df['Country/Region'] = 'World'
    world_df['WHO Region'] = 'World'
    world_df['Population'] = population_data['Population'].sum()

    return world_df

def generate_map(chart_data, metric='Confirmed', labels=None):
    """
    Plot interactive world map

    Parameters
    ----------
    chart_data : df 
        A dataframe of filtered data to plot
    metric: str, default to 'Confirmed'
        A metric that we want to display
    labels: dict, default to None
        A mapping between metric name and label name

    Returns
    -------
    plot
        A map of the world colored by confirmed cases
    """
    fig = px.choropleth(
        chart_data,
        locations="country_code",
        color=metric,
        hover_name="Country/Region",
        color_continuous_scale='Reds',
        projection= 'equirectangular',
        labels= labels,
        width = 700,
        height = 300
    )
    
    fig.update_layout(
        geo=dict(
        showframe=False,
        showcoastlines=False,
        projection_type='equirectangular'),
        margin={"r":0,"t":20,"l":0,"b":0}
    )            

    return fig

def load_daily_data():
    """
    Read in data for COVID daily observations

    Parameters
    ----------
    None

    Returns
    -------
    dataframe
        Data for COVID daily observations for all countries
    """
    return pd.read_csv(os.path.join('data', 'raw', 'full_grouped.csv'))

def load_population_data():
    """
    Read in data for countries and populations
    
    Parameters
    ----------
    None

    Returns
    -------
    dataframe
        Data for countries and their population
    """
    return  pd.read_csv(os.path.join('data', 'processed', 'worldometer_data.csv'),
        usecols = ['Country/Region','Population'])

def load_country_code_data():
    """
    Read in data for countries and their locations
   
    Parameters
    ----------
    None

    Returns
    -------
    gdf
        Data for countries and their locations
    """
    name_conversion = {
        'East Timor': 'Timor-Leste',
        'Republic of the Congo': 'Congo (Kinshasa)',
        'Ivory Coast': 'Cote d\'Ivoire',
        'Macedonia': 'North Macedonia',
        'Myanmar': 'Burma',
        'Republic of Serbia': 'Serbia',
        'Taiwan': 'Taiwan*',
        'The Bahamas': 'Bahamas',
        'United Republic of Tanzania': 'Tanzania',
        'United States of America': 'US'
    }

    shapefile = os.path.join('data', 'ne_110m_admin_0_countries.shp')

    gdf = gpd.read_file(shapefile)[['ADMIN', 'ADM0_A3', 'geometry']]
    gdf.columns = ['country', 'country_code', 'geometry']

    # if a country name is in the above dict, replace the name in gdf with the value
    # of that key.
    gdf.loc[gdf['country'].isin(name_conversion.keys()), 'country'] = gdf['country'].map(name_conversion)

    return gdf

def join_population_data(daily_data, population_data):
    """
    Merge daily_data and population_data dataframes

    Parameters
    ----------
    daily_data : df 
        A dataframe of daily observation
    population_data : df 
        A dataframe of population    
    Returns
    -------
    merged df
        A merged dataframe from daily_data and population_data
    """
    return daily_data.merge(population_data, how = 'left', on = 'Country/Region')

def join_country_code_data(daily_data, country_code_data):
    """
    Merge daily_data and country_code_data dataframes

    Parameters
    ----------
    daily_data : df 
        A dataframe of daily observations
    country_code_data : df 
        A dataframe of country codes    
    Returns
    -------
    merged df
        A merged dataframe from daily_data and country_code_data
    """
    #new columns: country, country_code, geometry
    return country_code_data.merge(daily_data, left_on = 'country', right_on = 'Country/Region').drop(['country'], axis=1)

alt.data_transformers.disable_max_rows()
alt.renderers.set_embed_options(actions=False)

prev_vals = {'country': None, 'continent': None}
drop_cols = ['Country/Region', 'Population', 'country_code', 'geometry']

metrics = {
    'Population': 'first',
    'Confirmed': 'mean',
    'Deaths': 'mean',
    'Recovered': 'mean',
    'Active': 'mean',
    'New cases': 'mean',
    'New deaths': 'mean',
    'New recovered': 'mean',
    'WHO Region': 'first'
}

# Load all data from files
month_data = load_daily_data()
population_data = load_population_data()
country_code_data = load_country_code_data()

# Combine daily data with population & locations
countries_daywise_df = join_population_data(month_data, population_data)
countries_daywise_df = join_country_code_data(countries_daywise_df, country_code_data)

# Aggregate for World & Continents level. Will be used in line charts / the map.
continents_daywise_df = calculate_continent_daywise(countries_daywise_df)
world_daywise_df = calculate_world_daywise(countries_daywise_df)

# Find unique values for countries / continents to put in the dropdown list
# sorted in the alphabetical order
countries = list(set(countries_daywise_df['Country/Region'].tolist()))
continents = list(set(countries_daywise_df['WHO Region'].tolist()))
countries.sort()
continents.sort()

date_range_selection = html.Label([
    'Date Range Selection',
    dcc.DatePickerRange(
        id='date_selection_range',
        min_date_allowed=date(2020, 1, 22),
        max_date_allowed=date(2020, 7, 27),
        initial_visible_month=date(2020, 1, 22),
        start_date=date(2020, 1, 22),
        end_date=date(2020, 7, 27),
        stay_open_on_select=True,
        updatemode='bothdates'
    )
])

options_selection = html.Label([
    'Display Data',
    dcc.RadioItems(
        id='select_options',
        options=[
            {'label': 'Absolute', 'value': 'Absolute'},
            {'label': 'Per Capita', 'value': 'Per Capita'},
        ],
        value='Absolute',
        labelStyle={'margin-right': '25px'},
        inputStyle={'margin-right': '5px'}
    )
])

region_selection = html.Label([
    'Selection Mode',
    dcc.RadioItems(
        id='region_selection',
        options=[
            {'label': item.name, 'value': item.value} for item in SelectionMode
        ],
        value=SelectionMode.World.value,
        labelStyle={'margin-right': '25px'},
        inputStyle={'margin-right': '5px'}
    )
])

blank_div = html.Div([], id='blank_div')

continent_filter = dcc.Dropdown(
    id='continent_filter',
    value='Africa',
    options=[{'label': continent, 'value': continent} for continent in continents],
    multi=True
)

country_filter =  dcc.Dropdown(
    id='country_filter',
    value='Afghanistan',
    options=[{'label': country, 'value': country} for country in countries],
    multi=True,
    style={'height': '15px', 'display': 'inline-block'}
)

total_cases_linechart = html.Iframe(
    id='line_totalcases',
    style={'border-width': '0', 'width': '100%', 'height': '400px', 'margin': '0 -30 0 0', 'padding': '0'}
)

total_death_linechart = html.Iframe(
    id='line_totaldeaths',
    style={'border-width': '0', 'width': '100%', 'height': '400px', 'margin': '0 -30 0 0', 'padding': '0'}
)

total_recovered_linechart = html.Iframe(
    id='line_totalrecovered',
    style={'border-width': '0', 'width': '100%', 'height': '400px', 'margin': '0 -30 0 0', 'padding': '0'}
)

map = dcc.Graph(
    id='world_map',
    figure=generate_map(countries_daywise_df)
)

loading = html.Div(
    dcc.Loading(
        id='loading',
        type='circle'
    ),
    style={'height': '1px', 'width': '1920px'}
)
                                
# Setup app and layout/frontend
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
app.layout = dbc.Container([
    html.H3('WHO Coronavirus Disease (COVID-19) Dashboard'),
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    region_selection
                ])]),
            dbc.Row([
                dbc.Col([
                    blank_div
                ])]),
            dbc.Row([
                dbc.Col([
                    continent_filter
                    ])]),
            dbc.Row([
                dbc.Col([
                    country_filter
                    ])]),
            dbc.Row([
                dbc.Col([
                    date_range_selection
                ])]),
             dbc.Row([
                dbc.Col([
                    options_selection
                ])
            ])],
            lg=4),
        dbc.Col([  
            dbc.Col([
                map
            ])
        ])
    ]),
    dbc.Row([loading]),
    dbc.Row([     
        dbc.Col([
            total_cases_linechart
        ]),
        dbc.Col([
            total_death_linechart
        ]),
        dbc.Col([
            total_recovered_linechart
        ])
    ])
])      
        

# Set up callbacks/backend
@app.callback(
    Output('line_totalcases', 'srcDoc'),
    Output('line_totaldeaths', 'srcDoc'),
    Output('line_totalrecovered', 'srcDoc'),
    Output('world_map', 'figure'),
    Input('region_selection', 'value'),
    Input('country_filter', 'value'),
    Input('continent_filter', 'value'),
    Input('date_selection_range', 'start_date'),
    Input('date_selection_range', 'end_date'),
    Input('select_options', 'value'))
def filter_plot(mode, country, continent, start_date, end_date, options):
    """
    Plot interactive line charts and world map based on filtering features

    Parameters
    ----------
    mode : str 
        A mode to filter the plots/map (default is World mode)
    country : str
        A country to filter the plots/map
    continent : str
        A continent to filter the plots/map
    start_date : datetime
        A starting date to filter the plots/map
    end_date : datetime
        An ending date to filter the plots/map
    options : str 
        An option to filter the plots/map 
    Returns
    -------
    plots & map
        Filtered plots and map based on filtering features 
    """
    # Default is World mode
    # We only use daily countries data for map
    # as it does not understand which countries to display
    chart_data = world_daywise_df
    map_data = countries_daywise_df

    if mode == SelectionMode.Regions.value:
        # Continents mode
        if not isinstance(continent, list):
            continent = [continent]

        chart_data = continents_daywise_df[continents_daywise_df['WHO Region'].isin(continent)]
        map_data = map_data[map_data['WHO Region'].isin(continent)]
    elif mode == SelectionMode.Countries.value:
        # Countries mode
        if not isinstance(country, list):
            country = [country]

        chart_data = countries_daywise_df[countries_daywise_df['Country/Region'].isin(country)]
        map_data = chart_data

    chart_data = chart_data.query('Date >= @start_date & Date <= @end_date')
    map_data = map_data.query('Date >= @start_date & Date <= @end_date')

    # fix the error when groupby geometry or put it in the aggregate column
    temp = map_data.drop(['geometry', 'country_code', 'Date'], axis=1).groupby(['Country/Region']).agg(metrics).reset_index()
    map_data = join_country_code_data(temp, country_code_data)

    if is_perCapita(options):
        for metric in ['Confirmed', 'Deaths', 'Recovered']:
            chart_data[metric + '_per_capita'] = chart_data[metric] / chart_data['Population']
            map_data[metric + '_per_capita'] = map_data[metric] / map_data['Population']
            
        return plot(chart_data, 'Confirmed_per_capita', 'Confirmed Cases Per Capita'), \
                plot(chart_data, 'Deaths_per_capita', 'Confirmed Deaths Per Capita', True), \
                plot(chart_data, 'Recovered_per_capita', 'Confirmed Recoveries Per Capita'), \
                generate_map(map_data, 'Confirmed_per_capita', {'Confirmed_per_capita':'Confirmed Cases Per Capita'})

    return plot(chart_data, 'Confirmed', 'Confirmed Cases'), \
        plot(chart_data, 'Deaths', 'Confirmed Deaths', True), \
        plot(chart_data, 'Recovered', 'Confirmed Recoveries'), \
        generate_map(map_data, 'Confirmed', {'Confirmed':'Confirmed Cases'})


def plot(chart_data, metric, metric_name, show_legend=False):
    """
    Plot an interactive line chart with the time period on the x axis and a selected metric on the y axis

    Parameters
    ----------
    chart_data : df 
        A dataframe being plotted
    metric : str
        A metric being examined as specifed in the metrics dictionary
    metric_name : str
        A title of the plot that should be outputted
    show_legend: bool
        A value to determine if the chart should have legend
    Returns
    -------
    plot
        A line chart with a single or multiple lines depending on dataframe selection 
    """
    if show_legend:
        legend = alt.Legend(orient='bottom')
    else:
        legend = None

    chart = (alt.Chart(chart_data).mark_line().encode(
        x=alt.X('month(Date):T', title='Month', axis=alt.Axis(tickCount=7)),
        y=alt.Y(f'mean({metric}):Q', title=f'Average {metric_name}', axis=alt.Axis(tickCount=5)),
        color=alt.Color('Country/Region', title='Region', legend=legend))
        .properties(title=[f'{metric_name} Over Time'], width=240, height=180)
    )
 
    return (chart + chart.mark_point()).configure_legend(columns=2).interactive(bind_x=True).to_html()

@app.callback(
    Output('blank_div', 'style'),
    Output('continent_filter', 'style'),
    Output('country_filter', 'style'),
    Input('region_selection', 'value'))
def get_region_dropdown(mode):
    """
    Display / show the dropdown list for continents / countries based
    on whether the user selects World / Continents or Countries mode
    
    Parameters
    ----------
    mode : str
        A mode to filter the plots/map (default is World mode)
    Returns
    -------
    tuple
        The display modes for (World, Continents, Countries dropdown list)
    """
    if mode == SelectionMode.Regions.value:
        return {'display': 'none'}, {'display': 'block'}, {'display': 'none'}
    elif mode == SelectionMode.Countries.value:
        return {'display': 'none'}, {'display': 'none'}, {'display': 'block'}
    
    return {'height': '35px'}, {'display': 'none'}, {'display': 'none'}

@app.callback(
    Output('loading', 'children'),
    Input('region_selection', 'value'),
    Input('country_filter', 'value'),
    Input('continent_filter', 'value'),
    Input('date_selection_range', 'start_date'),
    Input('date_selection_range', 'end_date'),
    Input('select_options', 'value'))
def create_loading_screen(region, country, continent, start_date, end_date, option):
    time.sleep(1)
    
    return ''

if __name__ == '__main__':
    app.run_server(debug=True)

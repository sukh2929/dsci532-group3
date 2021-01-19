import os

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

# As there is only 1 callback function allowed to map to each output,
# we use this to check which value got updated and updating the plots
# accordingly
def is_updated(key, new_value):
    return ((prev_vals[key] is None and new_value is not None)
        or (prev_vals[key] is not None and prev_vals[key] != new_value))

def calculate_continent_daywise(countries_daywise_df):
    return calculate_continent_statistics(countries_daywise_df, 'Date')

def calculate_continent_statistics(countries_df, group_col):
    all_df = countries_df.drop(['Country/Region', 'Population'], axis=1).groupby([group_col, 'WHO Region']).agg('mean').reset_index()
    all_df['Country/Region'] = 'All'
    all_df['Population'] = population_data['Population'].sum()

    return all_df

def calculate_world_daywise(countries_daywise_df):
    return calculate_world_statistics(countries_daywise_df, 'Date')

def calculate_world_statistics(countries_df, group_col):
    world_df = countries_df.drop(['Country/Region', 'Population'], axis=1).groupby(group_col).agg('mean').reset_index()
    world_df['Country/Region'] = 'All'
    world_df['WHO Region'] = 'All'
    world_df['Population'] = population_data['Population'].sum()

    return world_df
    
alt.data_transformers.disable_max_rows()

month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

prev_vals = {'country': None, 'continent': None, 'start_date': None, 'end_date': None}

month_data = pd.read_csv(os.path.join('data', 'raw', 'full_grouped.csv'))

population_data = pd.read_csv(os.path.join('data', 'raw', 'worldometer_data.csv'),
    usecols = ['Country/Region','Population'])

df = month_data.merge(population_data, how = 'left', on = 'Country/Region')

metrics = ['Confirmed',	'Deaths', 'Recovered', 'Active', 'New cases', 'New deaths', 'New recovered']

agg_steps = {metric: 'mean' for metric in metrics}
agg_steps['WHO Region'] = 'first' # to keep this column in aggregate

countries_daywise_df = df
continents_daywise_df = calculate_continent_daywise(countries_daywise_df)
world_daywise_df = calculate_world_daywise(countries_daywise_df)

countries = ['All'] + list(set(df['Country/Region'].tolist()))
continents = ['All'] + list(set(df['WHO Region'].tolist()))
countries.sort()
continents.sort()

continent_selection = html.Label([
    'Continent Selection',
    dcc.Dropdown(
        id='continent_filter',
        value='All',  # REQUIRED to show the plot on the first page load
        options=[{'label': continent, 'value': continent} for continent in continents])
])

country_selection = html.Label([
    'Country Selection',
    dcc.Dropdown(
        id='country_filter',
        value='All',  # REQUIRED to show the plot on the first page load
        options=[{'label': country, 'value': country} for country in countries])
])

date_range_selection = html.Label([
    'Date range selection',
    dcc.DatePickerRange(
        id='date_selection_range',
        min_date_allowed=date(2020, 1, 22),
        max_date_allowed=date(2020, 7, 27),
        initial_visible_month=date(2020, 1, 22),
        start_date=date(2020, 1, 22),
        end_date=date(2020, 7, 27)
    )
])

total_cases_linechart = html.Iframe(
    id='line_totalcases',
    style={'border-width': '0', 'width': '100vw', 'height': '100vh'}
)

shapefile = os.path.join('data', 'ne_110m_admin_0_countries.shp')
#Read shapefile using Geopandas

gdf = gpd.read_file(shapefile)[['ADMIN', 'ADM0_A3', 'geometry']]
#Rename columns.
gdf.columns = ['country', 'country_code', 'geometry']

merged = gdf.merge(countries_daywise_df, left_on = 'country', right_on = 'Country/Region')
print(merged.head())

fig = px.choropleth(merged, locations="country_code",
                    color="Confirmed",
                    hover_name="Country/Region",
                    color_continuous_scale='Reds')

map = dcc.Graph(
    id='example-graph-1',
    figure=fig
)
                                
# Setup app and layout/frontend
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H1('COVID-19'),
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    continent_selection
                    ])]),
            dbc.Row([
                dbc.Col([
                    country_selection
                    ])]),
            dbc.Row([
                dbc.Col([
                    date_range_selection
                    ])])],
            md=4),
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    map
                ])
            ]),
            dbc.Row([
                dbc.Col([
                    total_cases_linechart
                ])
            ])],
            md=8)
        ])])

# Set up callbacks/backend
@app.callback(
    Output('line_totalcases', 'srcDoc'),
    Input('country_filter', 'value'),
    Input('continent_filter', 'value'),
    Input('date_selection_range', 'start_date'),
    Input('date_selection_range', 'end_date'))
def filter_plot(country, continent, start_date, end_date):
    data = world_daywise_df
    if is_updated('continent', continent):
        prev_vals['continent'] = continent
        if continent != 'All':
            data = continents_daywise_df[continents_daywise_df['WHO Region'] == continent]
        print('use continent')
    elif is_updated('country', country):
        prev_vals['country'] = country
        if country != 'All':
            data = countries_daywise_df[countries_daywise_df['Country/Region'] == country]
        print('use country')
    
    if is_updated('start_date', start_date) or is_updated('end_date', end_date):
        prev_vals['start_date'] = start_date
        prev_vals['end_date'] = end_date

        print(start_date, end_date)
        data = data.query('Date >= @start_date & Date <= @end_date')
        print(data[:5])

    # print(data[:5])
    return plot(data)

def plot(data):
    chart = alt.Chart(data).mark_line().encode(
        x=alt.X('month(Date):T'),
        y='mean(Confirmed):Q')
        
    return (chart + chart.mark_point()).interactive(bind_x=True).to_html()

if __name__ == '__main__':
    app.run_server(debug=True)
import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
import altair as alt
from vega_datasets import data
import dash_bootstrap_components as dbc
import pandas as pd
from pathlib import Path
from datetime import datetime

print(Path.cwd())
month_data = pd.read_csv(".\\data\\raw\\full_grouped.csv")

population_data = pd.read_csv(".\\data\\raw\\worldometer_data.csv",
    usecols = ['Country/Region', 'Continent','Population', 'WHO Region', 'Tot Cases/1M pop', 'Deaths/1M pop'])

df = month_data.merge(population_data, how = 'left', on = 'Country/Region')
df['Month'] = df['Date'].apply(lambda x: datetime.strftime(datetime.strptime(x, "%Y-%m-%d"), "%b"))
print(df.columns)
print(df.iloc[:3,])

month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

countries = ['All'] + df['Country/Region'].tolist()
# Setup app and layout/frontend
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = dbc.Container([
    html.H1('COVID-19'),
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                id='country_filter',
                value='All',  # REQUIRED to show the plot on the first page load
                options=[{'label': country, 'value': country} for country in countries])],
            md=4),
        dbc.Col(
            html.Iframe(
                id='line_totalcases',
                style={'border-width': '0', 'width': '100vw', 'height': '100vh'}), md=8)])])
# Set up callbacks/backend
@app.callback(
    Output('line_totalcases', 'srcDoc'),
    Input('country_filter', 'value'))
def plot_altair(country):
    data = df if country == 'All' else df[df['Country/Region'] == country]
    alt.data_transformers.disable_max_rows()
    chart = alt.Chart(data).mark_line().encode(
        x='Month',
        y='Confirmed',
        tooltip='Month').interactive()
    return chart.to_html()

if __name__ == '__main__':
    app.run_server(debug=True)
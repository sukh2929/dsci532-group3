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

alt.data_transformers.disable_max_rows()
# print(Path.cwd())
month_data = pd.read_csv(".\\data\\raw\\full_grouped.csv")

population_data = pd.read_csv(".\\data\\raw\\worldometer_data.csv",
    usecols = ['Country/Region','Population'])

daywise_df = month_data.merge(population_data, how = 'left', on = 'Country/Region')
daywise_df['Month'] = daywise_df['Date'].apply(lambda x: datetime.strftime(datetime.strptime(x, "%Y-%m-%d"), "%b"))

metrics = ['Confirmed',	'Deaths', 'Recovered', 'Active', 'New cases', 'New deaths', 'New recovered']
keep_cols = ['WHO Region']

agg_steps = {metric: 'mean' for metric in metrics}
for col in keep_cols:
    agg_steps[col] = 'first'

df = daywise_df.drop(['Date'], axis=1).groupby(['Month', 'Country/Region', 'Population']).agg(agg_steps).reset_index()

for col in keep_cols:
    del agg_steps[col]

all_df = daywise_df.drop(['Country/Region', 'Population', 'Date'], axis=1).groupby(['Month']).agg(agg_steps).reset_index()
all_df['Country/Region'] = 'All'
all_df['WHO Region'] = 'All'
all_df['Population'] = population_data['Population'].sum()

month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

df = pd.concat([all_df, df], axis=0)
df = df.sort_values(by=['Month', 'Country/Region'], ascending=[month_order, True])

countries = ['All'] + list(set(daywise_df['Country/Region'].tolist()))
countries.sort()

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
    data = df[df['Country/Region'] == country]

    chart = alt.Chart(data).mark_line().encode(
        x=alt.X('Month:N', sort=month_order),
        y='Confirmed:Q',
        tooltip='Month').interactive()
    return chart.to_html()

if __name__ == '__main__':
    app.run_server(debug=True)
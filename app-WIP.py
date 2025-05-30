# Imports
import requests
from pyjstat import pyjstat
import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import plotly.express as px
import plotly.io as pio
import dash
from dash import dcc, html, Input, Output

# API and CSV saving/loading
URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/DEMO_R_D3DENS?lang=EN"
CSV_FILENAME = "population_density.csv"

if os.path.exists(CSV_FILENAME):
    df = pd.read_csv(CSV_FILENAME)
    print("Data loaded from existing CSV file.")
else:
    print("Downloading data.")
    response = requests.get(URL)
    response.raise_for_status()
    dataset = pyjstat.Dataset.read(response.text)
    df = dataset.write('dataframe')
    df.to_csv(CSV_FILENAME, index=False)
    print(f"Data downloaded and saved to {CSV_FILENAME}.")

# Creating DataFrames
country_rename_map = {
    "Czechia": "Czech Republic",
}
df['Geopolitical entity (reporting)'] = df['Geopolitical entity (reporting)'].replace(country_rename_map)

# Current EU member states only
countries_list = [
    "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czech Republic",
    "Denmark", "Estonia", "Finland", "France", "Germany", "Greece",
    "Hungary", "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg",
    "Malta", "Netherlands", "Poland", "Portugal", "Romania", "Slovakia",
    "Slovenia", "Spain", "Sweden"
]

df_countries = df[df['Geopolitical entity (reporting)'].isin(countries_list)]
df_countries.reset_index(drop=True, inplace=True)

df_plot = df_countries.groupby(['Time', 'Geopolitical entity (reporting)'], as_index=False)['value'].mean()
df_pivot = df_plot.pivot(index='Time', columns='Geopolitical entity (reporting)', values='value').sort_index()
df_pivot.index = df_pivot.index.astype(str)

country_to_iso3 = {
    "Austria": "AUT", "Belgium": "BEL", "Bulgaria": "BGR", "Croatia": "HRV",
    "Cyprus": "CYP", "Czech Republic": "CZE", "Denmark": "DNK", "Estonia": "EST",
    "Finland": "FIN", "France": "FRA", "Germany": "DEU", "Greece": "GRC",
    "Hungary": "HUN", "Ireland": "IRL", "Italy": "ITA", "Latvia": "LVA",
    "Lithuania": "LTU", "Luxembourg": "LUX", "Malta": "MLT", "Netherlands": "NLD",
    "Poland": "POL", "Portugal": "PRT", "Romania": "ROU", "Slovakia": "SVK",
    "Slovenia": "SVN", "Spain": "ESP", "Sweden": "SWE"
}

# === DASH APP ===
app = dash.Dash(__name__)
app.title = "EU Population Density Dashboard"

years = df_pivot.index.astype(int).tolist()

app.layout = html.Div([
    html.H2("Population Density Change in the EU"),
    html.Div([
        html.Label("Start Year:"),
        dcc.Dropdown(id='start-year', options=[{'label': y, 'value': str(y)} for y in years],
                     value=str(min(years)), clearable=False),
        html.Label("End Year:"),
        dcc.Dropdown(id='end-year', options=[{'label': y, 'value': str(y)} for y in years],
                     value=str(max(years)), clearable=False)
    ], style={'width': '300px', 'marginBottom': '20px'}),

    dcc.Graph(id='choropleth-map')
])

@app.callback(
    Output('choropleth-map', 'figure'),
    Input('start-year', 'value'),
    Input('end-year', 'value')
)
def update_map(start_year, end_year):
    if int(start_year) >= int(end_year):
        return px.choropleth(title="Please select a valid year range.")

    try:
        df_change = pd.DataFrame()
        df_change[start_year] = df_pivot.loc[start_year]
        df_change[end_year] = df_pivot.loc[end_year]
    except KeyError:
        return px.choropleth(title="Data not available for selected years.")

    df_change = df_change.dropna()
    df_change['change_pct'] = ((df_change[end_year] - df_change[start_year]) / df_change[start_year]) * 100
    df_change.reset_index(inplace=True)
    df_change.rename(columns={'Geopolitical entity (reporting)': 'country'}, inplace=True)
    df_change['iso_alpha'] = df_change['country'].map(country_to_iso3)

    fig = px.choropleth(
        df_change,
        locations='iso_alpha',
        color='change_pct',
        hover_name='country',
        color_continuous_scale=[
            [0.0, "rgb(198,219,239)"],
            [0.5, "rgb(255,255,255)"],
            [1.0, "rgb(252,187,161)"]
        ],
        range_color=(df_change['change_pct'].min(), df_change['change_pct'].max()),
        labels={'change_pct': '% Change'},
        title=f"Change in Population Density from {start_year} to {end_year}"
    )

    fig.update_geos(
        showcountries=True, countrycolor="LightGray", showframe=False
    )

    fig.update_layout(
        geo=dict(scope='europe', projection_scale=1, center={"lat": 55, "lon": 15}),
        coloraxis_colorbar=dict(title="% Change"),
        margin={"r": 0, "l": 0, "t": 50, "b": 0},
        title_x=0.5
    )

    return fig

if __name__ == '__main__':
    app.run(debug=True)

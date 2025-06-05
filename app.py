# Imports
import requests
from pyjstat import pyjstat
import pandas as pd
import os
import plotly.express as px
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

# Preprocessing
country_rename_map = {
    "Czechia": "Czech Republic",
}
df['Geopolitical entity (reporting)'] = df['Geopolitical entity (reporting)'].replace(country_rename_map)

countries_list = [
    "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czech Republic",
    "Denmark", "Estonia", "Finland", "France", "Germany", "Greece",
    "Hungary", "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg",
    "Malta", "Netherlands", "Poland", "Portugal", "Romania", "Slovakia",
    "Slovenia", "Spain", "Sweden"
]

df_countries = df[df['Geopolitical entity (reporting)'].isin(countries_list)].copy()
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
app = dash.Dash(__name__, external_stylesheets=[
    "https://fonts.googleapis.com/css2?family=Roboto&display=swap"
])
app.title = "EU Population Density Dashboard"

years = df_pivot.index.astype(int).tolist()
latest_year = df['Time'].max()

app.layout = html.Div([
    html.H2("Population Density Change in the EU", style={
        'textAlign': 'center',
        'fontFamily': 'Roboto, sans-serif'
    }),
    
    html.Div(
        f"Data last updated: {latest_year}",
        style={
            'textAlign': 'center',
            'fontSize': '14px',
            'color': 'gray',
            'marginBottom': '10px',
            'fontFamily': 'Roboto, sans-serif'
        }
    ),

    html.Div([
        html.Div([
            html.Label("Start Year:", style={'fontFamily': 'Roboto, sans-serif'}),
            dcc.Dropdown(
                id='start-year',
                options=[{'label': y, 'value': str(y)} for y in years],
                value=str(min(years)),
                clearable=False,
                style={'width': '150px', 'fontFamily': 'Roboto, sans-serif'}
            )
        ], style={'marginRight': '20px'}),

        html.Div([
            html.Label("End Year:", style={'fontFamily': 'Roboto, sans-serif'}),
            dcc.Dropdown(
                id='end-year',
                options=[{'label': y, 'value': str(y)} for y in years],
                value=str(max(years)),
                clearable=False,
                style={'width': '150px', 'fontFamily': 'Roboto, sans-serif'}
            )
        ])
    ], style={
        'display': 'flex',
        'justifyContent': 'center',
        'alignItems': 'center',
        'flexWrap': 'wrap',
        'gap': '10px',
        'marginBottom': '20px',
        'fontFamily': 'Roboto, sans-serif'
    }),

    dcc.Graph(id='choropleth-map', style={'height': '700px'}),

    html.Div([
        html.Label("Select Country for Time Series:", style={
            'fontFamily': 'Roboto, sans-serif',
            'marginRight': '10px'
        }),
        dcc.Dropdown(
            id='country-select',
            options=[{'label': c, 'value': c} for c in countries_list],
            value='Germany',
            clearable=False,
            style={
                'width': '200px',
                'fontFamily': 'Roboto, sans-serif'
            }
        )
    ], style={
        'display': 'flex',
        'justifyContent': 'center',
        'alignItems': 'center',
        'marginTop': '20px',
        'marginBottom': '20px'
    }),

    dcc.Graph(id='line-chart', style={'height': '400px'})
], style={
    'backgroundColor': '#f9f9f9',
    'minHeight': '100vh',
    'padding': '20px',
    'fontFamily': 'Roboto, sans-serif'
})

@app.callback(
    Output('choropleth-map', 'figure'),
    Input('start-year', 'value'),
    Input('end-year', 'value')
)
def update_map(start_year, end_year):
    if int(start_year) >= int(end_year):
        fig = px.choropleth(title="Please select a valid year range.")
        return fig

    try:
        df_change = pd.DataFrame()
        df_change[start_year] = df_pivot.loc[start_year]
        df_change[end_year] = df_pivot.loc[end_year]
    except KeyError:
        fig = px.choropleth(title="Data not available for selected years.")
        return fig

    df_change = df_change.dropna()
    if df_change.empty:
        fig = px.choropleth(title="No data available for the selected year range.")
        return fig

    df_change['change_pct'] = ((df_change[end_year] - df_change[start_year]) / df_change[start_year]) * 100
    df_change.reset_index(inplace=True)
    df_change.rename(columns={'Geopolitical entity (reporting)': 'country'}, inplace=True)
    df_change['iso_alpha'] = df_change['country'].map(country_to_iso3)

    fig = px.choropleth(
        df_change,
        locations='iso_alpha',
        color='change_pct',
        hover_name='country',
        color_continuous_scale='Blues',
        range_color=(df_change['change_pct'].min(), df_change['change_pct'].max()),
        labels={'change_pct': '% Change'},
        title=f"Change in Population Density from {start_year} to {end_year}"
    )

    fig.update_geos(
        showcountries=True, countrycolor="LightGray", showframe=False
    )

    fig.update_layout(
        geo=dict(scope='europe', projection_scale=1, center={"lat": 55, "lon": 15}),
        coloraxis_colorbar=dict(
            title="% Change",
            x=0.85,
            xanchor="left",
            len=0.75
        ),
        margin={"r": 0, "l": 0, "t": 50, "b": 0},
        title_x=0.5
    )

    return fig

@app.callback(
    Output('line-chart', 'figure'),
    Input('country-select', 'value')
)
def update_line_chart(country):
    df_line = df_plot[df_plot['Geopolitical entity (reporting)'] == country]
    fig = px.line(df_line, x='Time', y='value', title=f"Population Density Over Time: {country}")
    fig.update_layout(
        xaxis_title='Year',
        yaxis_title='People per km²',
        title_x=0.5,
        margin={"r": 20, "l": 20, "t": 50, "b": 20}
    )
    return fig

if __name__ == '__main__':
    app.run(debug=True)

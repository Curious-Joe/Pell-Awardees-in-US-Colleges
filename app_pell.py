import os
import pathlib
import re

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np
from dash.dependencies import Input, Output, State
import cufflinks as cf
import plotly.express as px


# Initialize app

app = dash.Dash(__name__)
app.title = "Where are all the Pell Grantees?"
server = app.server

# Load data

APP_PATH = str(pathlib.Path(__file__).parent.resolve())

# ------------------------------------------------------------------
# data load and process
# ------------------------------------------------------------------
pell_df = pd.read_csv("data/pell_grant_data.csv")
state_year_wise_total = pell_df.groupby(['Institution State', 'Year'])[['Total Recipients']].sum()
state_year_wise_total.reset_index(inplace = True)

YEARS = pell_df['Year'].unique()
# YEARS = [i.split('-') for i in YEARS]
# def Extract(lst):
#     return [item[0] for item in lst]
# YEARS = Extract(YEARS)
# YEARS = [int(numeric_string) for numeric_string in YEARS]

# ------------------------------------------------------------------
# app layout
# ------------------------------------------------------------------

app.layout = html.Div([

    html.Div(
        id="header",
        children=[
            html.A(
                html.Img(id="logo", src=app.get_asset_url("dash-logo.png")),
                href="https://plotly.com/dash/",
            ),
            html.A(
                html.Button("Enterprise Demo", className="link-button"),
                href="https://plotly.com/get-demo/",
            ),
            html.A(
                html.Button("Source Code", className="link-button"),
                href="https://github.com/plotly/dash-sample-apps/tree/main/apps/dash-opioid-epidemic",
            ),
            html.H4(children="Pell Awardees Across the US"),
            html.P(
                id="description",
                children="Check where all the Pell awardee students are studying.",
            ),
        ],
    ),

    html.Div(
        id="slider-container",
        children=[
            html.P(
                id="slct_year",
                children="Drag the slider to change the year:",
            ),
            # dcc.Slider(
            #     id="years_slider",
            #     min=min(YEARS),
            #     max=max(YEARS),
            #     value=min(YEARS),
            #     marks={
            #         str(year): {
            #             "label": str(year),
            #             "style": {"color": "#7fafdf"},
            #         }
            #         for year in YEARS
            #     },
            # ),
            dcc.Dropdown(id="years_dropdn",
                         options=[{'label': i, 'value': i} for i in YEARS],
                         multi=False,
                         value=min(YEARS),
                         style={'width': "40%"}
                         ),
        ],
    ),

    html.Div(id='output_container', children=[]),
    html.Br(),

    dcc.Graph(id='pell_app', figure={})

])


# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components
@app.callback(
    [Output(component_id='output_container', component_property='children'),
     Output(component_id='pell_app', component_property='figure')],
    [Input(component_id='years_dropdn', component_property='value')]
)
def update_graph(year_slctd):
    print(year_slctd)
    print(type(year_slctd))

    container = "The year chosen by user was: {}".format(year_slctd)

    state_year_wise_total_copy = state_year_wise_total.copy()
    state_year_wise_total_copy = state_year_wise_total_copy[state_year_wise_total_copy["Year"] == year_slctd]
    # state_year_wise_total_copy = state_year_wise_total_copy[state_year_wise_total_copy["Affected by"] == "Varroa_mites"]

    # Plotly Express
    fig = px.choropleth(
        data_frame=state_year_wise_total_copy,
        locationmode='USA-states',
        locations='Institution State',
        scope="usa",
        color='Total Recipients',
        hover_data=['Institution State', 'Year', 'Total Recipients'],
        color_continuous_scale=px.colors.sequential.YlOrRd,
        labels={'Total Recipients': 'of Pell Grants'},
        template='plotly_dark'
    )

    # fig.update_layout(
    #     title_text="Bees Affected by Mites in the USA",
    #     title_xanchor="center",
    #     title_font=dict(size=24),
    #     title_x=0.5,
    #     geo=dict(scope='usa'),
    # )

    return container, fig


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)
import os
import pathlib
import re

import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import pandas as pd
import numpy as np
from dash.dependencies import Input, Output, State
import cufflinks as cf
import plotly.express as px
import plotly.graph_objects as go

# Initialize app

app = dash.Dash(__name__)
# app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Where are all the Pell Grantees?"
server = app.server

# Load data

APP_PATH = str(pathlib.Path(__file__).parent.resolve())

# ------------------------------------------------------------------
# data load and process
# ------------------------------------------------------------------
pell_df = pd.read_csv("data/pell_grant_data.csv")
# year-wise total recipients
state_year_wise_total_recip = pell_df.groupby(['Institution State', 'Year'])[['Total Recipients']].sum()
state_year_wise_total_recip.reset_index(inplace = True)

# year-wise total award $$
state_year_wise_total_award = pell_df.groupby(['Institution State', 'Year'])[['Total Awards']].sum()
state_year_wise_total_award.reset_index(inplace = True)

# year and institution wise total recipients
ins_year_wise_total_recip = pell_df.groupby(['Institution Name', 'Year'])[['Total Recipients']].sum()
ins_year_wise_total_recip.reset_index(inplace = True)

YEARS = pell_df['Year'].unique()
slider_labels = {}
for i in YEARS:
    str_year = str(i)
    slider_labels[i] = str_year

STATES = pell_df['Institution State'].unique()
STATES = [x for x in STATES if x == x]

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
            html.H4(children="Pell Awardees Across the US"),
            html.H4(
                id="description",
                children="Check where all the Pell awardee students are studying."
            ),
        ],
    ),

    html.Div(
        id='controls',
        children=[
            html.Div(
                id="slider-container",
                children=[
                    html.P(
                        id="slct_year",
                        children="Drag the slider to change the year:",
                    ),
                    dcc.RangeSlider(
                        id='year-range-slider',
                        min=min(YEARS),
                        max=max(YEARS),
                        step=1,
                        value=[min(YEARS), min(YEARS) + 3],
                        marks =
                        # slider_labels
                        {1999: '1999',
                         2000: '2000',
                         2001: '2001',
                         2002: '2002',
                         2003: '2003',
                         2004: '2004',
                         2005: '2005',
                         2006: '2006',
                         2007: '2007',
                         2008: '2008',
                         2009: '2009',
                         2010: '2010',
                         2011: '2011',
                         2012: '2012',
                         2013: '2013',
                         2014: '2014',
                         2015: '2015',
                         2016: '2016',
                         2017: '2017'}
                    ),
                ], className='six columns'),
                html.Div(
                    id='dropdn_state',
                    children=[
                        html.P(
                        id="slct_state",
                        children="Select the state(s) to look at the top 20 colleges:",
                        ),
                        html.Div(),
                        html.Div(),
                        dcc.Dropdown(
                            id='dropdown-state',
                             options= [{'label': i, 'value': i} for i in STATES],
                             value = ['IL'],
                             multi=True,
                             placeholder='Select State...',
                             style = {'width':'100%'}
                        ),
                    ], className='six columns'
                )
        ], className='row'
    ),
    html.Br(), html.Br(),
    html.Div(
        id = 'visuals',
        children=[
            html.Div(
                    id="slider_maps",
                    children=[
                    html.Div(
                        id='maps',
                        children=[
                            html.H3(id='map_title', children=[], style={"textAlign":"center"}),
                            dcc.Graph(
                                id='map_recipient',
                                figure={}
                            ),
                            dcc.Graph(
                                id='map_dollar',
                                figure={})
                        ]
                    ),
                    ], className='six columns', style={'background':'black'}
                ),

                html.Div(
                    id='rank_plot',
                    children=[
                        html.H3(id='rank_title', children=[], style={"textAlign":"center"}),
                        dcc.Graph(
                            id='top20_rank',
                            style={'width': '100%', 'height': '100vh'},
                            figure={}
                        )
                    ], className='six columns', style={'background':'black', 'height':'100vh'}
                )
        ], className='row',
    )
])


# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components
@app.callback(
    [Output(component_id='rank_title', component_property='children'),
    Output(component_id='map_title', component_property='children'),
     Output(component_id='map_recipient', component_property='figure'),
     Output(component_id='map_dollar', component_property='figure'),
     Output(component_id='top20_rank', component_property='figure')
     ],
    [Input(component_id='year-range-slider', component_property='value'),
     Input(component_id='dropdown-state', component_property='value')]
)
def update_graph(year_slctd, state_slctd):
    rank_title = f"Top 20 Universities with the Most Pell Grantees in {state_slctd}"
    map_title = f"Pell Distribution Across the US from {year_slctd[0]} to {year_slctd[1]}"

    input_print = "The year range chosen is: {}".format(year_slctd)
    year_slctd = np.array(range(year_slctd[0], year_slctd[1]+1))
    # print(type(year_slctd))

    # year-wise total recipients
    state_year_wise_total_recip_copy = state_year_wise_total_recip.copy()
    state_year_wise_total_recip_copy = state_year_wise_total_recip_copy[state_year_wise_total_recip_copy["Year"].isin(year_slctd)]
    state_year_wise_total_recip_copy = state_year_wise_total_recip_copy.groupby(['Institution State'])[['Total Recipients']].sum()
    state_year_wise_total_recip_copy.reset_index(inplace=True)

    # year-wise total award $$
    state_year_wise_total_award_copy = state_year_wise_total_award.copy()
    state_year_wise_total_award_copy = state_year_wise_total_award_copy[state_year_wise_total_award_copy["Year"].isin(year_slctd)]

    # year-wise top 20 institutions
    ins_year_wise_total_recip = pell_df[pell_df['Year'].isin(year_slctd)]
    ins_year_wise_total_recip = ins_year_wise_total_recip[ins_year_wise_total_recip['Institution State'].isin(state_slctd)]
    top_20 = ins_year_wise_total_recip.groupby(["Year"]).apply(lambda x: x.sort_values(["Total Recipients"], ascending=False)).reset_index(
        drop=True)
    top_20 = top_20.groupby('Year').head(20)
    top_20 = top_20.sort_values(by=["Year", "Total Recipients"], ascending=False)
    top_20['rank'] = tuple(zip(top_20['Total Recipients'], top_20['Institution Name']))
    top_20['rank'] = top_20.groupby('Year', sort=False)['rank'].apply(lambda x: pd.Series(pd.factorize(x)[0])).values + 1

    # Plot - Total recipients
    recip_fig = px.choropleth(
        data_frame=state_year_wise_total_recip_copy,
        locationmode='USA-states',
        locations='Institution State',
        scope="usa",
        color='Total Recipients',
        hover_data=['Institution State', 'Total Recipients'],
        color_continuous_scale= 'cividis',# px.colors.sequential.YlOrRd,
        labels={'Total Recipients': '# Awarded'},
        template='plotly_dark'
    )

    recip_fig.update_layout(
        title_text="Number of Pell Awardees",
        title_xanchor="center",
        # title_font=dict(size=24),
        title_x=0.5,
        geo=dict(scope='usa'),
        # coloraxis_colorbar_y=-0.1
        coloraxis_colorbar=dict(yanchor="top", y=1, x=-0.1,
                                ticks="outside")
    )

    # Plot - Total award $$
    award_fig = px.choropleth(
        data_frame=state_year_wise_total_award_copy,
        locationmode='USA-states',
        locations='Institution State',
        scope="usa",
        color='Total Awards',
        hover_data=['Institution State', 'Year', 'Total Awards'],
        # color_continuous_scale=px.colors.sequential.YlOrRd,
        color_continuous_scale = 'greens',
        labels={'Total Awards': '$$ Awarded'},
        template='plotly_dark'
    )

    award_fig.update_layout(
        title_text="Dollar Disbursed as Pell Award",
        title_xanchor="center",
        # title_font=dict(size=12),
        title_x=0.5,
        geo=dict(scope='usa'),
        coloraxis_colorbar=dict(yanchor="top", y=1, x=-0.1,
                                ticks="outside")
    )

    # Rank plot of top 20 colleges
    lineRank = px.line(top_20, x = 'Year', y='rank', line_group= 'Institution Name', color='Institution Name')
    scatterRank = px.scatter(top_20, x='Year', y='rank', text='rank', color_discrete_sequence=['slategrey'])
    scatterRank.update_traces(
        marker = dict(size = 20, symbol = 'square'),
        textposition = 'middle center'
    )

    rankPlot = go.Figure(data=lineRank.data + scatterRank.data)
    rankPlot.update_xaxes(dtick = 1)
    rankPlot.update_yaxes(visible=False, showticklabels=False, autorange='reversed')
    rankPlot.update_layout(
        showlegend=False,
        template = 'plotly_dark',
        # title={
        #     'text': f"Top 20 Universities with the Most Pell Grantees in {state_slctd}",
        #     'y': 0.95,
        #     'x': 0.5,
        #     'xanchor': 'center',
        #     'yanchor': 'top'}
    )

    return rank_title, map_title, recip_fig, award_fig, rankPlot


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)
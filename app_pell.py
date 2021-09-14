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
import plotly.express as px
import plotly.graph_objects as go

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
# year-wise total recipients
state_year_wise_total_recip = pell_df.groupby(['STATE', 'YEAR'])[['RECIPIENT']].sum()
state_year_wise_total_recip.reset_index(inplace = True)

# year-wise total award $$
state_year_wise_total_award = pell_df.groupby(['STATE', 'YEAR'])[['AWARD']].sum()
state_year_wise_total_award.reset_index(inplace = True)

# year and institution wise total recipients
ins_year_wise_total_recip = pell_df.groupby(['NAME', 'YEAR'])[['RECIPIENT']].sum()
ins_year_wise_total_recip.reset_index(inplace = True)

YEARS = pell_df['YEAR'].unique()
slider_labels = {}
for i in YEARS:
    str_year = str(i)
    slider_labels[i] = str_year

STATES = pell_df['STATE'].unique()
STATES = [x for x in STATES if x == x]

# ------------------------------------------------------------------
# app layout
# ------------------------------------------------------------------

app.layout = html.Div([

    html.Div(
        id="header",
        children=[
            # html.A(
            #     html.Img(id="logo", src=app.get_asset_url("dash-logo.png")),
            #     href="https://plotly.com/dash/",
            # ),
            html.H4(children="Pell Awardees Across the US"),
            html.H4(
                id="description",
                children="Lately, Pell Grant students, "
                         "the largest federal grant program for college students got a renewed attention because of its inclusion "
                         "in the US News & World Report university ranking calculation. "
                         "While it makes sense to incentivise institutions for having larger share of lower income students, "
                         "it can be an undue punishment for institutions that are in the states with lower population. "
                         "This dashboard provides a comparative view of the states, and rank universities in terms of their enrolled Pell grantees."
            ),
        ], style={'width':'95%', 'margin':25, 'textAlign': 'center'}
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
                    ], className='six columns', style={'background':'#252e3f', 'height':'100%'}
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
                    ], className='six columns', style={'background':'#252e3f', 'height':'100%'}
                )
        ], className='row', style={'height':'100vh'}
    ),

    # html.Div(
    #     id = 'credits',
    #     children=[
    #
    #     ]
    # )
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
    state_year_wise_total_recip_copy = state_year_wise_total_recip_copy[state_year_wise_total_recip_copy['YEAR'].isin(year_slctd)]
    state_year_wise_total_recip_copy = state_year_wise_total_recip_copy.groupby(['STATE'])[['RECIPIENT']].sum()
    state_year_wise_total_recip_copy.reset_index(inplace=True)

    # year-wise total award $$
    state_year_wise_total_award_copy = state_year_wise_total_award.copy()
    state_year_wise_total_award_copy = state_year_wise_total_award_copy[state_year_wise_total_award_copy['YEAR'].isin(year_slctd)]

    # year-wise top 20 institutions
    ins_year_wise_total_recip = pell_df[pell_df['YEAR'].isin(year_slctd)]
    ins_year_wise_total_recip = ins_year_wise_total_recip[ins_year_wise_total_recip['STATE'].isin(state_slctd)]
    top_20 = ins_year_wise_total_recip.groupby(['YEAR']).apply(lambda x: x.sort_values(['RECIPIENT'], ascending=False)).reset_index(
        drop=True)
    top_20 = top_20.groupby('YEAR').head(20)
    top_20 = top_20.sort_values(by=['YEAR', 'RECIPIENT'], ascending=False)
    top_20['rank'] = tuple(zip(top_20['RECIPIENT'], top_20['NAME']))
    top_20['rank'] = top_20.groupby('YEAR', sort=False)['rank'].apply(lambda x: pd.Series(pd.factorize(x)[0])).values + 1

    # Plot - Total recipients
    recip_fig = px.choropleth(
        data_frame=state_year_wise_total_recip_copy,
        locationmode='USA-states',
        locations='STATE',
        scope="usa",
        color='RECIPIENT',
        hover_data=['STATE', 'RECIPIENT'],
        color_continuous_scale= 'cividis',# px.colors.sequential.YlOrRd,
        labels={'RECIPIENT': 'Number'},
        template='plotly_dark'
    )

    recip_fig.update_layout(
        font_family="Trivia Serif",
        title_text="Total Number of Awardees",
        title_xanchor="center",
        title_x=0.5,
        geo=dict(scope='usa'),
        coloraxis_colorbar=dict(yanchor="top", y=1, x=-0.1,
                                ticks="outside")
    )

    recip_fig.update_traces(
        hovertemplate = None
    )

    # Plot - Total award $$
    award_fig = px.choropleth(
        data_frame=state_year_wise_total_award_copy,
        locationmode='USA-states',
        locations='STATE',
        scope="usa",
        color='AWARD',
        hover_data=['STATE', 'AWARD'],
        # color_continuous_scale=px.colors.sequential.YlOrRd,
        color_continuous_scale = 'greens',
        labels={'AWARD': 'Dollar'},
        template='plotly_dark'
    )

    award_fig.update_layout(
        font_family="Trivia Serif",
        title_text="Total Dollar Amount Awarded",
        title_xanchor="center",
        # title_font=dict(size=12),
        title_x=0.5,
        geo=dict(scope='usa'),
        coloraxis_colorbar=dict(yanchor="top", y=1, x=-0.1,
                                ticks="outside")
    )

    award_fig.update_traces(
        hovertemplate=None
    )

    # Rank plot of top 20 colleges
    lineRank = px.line(top_20, x = 'YEAR', y='rank', color='NAME')
    lineRank.update_traces(hoverinfo='skip')

    scatterRank = px.scatter(
        top_20,
        x='YEAR',
        y='rank',
        text='rank',
        color = 'NAME',
        custom_data = ['NAME']
    )
    scatterRank.update_traces(
        marker = dict(size = 20, symbol = 'square'),
        textposition = 'middle center'
    )

    rankPlot = go.Figure(data=lineRank.data + scatterRank.data)
    rankPlot.update_xaxes(dtick = 1)
    rankPlot.update_yaxes(visible=False, showticklabels=False, autorange='reversed')

    rankPlot.update_layout(
        font_family="Trivia Serif",
        showlegend=False,
        template = 'plotly_dark',
        margin={
        'l': 20,
        'r': 20,
        'b': 5,
        't': 5,
        'pad': 4},
        hoverlabel=dict(
            bgcolor="white",
            # font_size=16,
            font_family="Trivia Serif"
        )
    )
    rankPlot.update_traces(
        hovertemplate="<b>%{customdata[0]} </b> <br>Rank: %{text} </br> Year: %{x}"
    )

    return rank_title, map_title, recip_fig, award_fig, rankPlot


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True, port=2020)
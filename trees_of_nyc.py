# -*- coding: utf-8 -*-
"""
Created on Fri Apr 23 11:05:04 2021

To do:
    - start with empty map for faster load?
    - Keep zoom and location of user when filter change
    - show a nice empty map of nyc when no data selected or keep last setting
    - change of color for entries after 'Alive' if 'Alive' is not present
    - create table with district statistics
    - export function

possible analytical questions:
    - city improvement priorities
    - where are the most sick or dead trees (also in relative terms, e.g. per
      area, borogh or street length)

@author: Jonas
"""

#import math
#import getpass
import numpy as np # for numpy.where()
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
from sodapy import Socrata
import pandas as pd

# predefined order for different health options
# although 'Alive' exists but just once, probably errorneous entry
health_status_order = ['Good', 'Fair', 'Poor', 'Dead', 'Stump']

# max number of data points
data_limit = 20000


def get_data(data_limit=2000):

    # data source
    datasource = "data.cityofnewyork.us"
    dataset = "uvpi-gqnh"
    timeout = 20

    ##########################################
    # Insert personal app_token here. Alternatively, if you do not want your
    # token in this file you can create a file app_token.txt in the
    # same directory containing only the app_token string
    token = ''
    ##########################################

    ## Try to read token from file app_token.txt
    if token == '':
        try:
            token = str(np.loadtxt('app_token.txt', dtype=str, max_rows=1))
        except:
            token = ''

    if token != '':
        client = Socrata(datasource,token,timeout=timeout)
    else:
        client = Socrata(datasource, None, timeout=timeout)

    record_count_total = client.get(dataset, select="COUNT(*)")
    record_count_total = int(record_count_total[0]['COUNT'])

    # results_meta = client.get_metadata(dataset)
    results = client.get(dataset, limit=data_limit)
    client.close()

    # Convert to pandas DataFrame
    df = pd.DataFrame.from_dict(results)

    # make data types usable and consistent
    df['latitude']   = df['latitude'].astype(float)
    df['longitude']  = df['longitude'].astype(float)
    df['tree_dbh']   = df['tree_dbh'].astype(float)
    df['stump_diam'] = df['stump_diam'].astype(float)
    df['status']     = df['status'].astype(str)  # in order to handle NaN as 'nan'
    df['health']     = df['health'].astype(str)
    df['spc_latin']  = df['spc_latin'].astype(str)
    df['spc_common'] = df['spc_common'].astype(str)
    df['problems']   = df['problems'].astype(str)

    # replace small diameter values with a larger value just for visualization in a new column
    df['tree_dbh_vis'] = df.tree_dbh
    df.loc[df.status == 'Stump', 'tree_dbh_vis'] = df.stump_diam
    df.loc[df.tree_dbh_vis < 3, 'tree_dbh_vis'] = 3

    # clipping of extremely large diameter
    df.loc[df.tree_dbh_vis > 25, 'tree_dbh_vis'] = 25

    # replace values - variant 1, using numpy.where (strange... but it works)
    # df.spc_common = np.where(df.health == 'nan', df.status, df.spc_common)
    # replace NaN in health by status entries ('Stump' or 'Dead')
    # df['health'] = np.where(df['health'] == 'nan', df['status'], df['health'])

    # replace nan values with status entires - variant 2, use pandas.where
    df.spc_common = df.status.where(df.spc_common == 'nan', df.spc_common)
    df['health'] = df['status'].where(df['health'] == 'nan', df['health'])

    return df, record_count_total


def create_mapbox_figure(df, health_status_selected):

    if df.count()[0] > 0:

        # set legend entries in predefined order
        category_orders = [
            val for val in health_status_order if val in health_status_selected]

        # change color order to fit health status order
        my_colors = px.colors.DEFAULT_PLOTLY_COLORS.copy()
        my_colors[0] = px.colors.DEFAULT_PLOTLY_COLORS[2]  # 'Good' = green
        my_colors[1] = px.colors.DEFAULT_PLOTLY_COLORS[0]  # 'Fair' = blue
        my_colors[2] = px.colors.DEFAULT_PLOTLY_COLORS[1]  # 'Poor' = orange

        # set color values
        color_discrete_sequence = [my_colors[idx] for idx, val in enumerate(
            health_status_order) if val in health_status_selected]

        # set hover data
        hover_data = {'spc_latin': True,
                      'health': True,
                      'problems': True,
                      'tree_dbh': True,
                      'tree_dbh_vis': False,
                      'latitude': False,
                      'longitude': False,
                      'tree_id': True,
                      # it is important to have tree_id on the last position
                      # for single tree identification in get_single_tree_data()
                      }

        fig = px.scatter_mapbox(df,
                                lat="latitude",
                                lon="longitude",
                                hover_name='spc_common',
                                hover_data=hover_data,
                                color='health',
                                category_orders={'health': category_orders},
                                color_discrete_sequence=color_discrete_sequence,
                                size='tree_dbh_vis',
                                size_max=15,
                                mapbox_style="carto-positron",
                                height=1000,
                                )
        fig.update_layout(legend=dict(
                          yanchor="top",
                          y=0.99,
                          xanchor="left",
                          x=0.01
                          ))
    else:
        # show empty map
        #category_orders = health_status_order
        #color_discrete_sequence = my_colors
        fig = px.scatter_mapbox(df,
                                lat="latitude",
                                lon="longitude",
                                hover_name='spc_common',
                                mapbox_style="carto-positron",
                                height=1000)

    # this might help to remember maps position and zoom
    # still looking for better handling of new data and keeping
    # user positions...
    fig['layout']['uirevision'] = 'my_setup'

    return fig


# get data
df, record_count_total = get_data(data_limit)
df_count = df.count()[0]

# create health_status filter options
# although 'Alive' exists just once or so, probably errorneous entry
health_status_order = ['Good', 'Fair', 'Poor', 'Dead', 'Stump']
available_health_status = df['health'].unique().astype(str)

# 1. add common status elements first in order
health_status = [
    val for val in health_status_order if val in available_health_status]

# 2. add additional unexpected or new status elements at back
health_status.extend(
    [val for val in available_health_status if val not in health_status_order])

# compare health status lists and give warning if unexpected elements in available_health_status
if set(available_health_status) - set(health_status_order) != set():
    print('Warning: Not all health status options covered:', set(
        available_health_status) - set(health_status_order))

# create borough filter options
borough_unique = df['boroname'].unique()
borough_unique.sort()

# create first figure for startup with all data
fig_mapbox = create_mapbox_figure(df, health_status)

# set up app
external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, title='Street Trees')

app.layout = html.Div([
    html.H1(children='Hello trees of NYC'),

    dcc.Markdown('''
                 The NYC 2015 Street Tree Census counts {} entries in total. Entries shown in this application: {}

                 Data from here: [NYC OpenData 2015 Street Tree Census](https://data.cityofnewyork.us/Environment/2015-Street-Tree-Census-Tree-Data/uvpi-gqnh)
                 '''.format(record_count_total, df_count)),

    html.Div([

        html.Div([

            html.Div([

                # Map for visualization
                dcc.Graph(id='graph_mapbox', figure=fig_mapbox),

                html.Div([

                    html.Div([

                        # Checklist for selecting Boroughs
                        html.H3('Borough'),
                        dcc.Checklist(id='checklist_borough',
                                      # make checklist with total number of elements in each category like, e.g.: Queens (212)
                                      options=[
                                          {'label': val + ' ({})'.format(sum(df.boroname == val)), 'value': val} for val in borough_unique],
                                      value=borough_unique
                                      )
                    ], className='four columns'),

                    html.Div([

                        # Checklist for selecting health status
                        html.H3('Health status'),
                        dcc.Checklist(id='checklist_health',
                                      # make checklist with total number of elements in each category like, e.g.: Good (1426)
                                      options=[
                                          {'label': val + ' ({})'.format(sum(df.health == val)), 'value': val} for val in health_status],
                                      value=health_status
                                      )
                    ], className='four columns'),

                ], className='row')

            ], className='column')

        ], className='nine columns'),

        html.Div([

            # Table showing details of selected item
            html.H3('Selected tree'),
            dash_table.DataTable(
                id='selectedTreeTable',
                columns=[{'name': 'Trait', 'id': 'Trait'},
                         {'name': 'Value', 'id': 'Value'}],
            ),

        ], className='three columns'),

    ], className='row'),

    html.Div(id='TestText'),

], style={"margin-left": "30px", "margin-right": "30px", })


@app.callback(dash.dependencies.Output('graph_mapbox', 'figure'),
              dash.dependencies.Input('checklist_borough', 'value'),
              dash.dependencies.Input('checklist_health', 'value'),)
def update_graph_mapbox(borough_name, health_status):
    # filter data
    df_filter = df.loc[df['boroname'].isin(borough_name)]
    df_filter = df_filter.loc[df_filter['health'].isin(health_status)]
    fig = create_mapbox_figure(df_filter, health_status)
    return fig


@app.callback(dash.dependencies.Output('selectedTreeTable', 'data'),
              dash.dependencies.Input('graph_mapbox', 'clickData'),)
def get_single_tree_data(selectedValue):

    if selectedValue:
        tree_id = selectedValue['points'][0]['customdata'][-1]

        value = df.loc[df.tree_id == tree_id]

        value = value.T

        value['Trait'] = value.index

        value.columns = ['Value', 'Trait']

        data = value.to_dict('records')

        return data

    return None


# @app.callback(dash.dependencies.Output('TestText', 'children'),
#               dash.dependencies.Input('graph_mapbox', 'clickData'),)
# def get_single_tree_data_tmp(selectedValue):

#     if selectedValue:
#         tree_id = selectedValue['points'][0]['customdata'][-1]

#         value = df.loc[df.tree_id == tree_id]

#         value = value.T
#         columns = [val for val in value.columns]

#         data = value.to_dict('records')

#         return '{} ############ {}'.format(selectedValue, data)

#     return None


if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')

# -*- coding: utf-8 -*-
"""
@author: Jonas

Created on Fri Apr 23 11:05:04 2021

To do and nice to have:
    - start with empty map for faster load?
    - Keep zoom and location of user when filter change
    - show empty map of nyc when no data selected or keep latest viewer setting
    - create table with district statistics
    - create individual links to google maps / street view for each tree?
    - export function
    . better performance for complete data set
    
possible analytical questions:
    - city improvement priorities
    - where are the most sick or dead trees (also in relative terms, e.g. per
      area, borogh or street length)

"""

import numpy as np 
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
from sodapy import Socrata
import pandas as pd

## predefined order for different health options
## although 'Alive' exists but just once, probably erroneous entry
health_status_order = ['Good', 'Fair', 'Poor', 'Dead', 'Stump']

# max number of data points. Last time I checked there were 683788 data points available
data_limit = 20000


def get_data(data_limit=2000):

    # data source
    datasource = "data.cityofnewyork.us"
    dataset = "uvpi-gqnh"
    timeout = 30

    ########################################################################
    # Insert personal app_token here. Alternatively, if you do not want your
    # token published in this file you can create a file app_token.txt in the
    # same directory containing only the app_token string
    token = ''
    ########################################################################

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

    ## results_meta = client.get_metadata(dataset)
    results = client.get(dataset, limit=data_limit)
    client.close()

    ## Convert to pandas DataFrame
    df = pd.DataFrame.from_dict(results)

    # make data types usable and consistent
    df['tree_id']    = df['tree_id'].astype(int)
    df['latitude']   = df['latitude'].astype(float)
    df['longitude']  = df['longitude'].astype(float)
    df['tree_dbh']   = df['tree_dbh'].astype(float)
    df['stump_diam'] = df['stump_diam'].astype(float)
    df['status']     = df['status'].astype(str)  # in order to handle NaN as 'nan'
    df['health']     = df['health'].astype(str)
    df['spc_latin']  = df['spc_latin'].astype(str)
    df['spc_common'] = df['spc_common'].astype(str)
    df['problems']   = df['problems'].astype(str)

    ## replace small diameter values with higher values for visualization in a new column
    df['tree_dbh_vis'] = df.tree_dbh
    df.loc[df.status == 'Stump', 'tree_dbh_vis'] = df.stump_diam
    df.loc[df.tree_dbh_vis < 5, 'tree_dbh_vis'] = 5

    ## clipping of extremely large diameter
    df.loc[df.tree_dbh_vis > 25, 'tree_dbh_vis'] = 25

    ## replace values - variant 1, using numpy.where (strange... but it works)
    # df.spc_common = np.where(df.health == 'nan', df.status, df.spc_common)
    ## replace NaN in health by status entries ('Stump' or 'Dead')
    # df['health'] = np.where(df['health'] == 'nan', df['status'], df['health'])

    ## replace nan values with status entires - variant 2, use pandas.where
    df.spc_common = df.status.where(df.spc_common == 'nan', df.spc_common)
    df['health'] = df['status'].where(df['health'] == 'nan', df['health'])

    return df, record_count_total


def create_mapbox_figure(df):

    if df.count()[0] > 0:

        health_status_selected = df['health'].unique().astype(str)

        ## set legend entries in predefined order
        category_orders = [
            val for val in health_status_order if val in health_status_selected]


        ## change color order to fit health status order
        my_colors = px.colors.DEFAULT_PLOTLY_COLORS.copy()
        my_colors[0] = px.colors.DEFAULT_PLOTLY_COLORS[2]  # 'Good' = green
        my_colors[1] = px.colors.DEFAULT_PLOTLY_COLORS[0]  # 'Fair' = blue
        my_colors[2] = px.colors.DEFAULT_PLOTLY_COLORS[1]  # 'Poor' = orange

        ## set color values
        color_discrete_sequence = [my_colors[idx] for idx, val in 
            enumerate(health_status_order) if val in health_status_selected]

        ## set hover data
        hover_data = {'spc_latin': True,
                      'health': True,
                      'problems': True,
                      'tree_dbh': True,
                      'tree_dbh_vis': False,
                      'latitude': False,
                      'longitude': False,
                      'tree_id': True,
                      ## it is important to have tree_id on the last position
                      ## for single tree identification in get_single_tree_data()
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
        ## show empty map
        #category_orders = health_status_order
        #color_discrete_sequence = my_colors
        fig = px.scatter_mapbox(df,
                                lat="latitude",
                                lon="longitude",
                                hover_name='spc_common',
                                mapbox_style="carto-positron",
                                height=1000)

    ## this might help to remember maps position and zoom
    ## still looking for better handling of new data and keeping
    ## user positions...
    fig['layout']['uirevision'] = 'my_setup'

    return fig





def make_borough_options(df, borough_names):
    options = [{'label': val + ' ({})'.format(sum(df.boroname == val)), 'value': val} for val in borough_names]
    return options


def make_health_status_options(df, health_status):
    options = [{'label': val + ' ({})'.format(sum(df.health == val)), 'value': val} for val in health_status]
    return options



## get data
df, record_count_total = get_data(data_limit)
df_count = df.count()[0]

## create health_status filter options
## although 'Alive' exists just once or so, probably errorneous entry
health_status_order = ['Good', 'Fair', 'Poor', 'Dead', 'Stump']
health_status_unique = df['health'].unique().astype(str)

# 1. add known status elements first in order
health_status = [
    val for val in health_status_order if val in health_status_unique]

# 2. add additional unexpected or new status elements at back
health_status.extend(
    [val for val in health_status_unique if val not in health_status_order])

## compare health status lists and give warning if unexpected elements in health_status_unique
if set(health_status_unique) - set(health_status_order) != set():
    print('Warning: Not all health status options covered:', set(health_status_unique) - set(health_status_order))

## create borough filter options
borough_names = df['boroname'].unique()
borough_names.sort()

## set up app
external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, title='Street Trees', prevent_initial_callbacks=False)

app.layout = html.Div([ 
    
    html.Div([ # main row

        html.Div([ # first column, width 8

            html.H1(children='Hello Street Trees of New York City'),

            dcc.Markdown('''
                     The NYC 2015 Street Tree Census counts {} entries in total. Entries shown in this application: {}
    
                     Data from here: [NYC OpenData 2015 Street Tree Census](https://data.cityofnewyork.us/Environment/2015-Street-Tree-Census-Tree-Data/uvpi-gqnh)
                     '''.format(record_count_total, df_count)),


            ## Map for visualization
            dcc.Loading(id='loading_1', type='default',
                        children = dcc.Graph(id='graph_mapbox')),

            html.Div([ # column

                html.Div([

                    ## Checklist for selecting Boroughs
                    html.H3('Borough'),
                    dcc.Checklist(id='checklist_borough',
                                   # make checklist with total number of elements in each category like, e.g.: Queens (212)
                                   options=make_borough_options(df, borough_names),
                                   value=['Brooklyn']),

                ], className='three columns'),

                html.Div([

                    ## Checklist for selecting health status
                    html.H3('Health status'),
                    dcc.Checklist(id='checklist_health',
                                  # make checklist with total number of elements in each category like, e.g.: Good (1426)
                                  options=make_health_status_options(df, health_status),
                                  value=health_status),
                    

                    ## storage variables wrapped in Loading(). This gives a 
                    ## lifesign when large data sets are processed 
                    html.Br(),
                    html.Br(),

                    dcc.Loading(id='loading_2', type='default',
                            children=[
                                dcc.Store(id='store_df_filtered'),
                                dcc.Store(id='store_df_filtered_borough'),
                                dcc.Store(id='store_df_filtered_health'),
                                dcc.Store(id='store_df_graph_select'),]),

                    
                ], className='three columns'),

                html.Div([

                    ## Export section
                    html.H3('Export data'),

                    html.H6('Complete data set'),
                    
                    html.Button("Download CSV", id="btn_all_csv"),
                    dcc.Download(id="download_dataframe_all_csv"),
                    
                    html.Button("Download XLSX", id="btn_all_xlsx"),
                    dcc.Download(id="download_dataframe_all_xlsx"),

                    html.Br(),
                    html.Br(),

                    html.H6('Filtered data set'),
                    
                    html.Button("Download CSV", id="btn_filtered_csv"),
                    dcc.Download(id="download_dataframe_filtered_csv"),
                    
                    html.Button("Download XLSX", id="btn_filtered_xlsx"),
                    dcc.Download(id="download_dataframe_filtered_xlsx"),
                    
                    html.Br(),
                    html.Br(),

                    html.H6('User selected (graphical selection)'),
                    
                    html.Button("Download CSV", id="btn_graph_select_csv"),
                    dcc.Download(id="download_dataframe_graph_select_csv"),
                    
                    html.Button("Download XLSX", id="btn_graph_select_xlsx"),
                    dcc.Download(id="download_dataframe_graph_select_xlsx"),
                    
                ], className='six columns'),

            ], className='column'),

        ], className='eight columns'),

        html.Div([ # second sub column, width 3 for table on right side

            ## Table showing details of selected item
            html.H3('Selected tree'),
            
            dash_table.DataTable(
                id='selectedTreeTable',
                columns=[{'name': 'Trait', 'id': 'Trait'},
                         {'name': 'Value', 'id': 'Value'}],
                ),

        ], className='three columns'),

    ], className='row'),

    # ## only for testing and debugging
    # html.Div('TEST', id='test_text'),

])


                 
                 
##############################################################################
## call back functions
##############################################################################


    


## update filtered data
@app.callback(dash.dependencies.Output('store_df_filtered', 'data'),
              dash.dependencies.Output('store_df_filtered_borough', 'data'),
              dash.dependencies.Output('store_df_filtered_health', 'data'),
              dash.dependencies.Input('checklist_borough', 'value'),
              dash.dependencies.Input('checklist_health', 'value'),
              prevent_initial_call=False,)
def update_filtered_data(borough_name, health_status):
    
    df_filtered_borough = df.loc[df['boroname'].isin(borough_name)]
    df_filtered_health = df.loc[df['health'].isin(health_status)]
    
    df_filtered = df_filtered_borough.loc[df['health'].isin(health_status)]
    
    return df_filtered.to_json(date_format='iso', orient='split'), \
           df_filtered_borough.to_json(date_format='iso', orient='split'), \
           df_filtered_health.to_json(date_format='iso', orient='split')


## update mapbox figure
@app.callback(dash.dependencies.Output('graph_mapbox', 'figure'),
              dash.dependencies.Input('store_df_filtered', 'data'),
              prevent_initial_call=True,)
def update_graph_mapbox(jsonified_filtered_data):
    df_filtered = pd.read_json(jsonified_filtered_data, orient='split')
    return create_mapbox_figure(df_filtered)


## update checklist_borough
@app.callback(dash.dependencies.Output('checklist_borough', 'options'),
              dash.dependencies.Input('store_df_filtered_health', 'data'))
def update_borough_options(jsonified_filtered_data):
    df_filtered = pd.read_json(jsonified_filtered_data, orient='split')
    options = make_borough_options(df_filtered, borough_names)
    return options

## update checklist_health
@app.callback(dash.dependencies.Output('checklist_health', 'options'),
              dash.dependencies.Input('store_df_filtered_borough', 'data'))
def update_health_status_options(jsonified_filtered_data):
    df_filtered = pd.read_json(jsonified_filtered_data, orient='split')
    options = make_health_status_options(df_filtered, health_status)
    return options


## save user selected tree_ids
@app.callback(dash.dependencies.Output('store_df_graph_select', 'data'),
              dash.dependencies.Input('graph_mapbox', 'selectedData'))
def update_user_selected_data(selected_data):
    if selected_data:
        tree_ids = [val['customdata'][-1] for val in selected_data['points'] ]
        return tree_ids
    return None


########################
## data export functions
########################

## all data - csv
@app.callback(dash.dependencies.Output("download_dataframe_all_csv", "data"),
              dash.dependencies.Input("btn_all_csv", "n_clicks"),
              prevent_initial_call=True,)
def download_all_csv(n_clicks):
    df_download = df.drop(columns = ['tree_dbh_vis'])
    return dcc.send_data_frame(df_download.to_csv, "StreetTreesOfNYC.csv")

## all data - excel
@app.callback(dash.dependencies.Output("download_dataframe_all_xlsx", "data"),
              dash.dependencies.Input("btn_all_xlsx", "n_clicks"),
              prevent_initial_call=True,)
def download_all_xlsx(n_clicks):
    df_download = df.drop(columns = ['tree_dbh_vis'])
    return dcc.send_data_frame(df_download.to_excel, "StreetTreesOfNYC.xlsx", sheet_name="Sheet_1")

## filtered data - csv
@app.callback(dash.dependencies.Output("download_dataframe_filtered_csv", "data"),
              dash.dependencies.Input("btn_filtered_csv", "n_clicks"),
              dash.dependencies.Input('store_df_filtered', 'data'),
              prevent_initial_call=True,)
def download_filtered_csv(n_clicks, jsonified_filtered_data):
    
    ## make sure that the button was clicked (we ignore the trigger event from altered data)
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    
    if 'btn_filtered_csv' in changed_id:
        df_filter = pd.read_json(jsonified_filtered_data, orient='split')
        df_filter = df_filter.drop(columns = ['tree_dbh_vis'])
    
        return dcc.send_data_frame(df_filter.to_csv, "StreetTreesOfNYC_filtered.csv")
    
    return

## filtered data - excel
@app.callback(dash.dependencies.Output("download_dataframe_filtered_xlsx", "data"),
              dash.dependencies.Input("btn_filtered_xlsx", "n_clicks"),
              dash.dependencies.Input('store_df_filtered', 'data'),
              prevent_initial_call=True,)
def download_filtered_xlsx(n_clicks, jsonified_filtered_data):
    
    ## make sure that the button was clicked (we ignore the trigger event from altered data)
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    
    if 'btn_filtered_xlsx' in changed_id:
        df_filter = pd.read_json(jsonified_filtered_data, orient='split')
        df_filter = df_filter.drop(columns = ['tree_dbh_vis'])
    
        return dcc.send_data_frame(df_filter.to_excel, "StreetTreesOfNYC_filtered.xlsx", sheet_name="Sheet_1")
    
    return


## graph selected data - csv
@app.callback(dash.dependencies.Output("download_dataframe_graph_select_csv", "data"),
              dash.dependencies.Input("btn_graph_select_csv", "n_clicks"),
              dash.dependencies.Input('store_df_graph_select', 'data'),
              prevent_initial_call=True,)
def download_graph_select_csv(n_clicks, tree_ids):
    
    ## make sure that the button was clicked (we ignore the trigger event from altered data)
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    
    if 'btn_graph_select_csv' in changed_id and tree_ids:
        
        df_filter = df[df['tree_id'].isin(tree_ids)]
        
        df_filter = df_filter.drop(columns = ['tree_dbh_vis'])
    
        return dcc.send_data_frame(df_filter.to_csv, "StreetTreesOfNYC_graph_select.csv")
    
    return

## graph selected data - excel
@app.callback(dash.dependencies.Output("download_dataframe_graph_select_xlsx", "data"),
              dash.dependencies.Input("btn_graph_select_xlsx", "n_clicks"),
              dash.dependencies.Input('store_df_graph_select', 'data'),
              prevent_initial_call=True,)
def download_graph_select_xlsx(n_clicks, tree_ids):
    
    ## make sure that the button was clicked (we ignore the trigger event from altered data)
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    
    if 'btn_graph_select_xlsx' in changed_id and tree_ids:
         
        df_filter = df[df['tree_id'].isin(tree_ids)]
        
        df_filter = df_filter.drop(columns = ['tree_dbh_vis'])
    
        return dcc.send_data_frame(df_filter.to_excel, "StreetTreesOfNYC_graph_select.xlsx", sheet_name="Sheet_1")
    
    return



## extract all data for a single tree selected by the user
@app.callback(dash.dependencies.Output('selectedTreeTable', 'data'),
              dash.dependencies.Input('graph_mapbox', 'clickData'),)
def get_single_tree_data(selected_value):

    ## selected_value has the following exemplary structure:
    ## {'points': [{'curveNumber': 4, 'pointNumber': 554, 'pointIndex': 554, 'lon': -73.94091248, 'lat': 40.71911554, 'hovertext': 'Stump', 'marker.size': 5, 'customdata': ['nan', 'Stump', 'nan', 0, 5, 40.71911554, -73.94091248, '221731']}]}
    ## we are just interested in the tree_id which is the last value of
    ## 'customdata'
    if selected_value:
        tree_id = selected_value['points'][0]['customdata'][-1]

        ## get complete entry for tree_id
        value = df.loc[df.tree_id == tree_id]

        ## remove tree_dbh_vis
        value = value.drop(columns = ['tree_dbh_vis'])

        ## Transpose 
        value = value.T

        ## copy original row names into a new column
        value['Trait'] = value.index
        
        ## create new column names
        value.columns = ['Value', 'Trait']
        
        # convert dataframe into dict which can be fed into DataTable
        data = value.to_dict('records')

        return data

    return None



# ## only for testing and debugging
# @app.callback(dash.dependencies.Output('test_text', 'children'),
#               dash.dependencies.Input("store_df_graph_select", "data"))
# def temp_fun(selected_values):

#     if selected_values:
        
#         #tree_ids = [val['customdata'][-1] for val in selected_values['points'] ]
        
#         #df = pd.DataFrame.from_dict(selected_value)
#         return '{} ############ '.format(selected_values)

#     return None



if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')

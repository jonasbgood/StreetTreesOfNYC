# StreetTreesOfNYC

This app visualizes the data from the 2015 New York City Street Tree Census. It also
provides options for filtering and export of the data.

The original data source is hosted at:
https://data.cityofnewyork.us/Environment/2015-Street-Tree-Census-Tree-Data/uvpi-gqnh

## Requirements

The following python packages are required:
 - numpy 
 - dash 
 - dash_table
 - dash_core_components 
 - dash_html_components
 - plotly 
 - sodapy 
 - pandas
 
In python these libraries can be installed using pip with the following command:
 
```python
        pip install numpy dash dash_table dash_core_components dash_html_components plotly sodapy pandas
```


## Settings before starting the application

### App token access for NYC OpenData:

Before you launch this app you can insert your personal app token for the NYC
OpenData server in the pre-defined section in trees_of_nyc.py

This app will start also without any app_token. Nevertheless, transfer bandwidth
might be restricted and access might be cut off any time. For further information
and creating your own app_token, see:
https://dev.socrata.com/foundry/data.cityofnewyork.us/uvpi-gqnh

### Data limit:

You can limit the amount of data which is loaded by the webserver by setting
data_limit. Keep in mind: if only a part of the full data set is selected it
is unknown (at least to me) which data will be downloaded from the data
server.


## Start the application 

```python
python trees_of_nyc.py
```

Note: depending on data_limit it might take a while until the data is loaded 
and the webserver is ready. The dasboard can now be opened in your web browser:

http://localhost:8050

and from other devices in your local network

http://your-ip-adress-here:8050


## How the app works

Trees are represented by the colored circles in the map. The color of each
circle represents the individuals health status. The diameter of each circle
roughly relates to the diameter of the tree in inch. 

The user can filter street trees from different boroughs and with different health
conditions. By clicking on a single tree all available information for this tree
is shown in the table on the right. The user can also select areas of interest
using the tools provided in the map.

The complete data set as well as the filtered and selected data can be exported and 
downloaded to csv and xlsx files.

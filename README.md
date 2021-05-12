# StreetTreesOfNYC

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
 
In python these can be installed using pip with the following command:
 
```python
        pip install numpy dash dash_table dash_core_components dash_html_components plotly sodapy pandas
```


## Settings before starting the application

### Credentials for NYC OpenData:

In order to start this app insert your personal app_token for the NYC open
data server in the pre-defined section in TreesOfNYC.py

This app will start also without any app_token. Nevertheless, it might be
restricted and access might cut off any time. For further information and
creating your own app_token, see:
https://dev.socrata.com/foundry/data.cityofnewyork.us/uvpi-gqnh

### Data limit:

You can limit the amount of data which is loaded by the webserver by setting
data_limit. Keep in mind: if only a part of the full data set is selected it
is unknown (at least to me) which data will be downloaded from the data
source server.


## Start the application 

```python
python trees_of_nyc.py
```

Note: depending on the data_limit it might take while until the data is loaded 
and the webserver is ready. The dasboard can now be opened in your web browser:

http://localhost:8050

other from other devices in your local network

http://your-ip-adress-here:8050


## How the app works

Trees are represented by the colored circles in the map. The color of each
circle represents the individuals health status. The diameter of each circle
roughly relates to the diameter of the tree in inch. 

The user can select trees from a list boroughs and different health conditions. 
By clicking on a single tree all available information for this tree is shown
in the table on the right.

The complete data sat as well as the filtered data can be exported and 
downloaded to csv and xlsx files.

The user can also select areas of interest using the tools provided in the map.
All trees in a selected area can then be exporte.



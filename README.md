# StreetTreesOfNYC

## Requirements

The following python packages are required:
 - pandas
 - numpy
 - plotly
 - dash
 - sopdapy
 
In python these can be installed using pip with the following command:
 
        pip install dash dash_table dash_core_components dash_html_components plotly sodapy pandas
 

## Settings before starting the application

### Credentials:

In order to start your app insert your personal credentials for the NYC open
data server. Enter the following data in the pre-defined section in TreesOfNYC.py
 - username
 - password
 - app token


### Data limit:

You can limit the amount of data which is loaded by the webserver by setting
data_limit. Keep in mind: if only parts of the full data set is selected it is unknown
which data will be downloaded from the data source server.


## Start the application 

```python
python TreesOfNYC.py

Note: depending on the data_limit it might take while until the data is loaded 
and the webserver is ready. The dasboard can now be opened in your web browser:

http://localhost:8050

other from other devices in your local network

http://your-ip-adress-here:8050


## How the app works

Trees are represented by the colored circles in the map. The color of each
circle represents the health status. The diameter of each circle roughly 
relates to the diameter of the tree in inch. 

The user can select trees from certain boroughs and certain health conditions.

By clicking on a single tree all available information for this tree is shown
in the table on the right.


'''This script can be used to collect, export to prom and view the data here'''
import time
import os
from datetime import datetime, timedelta
from threading import Thread
from hyundai_kia_connect_api import VehicleManager
from flask import Flask, render_template, Response
from prometheus_client import Gauge, generate_latest
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import folium
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from dotenv import load_dotenv

load_dotenv()

REQUIRED_ENV_VARS = ["BLUELINKUSER", "BLUELINKPASS", "BLUELINKPIN", "BLUELINKREGION", "BLUELINKBRAND", "BLUELINKVID"]
env_vars = {name: os.getenv(name) for name in REQUIRED_ENV_VARS}

missing_vars = [name for name, value in env_vars.items() if value is None]
if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Required environment variables, use .env for these
username = username = env_vars["BLUELINKUSER"] # Username used to access the API
password = username = env_vars["BLUELINKPASS"] # Password used to access the API
pin = username = env_vars["BLUELINKPIN"] # Pin used to access the API
region = username = env_vars["BLUELINKREGION"] # Region used to access the API
brand = username = env_vars["BLUELINKBRAND"] # Brand used to access the API
vehicle_id = username = env_vars["BLUELINKVID"] # Vehicle ID used to access the API

# Optional environment variables
UPDATE = os.getenv("BLUELINKUPDATE", "False") == "True"
APILIMIT = int(os.getenv("BLUELINKLIMIT", 30)) # Max API requests per 24 hours
PORT = int(os.getenv("BLUELINKPORT", 8001))
HOST = os.getenv("BLUELINKHOST", '0.0.0.0')

vm = VehicleManager(region=int(region), brand=int(brand), username=username, password=password, pin=pin)
vm.check_and_refresh_token()
vm.update_all_vehicles_with_cached_state()
vehicle = vm.get_vehicle(vehicle_id)

# Initialize Flask app
app = Flask(__name__)

# Prometheus metrics
charging_level_gauge = Gauge('vehicle_data_charging_level', 'Charging level')
mileage_gauge = Gauge('vehicle_data_mileage', 'Mileage')
battery_health_gauge = Gauge('vehicle_data_battery_health', 'Battery health percentage')
ev_driving_range_gauge = Gauge('vehicle_data_ev_driving_range', 'Estimated driving range')

# Rate limit variables
interval_between_requests = timedelta(seconds=86400 // APILIMIT)
log_file = 'vehicle_data.log'

def fetch_and_update_metrics():
    '''Fetch data from the vehicle API and update Prometheus metrics.''''
    # Refresh the token and update vehicle data
    vm.check_and_refresh_token()
    vm.update_all_vehicles_with_cached_state()
    
    # Fetch the data
    charging_level = vehicle.ev_battery_percentage
    mileage = vehicle.odometer
    battery_health = vehicle.ev_battery_soh_percentage if vehicle.ev_battery_soh_percentage else 0
    ev_driving_range = vehicle._ev_driving_range_value
    longitude = vehicle._location_longitude
    latitude = vehicle._location_latitude
    
    # Update Prometheus metrics
    charging_level_gauge.set(charging_level)
    mileage_gauge.set(mileage)
    battery_health_gauge.set(battery_health)
    ev_driving_range_gauge.set(ev_driving_range)
    
    # Log the data to a file
    with open(log_file, 'a') as file:
        file.write(f"{datetime.now().isoformat()}, Charging Level: {charging_level}%, Mileage: {mileage} miles, Battery Health: {battery_health}%, EV Driving Range: {ev_driving_range} miles, long: {longitude}, lat: {latitude}\n")

    print(f"{datetime.now().isoformat()}, Charging Level: {charging_level}%, Mileage: {mileage} miles, Battery Health: {battery_health}%, EV Driving Range: {ev_driving_range} miles, long: {longitude}, lat: {latitude}")

def scheduled_update():
    '''Schedule periodic updates to fetch and update vehicle data while adhering to the API rate limits.'''
    while True:
        now = datetime.now()
        next_update = (now + interval_between_requests).replace(second=0, microsecond=0)
        fetch_and_update_metrics()
        sleep_duration = (next_update - datetime.now()).total_seconds()
        time.sleep(max(0, sleep_duration))

def makedata():
    '''Load and preprocess vehicle data from the log file into a Pandas DataFrame.'''
    # Load your data (no header)
    vehicle_data = pd.read_csv('/opt/pyvisioniq/vehicle_data.log', header=None)

    # Extract timestamp and set it as the index
    vehicle_data['Timestamp'] = pd.to_datetime(vehicle_data[0].str.split(',').str[0], format='%Y-%m-%dT%H:%M:%S.%f')
    vehicle_data = vehicle_data.set_index('Timestamp')

    # Drop the first column with mixed data
    vehicle_data = vehicle_data.drop(columns=[0])

    # Rename columns based on their position after dropping
    vehicle_data = vehicle_data.rename(columns={
        1: 'Charging Level',
        2: 'Mileage',
        3: 'Battery Health',
        4: 'EV Driving Range',
        5: 'Longitude',
        6: 'Latitude'
    })

    # Data Cleaning: Remove '%', 'miles', and other non-numeric characters from relevant columns
    vehicle_data['Charging Level'] = (
        vehicle_data['Charging Level'].astype(str).str.replace(r'[^\d.]', '', regex=True).astype(float)
    )
    vehicle_data['EV Driving Range'] = (
        vehicle_data['EV Driving Range'].astype(str).str.replace(r'[^\d.]', '', regex=True).astype(float)
    )
    vehicle_data['Mileage'] = (
        vehicle_data['Mileage'].astype(str).str.replace(r'[^\d.]', '', regex=True).astype(float)
    )
    vehicle_data['Battery Health'] = (
        vehicle_data['Battery Health'].astype(str).str.replace(r'[^\d.]', '', regex=True).astype(float)
    )
    vehicle_data['Longitude'] = (
        vehicle_data['Longitude'].astype(str).str.replace(r'[^\d\-.]', '', regex=True).astype(float)
    )
    vehicle_data['Latitude'] = (
        vehicle_data['Latitude'].astype(str).str.replace(r'[^\d\-.]', '', regex=True).astype(float)
    )
    
    return vehicle_data

def rangeplot(data):
    '''Generate a plot of the charging level over time.'''
    plt.figure(figsize=(10, 6))
    plt.plot(data.index, data['Charging Level'], label='Charging Level', marker='o', linestyle='-')
    plt.xlabel('Timestamp')
    plt.ylabel('%')
    plt.title('Charging Level Over Time')
    plt.legend()
    plt.xticks(rotation=45, ha="right")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%y %H:%M'))
    plt.grid(axis='y')
    fig = plt.gcf() 
    plt.close()
    return fig

def mileageplot(data):
    '''Generate a plot of the mileage over time.'''
    plt.figure(figsize=(10,6))
    plt.plot(data.index, data['Mileage'], label='Mileage', marker='x', linestyle='-')
    plt.xlabel('Timestamp')
    plt.ylabel('Miles')
    plt.title('Total Miles')
    plt.legend()
    plt.xticks(rotation=45, ha="right")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%y %H:%M'))
    plt.grid(axis='y')
    fig = plt.gcf() 
    plt.close()
    return fig

def mapit(data):
    '''Create and save a map visualization of the vehicle's location data.'''
    map_center = [data['Latitude'].mean(), data['Longitude'].mean()]
    my_map = folium.Map(location=map_center, zoom_start=12)

    for index, row in data.iterrows():
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=5,
            color="blue",
            fill=True,
            fill_color="blue",
            fill_opacity=0.7,
            popup=f"Charging Level: {row['Charging Level']}%, Mileage: {row['Mileage']} miles"
        ).add_to(my_map)

    my_map.save("ev_map.html")
    return my_map

def mileage_png():
    '''Generate and return a PNG image of the mileage plot.'''
    data = makedata()
    fig = mileageplot(data)
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

def range_png():
    '''Generate and return a PNG image of the charging level plot.'''
    data = makedata()
    fig = rangeplot(data)
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

# Update Flask routes
@app.route('/metrics')
def metrics():
    '''Endpoint to expose Prometheus metrics.'''
    return Response(generate_latest(), mimetype='text/plain')

@app.route('/map')
def map():
    '''Endpoint to render the map visualization.'''
    return render_template('index.html', map=mapit(makedata())._repr_html_())

@app.route('/mileage.png')
def mileage():
    '''Endpoint to serve the mileage plot as a PNG image.''''
    return mileage_png()

@app.route('/range.png')
def range():
    '''Endpoint to serve the charging level plot as a PNG image.'''    
    return range_png()

if __name__ == "__main__":
    if UPDATE:
    # Start the scheduled update in a separate thread
        update_thread = Thread(target=scheduled_update)
        update_thread.daemon = True
        update_thread.start()
    else:
        print("Not updating.")
    
    # Start the Flask app
    app.run(host=HOST, port=PORT)


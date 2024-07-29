# PyVisionIQ - Hyundai/Kia Vehicle Data Monitor & Visualization
PyVisionIQ is a Python tool designed to fetch data from the Hyundai/Kia Connect API, log it, and visualize key metrics of your electric vehicle. It also exposes data for Prometheus monitoring.

## Features
* Data collection regularly fetches:
  * Charging level
  * Mileage
  * Battery health
  * Driving range
  * Location
* Data Logging: Stores fetched data in vehicle_data.csv (CSV).
* Prometheus Metrics: Exposes data via /metrics endpoint.
* Visualization:
    * Interactive map (Folium) at /map
    * Charging level plot at `/charge.png`
    * Mileage plot at `/mileage.png`
    * EV Driving Range plot at `/range.png`
* Rate Limiting: Respects API limits to avoid blocks.
* Environment Variables: Secure configuration using .env file.
* Systemd Service: Easy deployment on Linux (pyvisioniq.service).
## Prerequisites
* Python 3.x
* Libraries: Install from requirements.txt:

  ```Bash
  pip install -r requirements.txt
  ```
* Hyundai/Kia Connect Account  

## Setup
1. Environment Variables: Create .env file:
   ```
   BLUELINKUSER=your_username
   BLUELINKPASS=your_password
   BLUELINKPIN=your_pin
   BLUELINKREGION=your_region_code
   BLUELINKBRAND=your_brand_code
   BLUELINKVID=your_vehicle_id
   ```
   Region & Brand: Find codes in hyundai_kia_connect_api docs.  
2. (Optional) Other Variables:
   ```
   BLUELINKUPDATE: "True" to fetch data, "False" for dry run (default).
   BLUELINKLIMIT: API requests/day (default 30).
   BLUELINKPORT: Flask app port (default 8001).
   BLUELINKHOST: Flask app host (default '0.0.0.0').
   BLUELINKCSV: CSV file path (default './vehicle_data.csv').
   ```
## Installation & Running
1. Clone the repository:
   ```bash
   git clone https://github.com/mhuot/pyvisoniq.git
   cd pyvisioniq
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. Dependencies: 
   ```bash
   pip install -r requirements.txt
   ```
4. Systemd (Linux):
    Copy pyvisioniq.service to /etc/systemd/system/
    ```bash
   sudo systemctl enable pyvisioniq.service
   sudo systemctl start pyvisioniq.service
   ```
5. Accessing Data
   Prometheus: http://your_host:8001/metrics
   Map: http://your_host:8001/map
   Plots:
   Charging: http://your_host:8001/range.png
   Mileage: http://your_host:8001/mileage.png

## Linting with Pylint

Ensure you have activated the virtual environment before running `pylint`.  

If you encounter import errors with `pylint`, ensure that your environment is correctly set up and that the `.pylintrc` file is present in the project root. 
 
You can add the following to the `.pylintrc` file to include the virtual environment's site-packages:

## Additional Notes
* Data updates run automatically respecting rate limits.  
* Log file must be writable.  
* Consider Gunicorn/uWSGI for production Flask.
* Customize map in code for advanced visuals.


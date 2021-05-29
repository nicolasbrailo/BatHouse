from datetime import datetime
import json
import requests
import urllib.parse

def register_flask(app, cfg):
    @app.route('/weather/hourly')
    def temp():
        url = "https://api.openweathermap.org/data/2.5/onecall?lat={}&lon={}&appid={}&exclude=current,minutely,daily".format(cfg['lat'], cfg['lon'], cfg['openweathermap_api_key'])
        hourlies = requests.get(url).json()['hourly']
        forecast = []
        for hour in hourlies:
            forecast.append({
                    'time': str( datetime.fromtimestamp(int(hour['dt'])) ),
                    'temp': int(hour['temp'] - 273.15),
                    'feels_like': int(hour['feels_like'] - 273.15),
                    'wind_speed_ms': round(float(hour['wind_speed']), 2),
                })
        return json.dumps(forecast)


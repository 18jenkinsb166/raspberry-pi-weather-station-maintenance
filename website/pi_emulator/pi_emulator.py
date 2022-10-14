import requests
from random import uniform, randint
import os

# logging
import logging
import logger as logger_module

SERVER_URL = 'http://127.0.0.1:5000/data'


# setup logger
logger_module.setup_logger(os.path.basename(__file__))
logger = logging.getLogger(os.path.basename(__file__))


with open("secret_key.key", "r") as file:
    SECRET_KEY = file.read()


output_safe_secret_key = SECRET_KEY[:4] + "*"*(len(SECRET_KEY)-8) + SECRET_KEY[-4:]
logger.info(f"using secret key:   {output_safe_secret_key}")
logger.info(f"using server url:   {SERVER_URL}")

def send_reading(pressure, temperature, humidity, wind_speed, wind_direction, precipitation):
    reading_data = {
        'pressure': pressure,
        'temperature': temperature,
        'humidity': humidity,
        'wind_speed': wind_speed,
        'wind_direction': wind_direction,
        'precipitation': precipitation
    }
    logger.debug(f"data about to be sent in post request:   {reading_data}")


    payload = {"secret_key": SECRET_KEY, "new_data_item": reading_data}

    try:
        request = requests.post(SERVER_URL, json=payload)
        assert request.status_code == 200, f"Status code was not 200 success but was  {request.status_code}"
    except Exception as e:
        print("ERROR:")
        print(e)
        try:
            if request.status_code == 404:
                logger.critical('404 page not found')
            if request.status_code == 401:
                logger.critical('401 authentication failed, check key')
            if request.status_code == 500:
                logger.critical('500 internal server error, perhaps flask server has crashed')
        except UnboundLocalError:
            print("request variable not defined, error occurred before this")
    else:
        logger.debug("status code 200, data sent successfully")

if __name__ == '__main__':
    send_reading(
        pressure=uniform(1010, 1050),
        temperature=uniform(0, 40),
        humidity=uniform(40, 90),
        wind_speed=uniform(0, 30),
        wind_direction=uniform(0, 360),
        precipitation=uniform(0, 2),
    )
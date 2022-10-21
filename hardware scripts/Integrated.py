#IMPORTANT: Do not forget to update crontab if make a new Integreated.py version with... sudo crontab -e

#Import modules
import requests
from datetime import datetime
import json
import random
import logging
import os

#Import files to use
import Ann as Ann
import BME as BME
import Rain as Rain
import Wind as Wind
import logger as logger_module #For logging

#Logger Setup
#Logger for sensor readings
logger_module.setup_logger(os.path.basename(__file__) + " - Sensor Logger")
loggerSens = logging.getLogger(os.path.basename(__file__) + " - Sensor Logger")

logger_module.setup_logger(os.path.basename(__file__) + " - Backend Logger")
loggerBack = logging.getLogger(os.path.basename(__file__) + " - Backend Logger")

#Server setup
SERVER_URL = 'http://172.20.47.242:80/data' # Change to match /data endpoint of URL

#Reads secret key
with open("secret_key.key", "r") as file:
	SECRET_KEY = file.read()

#Confirm setup of server was successful
output_safe_secret_key = SECRET_KEY[:4] + "*"*(len(SECRET_KEY)-8) + SECRET_KEY[-4:]
loggerBack.info(f"using secret key:   {output_safe_secret_key}")
loggerBack.info(f"using server url:   {SERVER_URL}")

#Ensures all values have been calculated as floats (i.e. all valid) - if not defaults to 0
def floatCheck(checkMe):
	try:
		checkMe = float(checkMe)
	except ValueError:
		loggerSens.error('   {checkMe}   has incorrect form. ')
		checkMe = 0
	return checkMe
		
#Sends readings to server
def send_reading(pressure, temperature, humidity, wind_speed, wind_direction, precipitation):
	#Creates dictionary of all values to send
	readingData = {
		'pressure': pressure,
		'temperature': temperature,
		'humidity': humidity,
		'wind_speed': wind_speed,
		'wind_direction': wind_direction,
		'precipitation': precipitation
	}
	loggerBack.info(f"data about to be sent in post request:   {readingData}")

	payload = {"secret_key": SECRET_KEY, "new_data_item": readingData} 

	# Tries to send data to server
	try:
		request = requests.post(SERVER_URL, json=payload)
		assert request.status_code == 200, f"Status code was not 200 success but was  {request.status_code}"
	except Exception as e:
		print("ERROR:")
		print(e)

		#Tries to identify type of error
		try:
				if request.status_code == 404:
						loggerBack.critical('404 page not found')
				elif request.status_code == 401:
						loggerBack.critical('401 authentication failed, check key')
				elif request.status_code == 500:
						loggerBack.critical('500 internal server error, perhaps flask server has crashed')
		except:
				print("Request variable not defined. Error occurred before this. ")
		else:
				loggerBack.debug("Status code 200 - date sent successfully.")

#Takes readings - ensures they are integers
loggerSens.info(f"Taking rainfall reading...")
rainVol = Rain.main()
rainVol = floatCheck(rainVol)
loggerSens.info(f"Rainfall reading:   {rainVol}")

loggerSens.info(f"Taking wind speed reading...")
windSpeed = Ann.main()
windSpeed = floatCheck(windSpeed)
loggerSens.info(f"Wind speed reading:   {rainVol}")

loggerSens.info(f"Taking BME readings...")
temp, press, humid = BME.main()
temp = floatCheck(temp)
press = floatCheck(press)
humid = floatCheck(humid)

#Checks BME reading via pressure
if press < 900:
	loggerSens.error('Pressure value <900 - check BME')
else:
	loggerSens.info(f"Temperature reading:   {temp}")
	loggerSens.info(f"Pressure reading:   {press}")
	loggerSens.info(f"Relative Humidity reading:   {humid}")

loggerSens.info(f"Taking Wind Direction readings...")
windD = Wind.get_value()
windD = floatCheck(windD)
loggerSens.info(f"Wind Direction reading:   {humid}")

#Send values to store in server
send_reading(press, temp, humid, windSpeed, windD, rainVol)

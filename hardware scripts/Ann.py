from gpiozero import Button
import math
import time

wind_speed_sensor = Button(21) # GPIO Pin annemometer is connected to
wind_count = 0 # Sets current number of spins to 0

def spin(): # Runs on each 'spin' of anemometer
	global wind_count
	wind_count = wind_count + 1 # Incremenets number of spins by 1

def calculateSpeed(wind_interval):
	global wind_count

	# Sets constants of anemometer
	radius_cm = 9.0

	# Sets conversion details
	cm_in_km = 100000
	secs_in_hr = 3600
	km_per_mile = 1.60934
	kmph_per_knot = 1.852

	anem_factor = 1.18 #Due to energy being lost when blades turn - differenent annemometer will have different no. 

	circumference_cm = (2 * math.pi) * radius_cm # Calculates distance travelled by blades on 1 rotation
	rotations = wind_count / 2.0 # Wind count counts twice per actual rotation
	
	# Calculates total distance travelled by blades
	dist_cm = circumference_cm * rotations 
	dist_km = (circumference_cm * rotations) / cm_in_km
	
	# Calculates wind speed from this
   # cm_per_sec = (dist_cm / wind_interval) * anem_factor
	km_per_sec = (dist_km / wind_interval)
	km_per_hour = (km_per_sec * secs_in_hr) * anem_factor
	miles_per_hour = km_per_hour / km_per_mile
   # knots = km_per_hour / kmph_per_knot

	reset_wind() # Resets wind count to 0

	return miles_per_hour

def reset_wind():
	global wind_count
	wind_count = 0 # Resets total wind count to 0

def wind_manager():
	wind_gap = 5 #Gap between calculating speeds
	startTime = time.time() # Records current time

	while time.time() - startTime < wind_gap: # Loops for given time period
			wind_speed_sensor.when_pressed = spin # Records spin
	wind_speed_result = calculateSpeed(wind_gap) # Calculates wind speed

	return wind_speed_result

def main(): # Takes given no. of readings and finds average
	noReadings = 10 # Determines number of individual readings to take (and average out) to get wind speed result
	total = 0 # Running total annenometer rotations
	for i in range(noReadings):
		total = total + wind_manager() # Appends average wind speed of this iteration
	average = total / noReadings # Calculates average of readings

	return average

print(main())

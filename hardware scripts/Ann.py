#Imports required modules
from gpiozero import Button
import math
import time

wind_speed_sensor = Button(21) #GPIO pin annemometer is connected to
wind_count = 0

#Increments spin counter
def spin():
    global wind_count
    wind_count = wind_count + 1

def calculateSpeed(wind_interval):
    global wind_count

    #Known constants
    radius_cm = 9.0
    cm_in_km = 100000
    secs_in_hr = 3600
    km_per_mile = 1.60934
    #kmph_per_knot = 1.852 - Not used
    anem_factor = 1.18 #Due to energy being lost when blades turn - differenent annemometer will have different no. 

    # Performs calculations (circle circumference, etc) to calculate wind speed
    circumference_cm = (2 * math.pi) * radius_cm
    rotations = wind_count / 2.0
    
    #dist_cm = circumference_cm * rotations - Not used
    dist_km = (circumference_cm * rotations) / cm_in_km
    
   # cm_per_sec = (dist_cm / wind_interval) * anem_factor - Not used
    km_per_sec = (dist_km / wind_interval)
    km_per_hour = (km_per_sec * secs_in_hr) * anem_factor
    miles_per_hour = km_per_hour / km_per_mile
   # knots = km_per_hour / kmph_per_knot - Not used

    return miles_per_hour

def reset_wind():
    global wind_count
    wind_count = 0

def main(): # SP_NOTE - Not convinced by this - think this has changed on the RP but not on GitHub
    wind_gap = 30 #Gap between calculating speeds
    startTime = time.time()

    #Waits for required period of time to ellapse
    while time.time() - startTime < wind_gap:
            wind_speed_sensor.when_pressed = spin
    
    #Uses number of record spinds to calculate wind speed
    wind_speed_result = calculateSpeed(wind_gap)

    return wind_speed_result

from gpiozero import Button
import math
import time

wind_speed_sensor = Button(21)
wind_count = 0

def spin():
    global wind_count
    wind_count = wind_count + 1

def calculateSpeed(wind_interval):
    global wind_count

    radius_cm = 9.0
    
    cm_in_km = 100000
    
    secs_in_hr = 3600

    km_per_mile = 1.60934
    kmph_per_knot = 1.852

    anem_factor = 1.18 #Due to energy being lost when blades turn - differenent annemometer will have different no. 

    circumference_cm = (2 * math.pi) * radius_cm
    rotations = wind_count / 2.0
    
    dist_cm = circumference_cm * rotations
    dist_km = (circumference_cm * rotations) / cm_in_km
    
   # cm_per_sec = (dist_cm / wind_interval) * anem_factor
    km_per_sec = (dist_km / wind_interval)
    km_per_hour = (km_per_sec * secs_in_hr) * anem_factor
    miles_per_hour = km_per_hour / km_per_mile
   # knots = km_per_hour / kmph_per_knot

    return miles_per_hour

def reset_wind():
    global wind_count
    wind_count = 0

def main():
    wind_gap = 30 #Gap between calculating speeds
    startTime = time.time()

    while time.time() - startTime < wind_gap:
            wind_speed_sensor.when_pressed = spin
    wind_speed_result = calculateSpeed(wind_gap)

    return wind_speed_result

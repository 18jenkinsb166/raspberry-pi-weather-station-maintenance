from gpiozero import MCP3008
import time
import math as maths

def get_value():
    OFFSET = 67.5
    adc = MCP3008(channel=0)
    #print("Test: ", adc.value) #test outputting 1 raw reading
    count = 0
    volts = {0.4: 0.0,
             1.4: 22.5,
             1.2: 45.0,
             2.8: 67.5,
             2.7: 90.0,
             2.9: 112.5,
             2.2: 135.0,
             2.5: 157.5,
             1.8: 180.0,
             2.0: 202.5,
             0.7: 225.0,
             0.8: 247.5,
             0.1: 270.0,
             0.3: 292.5,
             0.2: 315.0,
             0.6: 337.5}

    value = adc.value*3.3 #Multiply by 3.3kOhm due to range of potential divider circuit
    wind = round(value, 1)
    if not wind in volts:
         #print("Unknown Value: " + str(wind))
         data = 0.0 #if unknown just sends as 0 or North 
    else:
         data = (volts[wind] + OFFSET) % 360
        #print(volts[wind]) #also used for testing
    return data

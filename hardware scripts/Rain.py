from gpiozero import Button
import datetime
import time

#Records Bucket Tip
def bucketTipped():
        #Formats current date and time as DD/MM/YY, HH:MM:SS
        dtNow = datetime.datetime.now()
        appendMe = dtNow.strftime("%d/%m/%Y, %H:%M:%S") 
        
        rainFile = open("rainTimesAll.txt", "a") #Opens file to record all rain tips in
        rainFile.write(appendMe + "\n") #Appends curent time to rain tips file
        rainFile.close()

#Removes bucket tips from previous day
def cleanRainfall(dateNow):
        #Opens the file containing all times of tips, and reads each line
	rainFile = open("rainTimesAll.txt", "r")
	rainTimes = rainFile.readlines()
	rainFile.close()

        #Checks a tip exists
	if len(rainTimes) > 0:
                flag = True
                while flag == True:
                        try:
                                date = (rainTimes[0])[0:9] #Takes date from each record
                        except IndexError: #No more dates in file
                                return 0
                        else:
                                if date != dateNow: #Checks date is not current date
                                        rainTimes.remove(rainTimes[0])
                                else:
                                        flag = False #Breaks loop
                                        
                #Write all valid times to text file, overwriting previously stored tip times
                recentRainFile = open("rainTimesAll.txt", "w")
                for times in rainTimes:
                        recentRainFile.write(times)
                recentRainFile.close()
                
        return len(rainTimes) #Retrns number of tips recorded

#Returns volume of rain in given period of time
def returnTips():
        timeNow = datetime.datetime.now()
        dtForm = timeNow.strftime("%d/%m/%Y, %H:%M:%S") #Formats current date and time as DD/MM/YY, HH:MM:SS
        
        bucketTips = cleanRainfall(dtForm[0:9]) #Returns number of tips today
        bucket_size = 0.2794 #Volume of water needed to tip rain gague

        return bucketTips * bucket_size #Returns volume of rain collected in given period

#Wait for and record bucket tips
def main():
	rain_sensor = Button(6) #GPIO pin guage is connected to
	startTime = time.time()

	while time.time() - startTime < ((5 * 60) - 52): #Change RHS for time between readings - minus 52 to account for time taking other readings
                rain_sensor.when_pressed = bucketTipped
        volumeCollected = returnTips()
	return volumeCollected

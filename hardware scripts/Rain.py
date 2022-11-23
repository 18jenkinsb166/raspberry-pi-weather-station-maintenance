from gpiozero import Button
from datetime import datetime, timedelta
from time import time.sleep()
# import csv to store an array of timestamps of bucket tip events
import csv
from typing import Iterable

# removed comma
DATE_FORMAT = "%d/%m/%Y %H:%M:%S"
# Volume of water needed to tip rain gague
BUCKET_SIZE = 0.2794

#Records Bucket Tip
def bucketTipped():
	# get current time stamp
	now_timestamp: str = datetime.now().strftime(DATE_FORMAT)

	# append it as new row to csv
	with open("rain_tip_times.csv", "a", newline="") as csv_file:
		csv_writer = csv.writer(csv_file, delimiter=",")
		csv_writer.writerow([now_timestamp])

# tell if 2 time stamps are less than
def time_difference_less_than_day(now: datetime, then: datetime):
	difference: timedelta = now - then
	return difference.days < 1

#Returns volume of rain in given period of time
def returnTips():  # sourcery skip: inline-immediately-yielded-variable
	now: datetime = datetime.now()

	# function returns a generator object which iterates to yield data times form csv
	def generate_tip_timestamps():
		# read the csb
		with open("rain_tip_times.csv", "r") as csv_file:
			# csv_reader is an iterable of rows
			csv_reader = csv.reader(csv_file, delimiter=',')
			# for each row
			for row in csv_reader:
				# get and yield datetime
				time_stamp: str = row[0]
				time: datetime = datetime.strptime(time_stamp, DATE_FORMAT)
				yield time

	# get iterable of all tips
	tips: Iterable[datetime] = generate_tip_timestamps()

	# filter where function true
	# used to remove tips of more than a day old
	tips_in_last_day: list[datetime] = list(filter(
		lambda then: time_difference_less_than_day(now, then),
		tips
	))
	# count tips in last 24 hours
	num_tips_in_last_day: int = len(tips_in_last_day)
	# print(list(tips_in_last_day))

	# format filtered data into rows to overwrite csv file
	# turn each tip into a single element array to show a row

	rows: list[str] = list(map(
		lambda tip: [tip.strftime(DATE_FORMAT)],
		tips_in_last_day
	))

	# overwrite csv with new filtered tips to prevent old tips accumulating
	with open("rain_tip_times.csv", "w", newline="") as csv_file:
		csv_writer = csv.writer(csv_file, delimiter=",")
		csv_writer.writerows(rows)

	# calculate total volume in 24 hours
	total_volume = num_tips_in_last_day * BUCKET_SIZE
	return total_volume


#Wait for and record bucket tips
def main():
	# configure rain sensor with tip handler method
	rain_sensor = Button(6) #GPIO pin guage is connected to
	rain_sensor.when_pressed = bucketTipped

	startTime = time()
	# wait until time elapsed
	while time() - startTime < ((5 * 60) - 52): #Change RHS for time between readings - minus 52 to account for time taking other readings
		time.sleep(10)
	return returnTips()
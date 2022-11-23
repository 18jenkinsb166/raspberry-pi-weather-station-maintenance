from gpiozero import Button
from datetime import datetime, timedelta
import time
# import csv to store an array of timestamps of bucket tip events
import csv
from typing import Iterable

# removed comma
DATE_FORMAT = "%d/%m/%Y %H:%M:%S"
# Volume of water needed to tip rain gague
BUCKET_SIZE = 0.2794

#Records Bucket Tip
def bucketTipped():
	now_timestamp: str = datetime.now().strftime(DATE_FORMAT)
	with open("rain_tip_times.csv", "a", newline="") as csv_file:
		csv_writer = csv.writer(csv_file, delimiter=",")
		csv_writer.writerow([now_timestamp])


def time_difference_less_than_day(now: datetime, then: datetime):
	difference: timedelta = now - then
	return difference.days < 1

#Returns volume of rain in given period of time
def returnTips():  # sourcery skip: inline-immediately-yielded-variable
	now: datetime = datetime.now()

	def generate_tip_timestamps():
		with open("rain_tip_times.csv", "r") as csv_file:
			# csv_reader is an iterable of rows
			csv_reader = csv.reader(csv_file, delimiter=',')
			for row in csv_reader:
				time_stamp: str = row[0]
				time: datetime = datetime.strptime(time_stamp, DATE_FORMAT)
				yield time

	tips: Iterable[datetime] = generate_tip_timestamps()
	# filter where function true
	tips_in_last_day: list[datetime] = list(filter(
		lambda then: time_difference_less_than_day(now, then),
		tips
	))
	num_tips_in_last_day: int = len(tips_in_last_day)
	# print(list(tips_in_last_day))
	# turn each tip into a single element array to show a row
	rows: list[str] = list(map(
		lambda tip: [tip.strftime(DATE_FORMAT)],
		tips_in_last_day
	))

	# overwrite csv with new filtered tips
	with open("rain_tip_times.csv", "w", newline="") as csv_file:
		csv_writer = csv.writer(csv_file, delimiter=",")
		csv_writer.writerows(rows)

	total_volume = num_tips_in_last_day * BUCKET_SIZE
	return total_volume


#Wait for and record bucket tips
def main():
	rain_sensor = Button(6) #GPIO pin guage is connected to
	startTime = time.time()

	while time.time() - startTime < ((5 * 60) - 52): #Change RHS for time between readings - minus 52 to account for time taking other readings
		rain_sensor.when_pressed = bucketTipped
	return returnTips()
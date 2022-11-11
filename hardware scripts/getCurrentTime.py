# This file will write the current time (after every time the Integrated.py file runs) - overwriting any previous values.
# This will allow you to see whether, when the server goes offline, this is due to a network issue (i.e. when the RP is back
# online the time is the current time - or there or there abouts) or if this is due to an electrical issue - in which case
# the time will not be the same/similar.

# Importing modules
import datetime

# Gets current date/time
dtNow = datetime.datetime.now()

# Opens and writes to file
timeFile = open("lastUsed.txt", "w")
timeFile.write(str(dtNow))

# Closes file
timeFile.close
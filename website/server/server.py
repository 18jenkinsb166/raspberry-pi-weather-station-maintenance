# docs:
# https://marshmallow-sqlalchemy.readthedocs.io/en/latest/

# imports
# sourcery skip: avoid-builtin-shadow
import hashlib
import json
import os
from datetime import datetime

import flask
import sqlalchemy as sqla
from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

# local import, this is a local file
try:
    from server import logger as logger_module
except ImportError:
    import logger as logger_module

# setup logger
# an object to keep track of what is going on in a log file
basedir = os.getcwd()
LOG_DIR =  os.path.join(basedir, 'server', 'server.log')
lgr = logger_module.setup_logger('server', LOG_DIR)

# constants:
lgr.info('setup: defining constants')
PORT = 5000
DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
LAST_COMMITTED_TIMESTAMP = None
# can be changed, affects how many days of data are displayed on the webiste
LAST_X_DAYS = 21

# read key file for hashed key  
lgr.info('setup: reading hashed key file')
with open('./server/hashed_key.key', 'r') as file:
    SECRET_KEY_HASH = file.read()

lgr.info('setup: reading image path lookup file')
# image paths lookup
with open("./images/images.json", "r") as file:
    image_file_names = json.loads(file.read())


lgr.info("setting up flask app")
# setup app
app = flask.Flask(
    __name__,
    static_folder=os.path.join(basedir, 'static'),
    template_folder=os.path.join(basedir, 'templates'),
)
# trying to prevent issues with caching of old files
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


lgr.info("setting up sqlalchemy engine")
# setup sql engine:
# https://stackoverflow.com/questions/48218065/programmingerror-sqlite-objects-created-in-a-thread-can-only-be-used-in-that-sa
# this object is the connection to the database. 
engine = sqla.create_engine(
    'sqlite:///' + os.path.join(basedir, 'server', 'database.db'),
    # "sqlite:///:memory:",
    echo=True,
    future=True,
    connect_args={'check_same_thread': False}
)

# create more objects (boilerplate code) to access database
session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()

lgr.info('defining reading class to represent a row in the readings table')
# setup sqlalchemy row obj
# this object can be directly read and written to the database
class Reading(Base):
    """Table for uncalibrated readings"""
    __tablename__ = 'Readings'
    # data types for each column
    primary_key = sqla.Column(sqla.Integer, primary_key=True)
    timestamp = sqla.Column(sqla.DateTime())
    # background_img = sqla.Column(sqla.VARCHAR(100))

    pressure = sqla.Column(sqla.Float())
    temperature = sqla.Column(sqla.Float())
    humidity = sqla.Column(sqla.Float())
    wind_speed = sqla.Column(sqla.Float())
    wind_direction = sqla.Column(sqla.Float())
    precipitation = sqla.Column(sqla.Float())

    # init function determines timestamp and adds arguments as parameters
    def __init__(self, pressure, temperature, humidity, wind_speed, wind_direction, precipitation):
        self.pressure = pressure
        self.temperature = temperature
        self.humidity = humidity
        self.wind_speed = wind_speed
        self.wind_direction = wind_direction
        self.precipitation = precipitation
        self.timestamp = datetime.now()

    # used to represent the object as a string for debugging
    def __repr__(self):
        return f"<Reading_Uncalibrated(primary_key={self.primary_key}, timestamp={self.timestamp})>"
        # return f"<Reading(timestamp={self.timestamp})>"


lgr.info("creating all tables if not already exists")
# create table in SQL database
Base.metadata.create_all(engine, checkfirst=True)

lgr.info('define sql index on timestamp to improve read times by timestamp')
# index allows for faster lookup of rows by index
sqla.schema.Index("timestamp_index", Reading.timestamp)

# setup marshmallow schema
# blueprint for serializing and deserializing the reading row object
lgr.info('defining schema for reading to allow for validation and serialization')
class Reading_Schema(SQLAlchemySchema):
    class Meta:
        model = Reading
        # to and from relationship between json and row object
        load_instance = True  # Optional: deserialize to model instances
        # tell schema the timestamp format
        datetimeformat = DATE_TIME_FORMAT

    # primary_key = auto_field(dump_only=True)
    # not needed to load json into new row object
    timestamp = auto_field(dump_only=True)
    
    # required sensor data
    pressure = auto_field(required=True)
    temperature = auto_field(required=True)
    humidity = auto_field(required=True)
    wind_speed = auto_field(required=True)
    wind_direction = auto_field(required=True)
    precipitation = auto_field(required=True)


lgr.info('setting up instances of the schema for serializing readings')
# schema objs used in serialization and desalination 
reading_schema = Reading_Schema()
reading_schema_many = Reading_Schema(many=True)



# functions
lgr.info('defining utility functions')

# this function is a decorator. It takes another function as an argument and returns a new function with augmented functionality
def print_dec(function):
    name = function.__name__
    def wrapper(*args, **kwargs):
        # add the function call to the log file
        lgr.debug(f"Beginning execution of function:   {name}")
        result = function(*args, **kwargs)
        lgr.debug(f"Finished execution of function:   {name}")
        out = str(result).replace("\n", " ").replace("\t", " ")[:200]
        lgr.debug(f" function {name} returned:   {out}")
        return result
    wrapper.__name__ = name
    return wrapper

# also a decorator. Calls the function repeatedly on the last result for multiple rounds of hashing
def repeat_decorator_factory(repeats:int):
    """works where there is one input and a process can be repeated by running again on previous output"""
    def decorator(function):
        name = function.__name__
        def wrapper(arg):
            result = arg
            for _ in range(repeats):
                result = function(result)
            return result
        wrapper.__name__ = name
        return wrapper
    return decorator

# function returns a hexadecimal string for the SHA256 hash of an object
@print_dec
@repeat_decorator_factory(10**3)
def hash(plain_txt):
    """one way hash using sha256"""
    hash_ = hashlib.sha256()
    hash_.update(plain_txt.encode())
    return hash_.hexdigest()

# this function logic determines what the weather is approximately
@print_dec
def determine_background_image(temperature, precipitation):
    # will check time stamp and be true if between 11pm and 5am
    hour = datetime.now().hour
    is_night = hour < 5 or hour >= 23
    is_raining = precipitation > 1

    if is_night:
        return "night"
    if is_raining:
        return "rain"
    if temperature >= 20:
        return "sunny"
    if temperature <= 10:
        return "cold"
    # default mild
    return "mild"


lgr.info("defining functions to handle routes / endpoints")
# setup methods to handle routes


# decorator removed as I want an un-augmented coppy of the function to call as well as trying it to the endpoint 
# @app.route('/data', methods=['GET'])
@print_dec
def get_data():
    # datediff: https://stackoverflow.com/questions/36571706/python-sqlalchemy-filter-by-datediff-of-months
    # define query to get all the reading objects that meet the time period requirement
    # sort by timestamp
    stmt = sqla.select(Reading)\
        .filter(
            sqla.func.julianday() - sqla.func.julianday(Reading.timestamp) <= LAST_X_DAYS
        )\
        .order_by(
            Reading.timestamp
        )
    # execute query to get reading objects
    all_readings = list(session.scalars(stmt))
    # this changes the order so the most recent item is at the top
    # all_readings.reverse()

    # convert the readings to dictionary and then to json
    serialised_readings: dict = reading_schema_many.dump(all_readings)
    return flask.jsonify(serialised_readings)


# handle pi sending new data
@print_dec
# @app.route('/data', methods=['POST'])
def post_data():
    # get the data attached to the post request
    data_header = flask.request.json
    secret_key = data_header["secret_key"]
    new_reading_data: dict = data_header["new_data_item"]
    # print(new_reading_data)
    
    # abort if the given key is invalid
    if hash(secret_key) != SECRET_KEY_HASH:
        # print("secret key wrong for post request")
        flask.abort(401)

    # convert dictionary data to a reading object
    new_reading_obj = reading_schema.load(new_reading_data, session=session)
    # print(repr(new_reading_obj))
    
    # update last committed timestamp global (avoids excess DB queries)
    global LAST_COMMITTED_TIMESTAMP
    LAST_COMMITTED_TIMESTAMP = new_reading_obj.timestamp

    # ass to the session this reading row and then commit the changes to the database
    session.add(new_reading_obj)
    session.commit()
    
    # return the new reading object as a redundant standard
    return flask.jsonify(
        reading_schema.dumps(new_reading_obj)
    )

# these utility function are exclusive to the developer who has the secret key
@print_dec
def delete_utility():
    # get secret key form header data and then abort if wrong key
    data_header = flask.request.json
    secret_key = data_header["secret_key"]

    if hash(secret_key) != SECRET_KEY_HASH:
        flask.abort(401)

    # delete all readings from the database
    session.query(Reading).delete()
    session.commit()

    return "Database cleared"

@print_dec
# deletes all entries before a certain date
def delete_before_date_utility():
    # ensure valid secret key
    data_header = flask.request.json
    secret_key = data_header["secret_key"]
    date: str = data_header["date"]

    if hash(secret_key) != SECRET_KEY_HASH:
        flask.abort(401)
    
    # convert given date to datetime
    date: datetime = datetime.strptime(date, DATE_TIME_FORMAT)

    # get all readings before this date and then delete them
    session\
        .query(Reading)\
        .where(
            Reading.timestamp <= date
        )\
        .delete()
    session.commit()

    return "Database cleared"


@print_dec
# function to give the servers log file
def server_log_utility():
    # check key
    data_header = flask.request.json
    secret_key = data_header["secret_key"]
    
    if hash(secret_key) != SECRET_KEY_HASH:
        # print("secret key wrong for post request")
        flask.abort(401)
    
    # sent log file
    return flask.send_file(
        LOG_DIR
    )


@print_dec
# loads many weather data items into DB
def load_many_utility():
    # get data from header
    data_header = flask.request.json
    secret_key = data_header["secret_key"]
    new_data_items = data_header["new_data_items"]
    
    # check secret key
    if hash(secret_key) != SECRET_KEY_HASH:
        # print("secret key wrong for post request")
        flask.abort(401)
    
    # use schema to deserialize
    new_reading_objs = reading_schema_many.load(new_data_items, session=session)
    # print(repr(new_reading_obj))
    
    # update last committed
    global LAST_COMMITTED_TIMESTAMP
    LAST_COMMITTED_TIMESTAMP = None

    # bulk save many objects
    session.bulk_save_objects(new_reading_objs)
    session.commit()
    
    # return the new objects as it default practice
    return flask.jsonify(
        reading_schema_many.dumps(new_reading_objs)
    )


@print_dec
# provides the whole contents of the DB
# could be used for an external backup along with the load many function
def dump_all_utility():
    # check key
    data_header = flask.request.json
    secret_key = data_header["secret_key"]
    
    if hash(secret_key) != SECRET_KEY_HASH:
        # print("secret key wrong for post request")
        flask.abort(401)
    
    # select all query
    stmt = sqla.select(Reading)
    # execute query to get list of readings
    all_readings = list(session.scalars(stmt))
    # this changes the order so the most recent item is at the top
    # all_readings.reverse()
    # serialised the data to return it as JSON 
    serialised_readings: dict = reading_schema_many.dump(all_readings)
    return flask.jsonify(serialised_readings)


# @app.route("/get_data")
# def redirect_to_data():
#     """was an old endpoint replaced by data"""
#     return flask.url_for(flask.url_for("get_data"))


# returns the html for the main page
# @app.route("/", methods=['GET'])
@print_dec
def index():
    # return "HTML HERE"
    # return flask.redirect(flask.url_for("get_readings"))
    return flask.render_template("index.html")


# gives the image file corresponding to a name
# @app.route("/images/<name>", methods=["GET"])
@print_dec
def give_photo(name):
    # print(name)
    try:
        # assertion error if name not in list or file not found
        assert name in image_file_names.keys(), "image name not in available names"
        full_file_path = os.path.join(basedir, 'images', image_file_names[name])
        print(full_file_path)
        assert os.path.exists(full_file_path), "file path to image doesn't exist"
    except AssertionError:
        # print(e)
        # if not found abort 404
        flask.abort(404)
    else:
        # if found send the image file
        return flask.send_file(full_file_path, mimetype='image/gif')


# @app.route("/background_image", methods=["GET"])
@print_dec
# gives the background image based on the last reading
def background_image():
    # get last reading based on timestamp
    if LAST_COMMITTED_TIMESTAMP is not None:
        reading = list(session.scalars(
            sqla.select(Reading)
            .where(Reading.timestamp == LAST_COMMITTED_TIMESTAMP)
        ))[0]
    # if just restarted then query all, sort and pick most recent
    else:
        reading = list(session.scalars(
            sqla.select(Reading)
            .order_by(Reading.timestamp)
        ))[-1]

    # determine the appropriate image name based on the weather conditions
    image_name = determine_background_image(
        temperature=reading.temperature,
        precipitation=reading.precipitation
    )
    # print(f"determine_background_image called with ({reading.temperature}, {reading.precipitation}) returned {image_name}")
    # return the appropriate file
    return give_photo(image_name)
    # return give_photo('sunny')
    # return flask.send_file("test image.png", mimetype='image/gif')


# @app.route("/csv_data", methods=["GET"])
@print_dec
# return all the data as a CSV file 
def csv_data():
    # convert an array of records to a series of CSV rows
    def dicts_to_csv_lines(records):
        # format a row of items by adding delimiter
        def format_row(row):
            return ",".join(
                map(
                    lambda e: str(e),
                    row
                )
            ) + ","
        # used to set order
        keys = "timestamp,humidity,precipitation,pressure,temperature,wind_direction,wind_speed".split(",")
        # for row in [records[0].keys()] + [r.values() for r in records]:
        yield format_row(keys)
        for record in records:
            yield format_row(record[key] for key in keys)

    # source: https://stackoverflow.com/questions/30024948/flask-download-a-csv-file-on-clicking-a-button
    # query all records
    query = sqla.select(Reading).order_by(Reading.timestamp)
    all_readings = list(session.scalars(query))
    # reverse so most recent at the top
    # all_readings.reverse()

    # dump to dictionary (serialize)
    serialised_readings: dict = reading_schema_many.dump(all_readings)

    # convert list of dictionaries to csv
    # would use csv library but i don't want to write to a local file
    # join CSV lines with a line break
    return flask.Response(
        "\n".join(
            dicts_to_csv_lines(serialised_readings)
        ),
        # metadata to make it appear as a file not just text
        mimetype="text/csv",
        headers={
            "Content-disposition": "attachment; filename=weather_data.csv",
        }
    )
    
# now tie the handlers to the endpoints
lgr.info("binding route handlers to respective route")
# decided to not use conventual decorators so that background image func can call give photo
app.route('/data', methods=['POST'])(post_data)
app.route('/data', methods=['GET'])(get_data)
app.route("/csv_data", methods=["GET"])(csv_data)
app.route("/images/<name>", methods=["GET"])(give_photo)
app.route("/background_image", methods=["GET"])(background_image)
app.route("/", methods=['GET'])(index)
app.route("/utility/delete", methods=["POST"])(delete_utility)
app.route('/utility/server_log', methods=['POST'])(server_log_utility)
app.route('/utility/load_many', methods=['POST'])(load_many_utility)
app.route('/utility/dump_all', methods=['POST'])(dump_all_utility)
app.route('/utility/delete_before_date', methods=['POST'])(delete_before_date_utility)

lgr.info('defining safe method for running app')
@print_dec
# runs app
def run_app():
    try:
        app.run(host='127.0.0.1', port=PORT, debug=True)
    # if keyboard interrupt given then database connection safely closed before shutdown 
    except KeyboardInterrupt:
        # print("closing database: ")
        session.close()
        engine.dispose()

# if file called directly run the app
# redundant as app.py and flask run used now
# if __name__ == '__main__':
#     lgr.info('running app')
#     run_app()

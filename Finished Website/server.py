# docs:
# https://marshmallow-sqlalchemy.readthedocs.io/en/latest/

# imports
# sourcery skip: avoid-builtin-shadow
import hashlib
import sqlalchemy as sqla
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field
import os
from datetime import datetime
import flask
import json

# local import
import logger as logger_module

# setup logger
lgr, log_dir = logger_module.setup_logger(os.path.basename(__file__))

# constants:
lgr.info('setup: defining constants')
PORT = 5000
DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
LAST_COMMITTED_TIMESTAMP = None

lgr.info('setup: reading hashed key file')
with open('./server/hashed_key.key', 'r') as file:
    SECRET_KEY_HASH = file.read()

lgr.info('setup: reading image path lookup file')
# image paths lookup
with open("./images/images.json", "r") as file:
    image_file_names = json.loads(file.read())




lgr.info("setting up flask app")
# basedir = os.path.abspath(os.path.dirname(__file__))
basedir = os.getcwd()

# setup app
app = flask.Flask(
    __name__,
    # static_url_path='',
    static_folder=os.path.join(basedir, 'static'),
    template_folder=os.path.join(basedir, 'templates'),
)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


lgr.info("setting up sqlalchemy engine")
# setup sql engine:
# https://stackoverflow.com/questions/48218065/programmingerror-sqlite-objects-created-in-a-thread-can-only-be-used-in-that-sa
engine = sqla.create_engine(
    'sqlite:///' + os.path.join(basedir, 'server', 'database.db'),
    # "sqlite:///:memory:",
    echo=True,
    future=True,
    connect_args={'check_same_thread': False}
)

session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()

lgr.info('defining reading class to represent a row in the readings table')
# setup sqlalchemy row obj
class Reading(Base):
    """Table for uncalibrated readings"""
    __tablename__ = 'Readings'
    primary_key = sqla.Column(sqla.Integer, primary_key=True)
    timestamp = sqla.Column(sqla.DateTime())
    # background_img = sqla.Column(sqla.VARCHAR(100))

    pressure = sqla.Column(sqla.Float())
    temperature = sqla.Column(sqla.Float())
    humidity = sqla.Column(sqla.Float())
    wind_speed = sqla.Column(sqla.Float())
    wind_direction = sqla.Column(sqla.Float())
    precipitation = sqla.Column(sqla.Float())

    def __init__(self, pressure, temperature, humidity, wind_speed, wind_direction, precipitation):
        self.pressure = pressure
        self.temperature = temperature
        self.humidity = humidity
        self.wind_speed = wind_speed
        self.wind_direction = wind_direction
        self.precipitation = precipitation
        self.timestamp = datetime.now()

    def __repr__(self):
        return f"<Reading_Uncalibrated(primary_key={self.primary_key}, timestamp={self.timestamp})>"
        # return f"<Reading(timestamp={self.timestamp})>"

lgr.info("creating all tables if not already exists")
# create all tables
Base.metadata.create_all(engine, checkfirst=True)

lgr.info('define sql index on timestamp to improve read times by timestamp')
sqla.schema.Index("timestamp_index", Reading.timestamp)

# setup marshmallow schema

lgr.info('defining schema for reading to allow for validation and serialization')
class Reading_Schema(SQLAlchemySchema):
    class Meta:
        model = Reading
        load_instance = True  # Optional: deserialize to model instances
        datetimeformat = DATE_TIME_FORMAT

    # primary_key = auto_field(dump_only=True)
    timestamp = auto_field(dump_only=True)
    pressure = auto_field(required=True)
    temperature = auto_field(required=True)
    humidity = auto_field(required=True)
    wind_speed = auto_field(required=True)
    wind_direction = auto_field(required=True)
    precipitation = auto_field(required=True)


lgr.info('setting up instances of the schema for serializing readings')
# schema objs used in serialization
reading_schema = Reading_Schema()
reading_schema_many = Reading_Schema(many=True)

# def delete_all_readings():
#     # all_readings = list(session.scalar(
#     #     sqla.select(Reading)
#     # ))
#     # session.delete_all(all_readings)
#     session.()
#     session.commit()

lgr.info('defining utility functions')
# functions
def hash(plain_txt):
    """one way hash using sha256"""
    hash_ = hashlib.sha256()
    hash_.update(plain_txt.encode())
    return hash_.hexdigest()


def determine_background_image(temperature, precipitation):
    # will check time stamp and be true if between 11pm and 5am
    hour = datetime.now().hour
    is_night = hour < 5 or hour >= 23
    # will make some comparrison with rain but I am not sure how to yet ask Sam
    is_raining = precipitation/hour > 1

    if is_raining:
        return "rain"
    # not sure of priority, should a hot night be night image or sunny image
    if is_night:
        return "night"
    if temperature >= 20:
        return "sunny"
    if temperature <= 14:
        return "cold"
    # default mild
    return "mild"


lgr.info("defining functions to handle routes / endpoints")
# setup methods to handle routes

# @app.route('/data', methods=['GET'])
def get_data():
    # datediff: https://stackoverflow.com/questions/36571706/python-sqlalchemy-filter-by-datediff-of-months
    stmt = sqla.select(Reading)\
        .filter(
            sqla.func.julianday() - sqla.func.julianday(Reading.timestamp) <= 14
        )\
        .order_by(
            Reading.timestamp
        )
    all_readings = list(session.scalars(stmt))
    # this changes the order so the most recent item is at the top
    # all_readings.reverse()
    serialised_readings: dict = reading_schema_many.dump(all_readings)
    return flask.jsonify(serialised_readings)

# @app.route('/data', methods=['POST'])
def post_data():
    data_header = flask.request.json

    secret_key = data_header["secret_key"]
    new_reading_data: dict = data_header["new_data_item"]
    # print(new_reading_data)

    if hash(secret_key) != SECRET_KEY_HASH:
        # print("secret key wrong for post request")
        flask.abort(401)

    new_reading_obj = reading_schema.load(new_reading_data, session=session)
    # print(repr(new_reading_obj))
    global LAST_COMMITTED_TIMESTAMP
    LAST_COMMITTED_TIMESTAMP = new_reading_obj.timestamp

    session.add(new_reading_obj)
    session.commit()
    return flask.jsonify(
        reading_schema.dumps(new_reading_obj)
    )
    # return "Thumbs up"

# @app.route('/server_logs', methods=['POST'])
# def get_log():
#     data_header = flask.request.json
#     secret_key = data_header["secret_key"]
    
#     if hash(secret_key) != SECRET_KEY_HASH:
#         # print("secret key wrong for post request")
#         flask.abort(401)
    
#     return flask.send_file()


# @app.route("/get_data")
# def redirect_to_data():
#     """was an old endpoint replaced by data"""
#     return flask.url_for(flask.url_for("get_data"))


# @app.route("/", methods=['GET'])
def index():
    # return "HTML HERE"
    # return flask.redirect(flask.url_for("get_readings"))
    return flask.render_template("index.html")


# @app.route("/images/<name>", methods=["GET"])
def give_photo(name):
    # print(name)
    try:
        assert name in image_file_names.keys(), "image name not in available names"
        full_file_path = os.path.join(basedir, 'images', image_file_names[name])
        print(full_file_path)
        assert os.path.exists(full_file_path), "file path to image doesn't exist"
    except AssertionError as e:
        # print(e)
        flask.abort(404)
    else:
        return flask.send_file(full_file_path, mimetype='image/gif')


# @app.route("/background_image", methods=["GET"])
def background_image():
    # get last reading
    if LAST_COMMITTED_TIMESTAMP is not None:
        reading = list(session.scalars(
            sqla.select(Reading)
            .where(Reading.timestamp == LAST_COMMITTED_TIMESTAMP)
        ))[0]
    else:
        reading = list(session.scalars(
            sqla.select(Reading)
            .order_by(Reading.timestamp)
        ))[-1]


    image_name = determine_background_image(
        temperature=reading.temperature,
        precipitation=reading.precipitation
    )
    # print(f"determine_background_image called with ({reading.temperature}, {reading.precipitation}) returned {image_name}")
    return give_photo(image_name)
    # return give_photo('sunny')
    # return flask.send_file("test image.png", mimetype='image/gif')


# @app.route("/csv_data", methods=["GET"])
def csv_data():
    def dicts_to_csv_lines(records):
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

    # dump to dictionary
    serialised_readings: dict = reading_schema_many.dump(all_readings)

    # convert list of dictionaries to csv
    # would use csv library but i don't want to write to a local file
    return flask.Response(
        "\n".join(
            dicts_to_csv_lines(serialised_readings)
        ),
        mimetype="text/csv",
        headers={
            "Content-disposition": "attachment; filename=weather_data.csv",
        }
    )
    

lgr.info("binding route handlers to respective route")
# decided to not use conventual decorators so that background image func can call give photo
app.route('/data', methods=['POST'])(post_data)
app.route('/data', methods=['GET'])(get_data)
app.route("/csv_data", methods=["GET"])(csv_data)
app.route("/images/<name>", methods=["GET"])(give_photo)
app.route("/background_image", methods=["GET"])(background_image)
app.route("/", methods=['GET'])(index)


lgr.info('defining safe method for running app')
def run_app():
    try:
        app.run(host='127.0.0.1', port=PORT, debug=True)
    except KeyboardInterrupt:
        # print("closing database: ")
        session.close()
        engine.dispose()


if __name__ == '__main__':
    lgr.info('running app')
    run_app()
    # delete_all_readings()

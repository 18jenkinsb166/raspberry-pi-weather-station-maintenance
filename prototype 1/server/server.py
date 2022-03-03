import flask
import json
import os
import hashlib
import logging

# local
import logger as logger_module

# setup logger
logger_module.setup_logger(os.path.basename(__file__))
logger = logging.getLogger(os.path.basename(__file__))

# would be sotred hashed
with open('hashed_key.key', 'r') as file:
    SECRET_KEY_HASH = file.read()
PORT = 5000
logger.info(f"fetched secret key hash: {SECRET_KEY_HASH}")
logger.info(f"Using port {PORT}")


def hash(plain_txt):
    """one way hash using sha256"""
    hash_ = hashlib.sha256()
    hash_.update(plain_txt.encode())
    return hash_.hexdigest()

# read data
def read_data():
    logger.info("reading all data from data store")
    with open("./data.json", "r") as file:
        # return json.load(file)
        result = file.read()
    logger.info(f"data store contents:  {result}")
    return result

# append data point
def append_data(data_item):
    logger.info(f"appending data item  {data_item} to data store")
    # read existing data
    with open("./data.json", "r") as file:
        data = json.load(file)
    # append new item
    data.append(data_item)
    # rewrite
    with open("./data.json", "w") as file:
        json.dump(data, file)



app = flask.Flask(
    __name__,
    static_folder= os.path.abspath('../website/static'),
    template_folder= os.path.abspath('../website/templates'),
)
logger.info("flask app object created")


@app.route("/data", methods=['GET', 'POST'])
def data():
    method = flask.request.method
    logger.info(f"Route data used with method  {method}")
    if method == "GET":
        logger.info("Responding to get request with all data")
        return read_data()

    if method == "POST":
        data_header  = flask.request.json
        secret_key = data_header["secret_key"]
        new_data_item = data_header["new_data_item"]

        logger.info(f"server received new data:  {new_data_item}")
        output_safe_secret_key = secret_key[:4] + "*"*(len(secret_key)-8) + secret_key[-4:]
        logger.info(f"server received new secret key:  {output_safe_secret_key}")
        hashed_key = hash(secret_key)
        logger.info(f"the hash of which is:  {hashed_key}")
        
        if hashed_key != SECRET_KEY_HASH:
            logger.warning("secret key wrong for post request, aborting with 401 authentication failed")
            flask.abort(401)
        else:
            logger.info("secret key correct after hash comparrison")
            append_data(new_data_item)
            logger.info("data item added to data store")
            logger.info("returning all data")
            return str(read_data())


@app.route("/")
def main():
    logger.info("Route main used with GET method")
    logger.info("Rendering and returning html home page")
    
    rendered = flask.render_template("index.html")
    # vue meant to also use {{ }} but it instead now uses {({})}
    rendered = rendered.replace("{({", "{{").replace("})}", "}}")
    return rendered


logger.info("all flask routes defined")
if __name__ == "__main__":
    logger.info("running flask app")
    app.run(host='127.0.0.1', port=PORT)

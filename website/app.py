# This file is part of the way to run the project. It contains no logic

from server import server

FLASK_APP = server.app

if __name__ == '__main__':
    print("http://127.0.0.1:5000/")
    FLASK_APP.run(host='127.0.0.1', port=5000)

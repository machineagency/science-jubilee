import os

# from picamera2 import Picamera2
import time

from flask import Flask, send_file, send_from_directory

scratch_fp = "./"


def create_app():

    app = Flask(__name__)
    from picamera2 import Picamera2

    camera = Picamera2()

    @app.route("/image", methods=("GET", "POST"))
    def image():
        """
        Take an image and return it over the function
        """
        time.sleep(2)
        camera.start_and_capture_file(scratch_fp + "capture.jpg")

        return send_file("../capture.jpg")  # , as_attachement=True)

    return app

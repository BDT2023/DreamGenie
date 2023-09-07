import sys
import threading
import time
import tkinter as tk
import wave
from tkinter import filedialog, messagebox

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import requests
import io
from io import BytesIO
import os
import datetime

sys.path.append("../Scene_Analyzer")
sys.path.append("../Image_Generation")
sys.path.append("../Utils")
import os
os.chdir(os.path.dirname(__file__))

os.chdir(
    f"{os.path.dirname(os.path.realpath(__file__))}"
)  # Change directory to current file location  ')")
cwd = os.getcwd()
print(cwd)
import string

from gpt_call import call_openai
from send_prompt import send_to_sd
from utils import get_service_urls

IS_TEST = True

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")

# Global variables
progress = 0
scenes_list = []
current_scene_index = 0
URLS = get_service_urls()


@app.route("/")
def index():
    print(f"Current working directory in main route: {os.getcwd()}")
    return render_template("index.html")


@socketio.on("user_input")
def handle_user_input(input_data):
    app.log_info(input_data)
    print(input_data)
    global progress, scenes_list, current_scene_index

    # Reset global variables
    progress = 0
    scenes_list = []
    current_scene_index = 0

    # Start processing the input
    socketio.start_background_task(process_input, input_data)


@socketio.on("get_progress")
def handle_get_progress():
    emit("progress", progress)


@socketio.on("get_scene")
def handle_get_scene():
    global scenes_list, current_scene_index

    if current_scene_index < len(scenes_list):
        scene = scenes_list[current_scene_index]
        current_scene_index += 1
        emit("scene", scene)
    else:
        emit("no_more_scenes")


@socketio.on("audio")
def process_audio(audioBlob):
    app.logger.info("Audio received")

    def send_request(audio_data):
        url = URLS["whisper"] + "/whisper"

        # Wraps the audio data in a BytesIO object to mimic a file
        audio_file = BytesIO(audio_data)
        audio_file.name = "audio.wav"

        # The 'files' parameter for 'requests.post' should be a dictionary or a list of tuples
        files = {"file": audio_file}

        response = requests.post(url, files=files, auth=("bdt", "12xmnxqgkpzj9cjb"))
        result = response.json()["results"][0]["transcript"]
        print(result)
        app.logger.info(result)
        socketio.emit("audio_result", result)
        return result

    t = threading.Thread(target=send_request, args=(audioBlob,))
    t.start()


def process_input(input_data):
    global progress, scenes_list

    # Update progress
    progress = 10
    socketio.emit("progress", progress)

    # Call OpenAI GPT-3 to separate scenes
    scenes_list = call_openai(input_data, test=IS_TEST)

    # Update progress
    progress = 100
    socketio.emit("progress", progress)

    # Get today's date
    today = datetime.date.today()

    # Generate images for scenes
    for scene in scenes_list:
        # Update progress for each scene
        progress = 0
        socketio.emit("progress", progress)

        # Generate image for scene
        image_path = send_to_sd(scene)

        # Update progress
        progress = 100
        socketio.emit("progress", progress)

        # Display the image to the user
        # Extract only the part of the path from the 'static' directory onwards
        relative_image_path = os.path.join('static', today.isoformat(), os.path.basename(image_path))
        socketio.emit("image", relative_image_path)

if __name__ == "__main__":
    socketio.run(app, debug=True)

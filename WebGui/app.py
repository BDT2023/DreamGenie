# Run with gunicorn app:app --worker-class eventlet --bind 127.0.0.1:5000
# IMPORTANT! this should be first, otherwise the code breaks
import eventlet

eventlet.monkey_patch()

import sys
import threading
import time
import wave
from flask import (
    copy_current_request_context,
    request,
    Flask,
    render_template,
    session,
    jsonify,
)
from flask_sse import sse
from flask_session import Session
import requests
import string
import io
from io import BytesIO
from urllib.request import urlopen
import base64
import os
import logging
import datetime
import concurrent
import uuid


sys.path.append("../Scene_Analyzer")
sys.path.append("../Image_Generation")
sys.path.append("../Utils")

os.chdir(
    f"{os.path.dirname(os.path.realpath(__file__))}"
)  # Change directory to current file location  ')")
cwd = os.getcwd()
print(cwd)

from gpt_call import call_openai
from send_prompt import send_to_sd
from utils import get_service_urls
from send_prompt import poll_results

IS_TEST = True
app = Flask(__name__)
app.logger.setLevel(logging.INFO)

app.config["REDIS_URL"] = "redis://localhost"
app.config["SESSION_TYPE"] = "redis"
app.config["SECRET_KEY"] = "secret!"
app.register_blueprint(sse, url_prefix="/stream")
Session(app)

# Global variables
progress1 = 0
scenes_list = []
current_scene_index = 0
URLS = get_service_urls()


def poll_results_until_done():
    time_started = time.time()
    TIMEOUT = 50  # seconds
    while True:
        progress = poll_results()
        if progress <= 0 or progress >= 99 or time.time() > time_started + TIMEOUT:
            break
        # print(f"Progress: {progress}%")
        # socketio.emit("progress", progress)
        time.sleep(0.5)


@app.route("/")
def index():
    # generate a unique user id
    if "user_id" not in session:
        user_id = str(uuid.uuid4())
        session["user_id"] = user_id
        session.modified = True
    else:
        user_id = session["user_id"]
    print("User id: " + user_id)
    return render_template("index.html", user_id=user_id)


@app.route("/gallery")
def gallery():
    if "user_id" not in session:
        return "No user id found. Please go back to the home page and try again."
    else:
        user_id = session["user_id"]
    print("User id: " + user_id)
    app.logger.info("Gallery requested")
    return render_template("gallery.html", user_id=user_id)


@app.route("/user_input", methods=["POST"])
def receive_user_input():
    """
    Endpoint to receive a POST request with user input.
    """
    global progress, scenes_list, current_scene_index
    input_data = request.form["user_input"]
    app.logger.info("User input received" + (input_data))
    # eventlet.sleep(0)
    # Reset global variables
    progress = 0
    scenes_list = []
    current_scene_index = 0
    # Start processing the input
    with app.app_context():
        eventlet.spawn(process_input, input_data, session["user_id"])
    app.logger.info("Started background task")
    return jsonify(success=True)


def process_input(input_data, user_id):
    with app.app_context():
        sse.publish(
            {"message": "foo"},
            type="message",
            channel=user_id,
        )
    global progress1, scenes_list
    # socketio.emit("progress", progress)
    # Update progress
    # progress1 = 10
    # socketio.emit("progress", progress)

    # TODO: change the placeholder!
    # Call OpenAI GPT-3 to separate scenes
    scenes_list = call_openai(input_data, test=IS_TEST)
    # scenes_list = [input_data]
    # Update progress
    # progress1 = 100
    # socketio.emit("progress", progress)

    # Get today's date
    today = datetime.date.today()

    # Generate images for scenes

    for i, scene in enumerate(scenes_list):
        # socketio.sleep(0)
        # Update progress for each scene
        progress1 = 0
        # socketio.emit("progress", progress)

        # Generate image for scene using SD

        image_path = send_to_sd(scene, isWeb=True)
        app.logger.info(f"send_to_sd called")
        app.logger.info(f"image_path: {image_path}")
        # socketio.start_background_task(poll_results_until_done)

        # with concurrent.futures.ThreadPoolExecutor() as executor:
        #     executor.submit(poll_results_until_done)

        # Update progress
        progress1 = 100

        # Display the image to the user
        # Extract only the part of the path from the 'static' directory onwards
        relative_image_path = os.path.join(
            "static", today.isoformat(), os.path.basename(image_path)
        )
        app.logger.info(f"relative_image_path: {relative_image_path}")
        # convert the path to a blob object

        with open(relative_image_path, "rb") as f:
            image_blob = f.read()
            base64_bytes = base64.b64encode(image_blob)
            base64_string = base64_bytes.decode()
            base64_image = "data:image/png;base64," + base64_string

        print("Publishing from " + user_id + "!")
        with app.app_context():
            sse.publish(
                {"image": base64_image, "scene": f"Scene {i+1}: \n" + scene},
                type="image_and_scene",
                channel=user_id,
            )

        app.logger.info(f"Emitted: Image path: {relative_image_path}")


# # DEPRECATED
# @socketio.on("get_progress")
# def handle_get_progress():
#     app.logger.info("Progress requested")
#     emit("progress", progress)


# DEPRECATED
# @socketio.on("get_scene")
# def handle_get_scene():
#     global scenes_list, current_scene_index
#     app.logger.info("Scene requested")
#     if current_scene_index < len(scenes_list):
#         scene = scenes_list[current_scene_index]
#         current_scene_index += 1
#         emit("scene", scene)
#     else:
#         emit("no_more_scenes")


# Create an empty list to store received chunks
audio_chunks = []


# Receive base64 encoded audio chunk
# DEPRECATED
# @socketio.on("audioChunk")
# def process_audio_chunk(chunk):
#     app.logger.info("Received audio chunk")
#     audio_chunks.append(chunk)


# When all audio chunks are received, reassemble the WAV file
# DEPRECATED
# @socketio.on("audioComplete")
# def process_complete_audio():
#     app.logger.info("Received all audio chunks")

#     # Combine the received chunks into a single base64 string
#     complete_base64 = "".join(audio_chunks)

#     # Decode the complete base64 string to obtain binary audio data
#     decoded_data = base64.b64decode(complete_base64)

#     # Create a BytesIO object to mimic a file
#     audio_file = BytesIO(decoded_data)
#     audio_file.name = "audio.wav"

#     # Save the audio file to disk for debugging (optional)
#     with open("audio.wav", "wb") as f:
#         f.write(decoded_data)

#     # Further processing or sending the audio file to the server can be done here
#     # ...

#     app.logger.info("Processing complete audio")


# DEPRECATED
# @socketio.on("endAudio")
# def end_audio(data):
#     global audio_chunks
#     print("End of audio received. Processing...")

#     # Here, concatenate all the audio chunks
#     complete_audio_data = base64.b64decode("".join(audio_chunks))

#     send_request(complete_audio_data)
#     audio_chunks = []
#     # Create an empty list to store received chunks


# def send_request(audio_data):
#     url = URLS["whisper"] + "/whisper"
#     audio_file = BytesIO(audio_data)
#     audio_file.name = "audio.wav"

#     files = {"file": audio_file}
#     response = requests.post(url, files=files, auth=("bdt", "12xmnxqgkpzj9cjb"))

#     result = response.json()["results"][0]["transcript"]
#     # socketio.emit("result", result)
#     print(f"Result: {result}")


def send_request(audio_data, user_id):
    url = URLS["whisper"] + "/whisper"
    # Wraps the audio data in a BytesIO object to mimic a file
    audio_file = BytesIO(audio_data)
    audio_file.name = "audio.wav"
    # save the audio file to disk for debugging
    with open("audio.wav", "wb") as f:
        f.write(audio_data)
        f.close()

    # The 'files' parameter for 'requests.post' should be a dictionary or a list of tuples
    files = {"file": audio_file}
    app.logger.info(files)
    response = requests.post(url, files=files, auth=("bdt", "12xmnxqgkpzj9cjb"))
    app.logger.info(response)
    result = response.json()["results"][0]["transcript"]
    print(result)
    app.logger.info(result)

    # TODO: update to SSE
    # Emitting to the originating client
    with app.app_context():
        sse.publish(
            {"audio_result": result},
            type="audio_result",
            channel=user_id,
        )
    app.logger.info("Emitted audio")


@app.route("/audio", methods=["POST"])
def process_audio():
    audioData = request.files["audio"]
    app.logger.info("Audio received")
    app.logger.info(audioData)
    try:
        # decoded_data = base64.b64decode(audioData.read())
        with app.app_context():
            eventlet.spawn(send_request, audioData.read(), session["user_id"])
        success = True
    except Exception as e:
        app.logger.error(e)
        success = False

    return jsonify(success)


# #DEPRECATED - need to convert to SSE
# @socketio.on("audio")
# def process_audio(audioData):
#     app.logger.info("Audio received")

#     @copy_current_request_context
#     def send_request(audio_data):
#         url = URLS["whisper"] + "/whisper"
#         # Wraps the audio data in a BytesIO object to mimic a file
#         audio_file = BytesIO(audio_data)
#         audio_file.name = "audio.wav"
#         # save the audio file to disk for debugging
#         with open("audio.wav", "wb") as f:
#             f.write(audio_data)
#             f.close()

#         # The 'files' parameter for 'requests.post' should be a dictionary or a list of tuples
#         files = {"file": audio_file}
#         app.logger.info(files)
#         response = requests.post(url, files=files, auth=("bdt", "12xmnxqgkpzj9cjb"))
#         app.logger.info(response)
#         result = response.json()["results"][0]["transcript"]
#         print(result)
#         app.logger.info(result)

#         # TODO: update to SSE
#         # Emitting to the originating client
#         socketio.emit("result", result, room=request.sid)
#         app.logger.info("Emitted audio")

#     decoded_data = base64.b64decode(audioData)
#     socketio.start_background_task(send_request, decoded_data)

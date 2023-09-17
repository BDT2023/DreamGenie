# Run with gunicorn app:app --worker-class eventlet --bind 127.0.0.1:5000
# IMPORTANT! this should be first, otherwise the code breaks
import eventlet

eventlet.monkey_patch()
import sys
import time
from flask import (
    request,
    Flask,
    render_template,
    session,
    jsonify,
    redirect,
    url_for
)
from flask_sse import sse
from flask_session import Session
import requests
from io import BytesIO
import base64
import os
import logging
import datetime
import uuid
import redis


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

app.config["SESSION_TYPE"] = "redis"
host = os.getenv("REDIS_HOST", "localhost")
app.logger.info(f"REDIS_HOST: {host}")
r = redis.Redis(host=host, port=6379)
r.ping()

# get redis url:
# redis_url = r.connection_pool.connection_kwargs.get("url")
app.config["SESSION_REDIS"] = r
app.config["SSE_REDIS_URL"] = app.config["REDIS_URL"] = os.getenv(
    "REDIS_URL", "redis://localhost"
)
app.logger.info(app.config["REDIS_URL"])
app.config["SECRET_KEY"] = "secret!"
app.register_blueprint(sse, url_prefix="/stream")
Session(app)

# Global variables
progress1 = 0
scenes_list = []
current_scene_index = 0
URLS = get_service_urls()

#currently not used
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
    global progress1, scenes_list

    # TODO: change the placeholder!

    # Call OpenAI GPT-3 to separate scenes
    scenes_list = call_openai(input_data, test=IS_TEST)
    # scenes_list = [input_data]

    # Get today's date
    today = datetime.date.today()

    # Generate images for scenes

    for i, scene in enumerate(scenes_list):
        # Update progress for each scene
        progress1 = 0

        # Generate image for scene using SD
        image_path = send_to_sd(scene, isWeb=True)
        app.logger.info(f"send_to_sd called")
        app.logger.info(f"image_path: {image_path}")

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


# Create an empty list to store received chunks
audio_chunks = []


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

    # Emitting to the originating client
    with app.app_context():
        sse.publish(
            {"audio_result": result},
            type="audio_result",
            channel=user_id,
            retry=1000
        )
    app.logger.info("Emitted audio result to " + user_id)


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

@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    image_rating = request.form.get('image_rating')
    sound_rating = request.form.get('sound_rating')
    scene_rating = request.form.get('scene_rating')
    experience_rating = request.form.get('experience_rating')
    
    # Save the ratings to a database or a file
    # (Your logic here)
    
    return render_template('thank_you.html')
    
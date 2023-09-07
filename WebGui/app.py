import sys
import threading
import time
import tkinter as tk
import wave
from tkinter import filedialog, messagebox

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

sys.path.append("../Scene_Analyzer")
sys.path.append("../Image_Generation")
sys.path.append("../Utils")
import os
os.chdir(os.path.dirname(__file__))
cwd = os.getcwd()
print(70000000000)
print(cwd)
import string

from gpt_call import call_openai
from send_prompt import send_to_sd
from utils import get_service_urls

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Global variables
progress = 0
scenes_list = []
current_scene_index = 0

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('user_input')
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

@socketio.on('get_progress')
def handle_get_progress():
    emit('progress', progress)

@socketio.on('get_scene')
def handle_get_scene():
    global scenes_list, current_scene_index

    if current_scene_index < len(scenes_list):
        scene = scenes_list[current_scene_index]
        current_scene_index += 1
        emit('scene', scene)
    else:
        emit('no_more_scenes')

def process_input(input_data):
    global progress, scenes_list

    # Update progress
    progress = 10
    socketio.emit('progress', progress)

    # Call OpenAI GPT-3 to separate scenes
    scenes_list = call_openai(input_data)

    # Update progress
    progress = 100
    socketio.emit('progress', progress)

    # Generate images for scenes
    for scene in scenes_list:
        # Update progress for each scene
        progress = 0
        socketio.emit('progress', progress)

        # Generate image for scene
        image_path = send_to_sd(scene)

        # Update progress
        progress = 100
        socketio.emit('progress', progress)

        # Display the image to the user
        socketio.emit('image', image_path)


if __name__ == "__main__":
    socketio.run(app, debug=True)

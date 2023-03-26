import tkinter as tk
from tkinter import messagebox
import wave
import struct
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
import pyaudio
import threading
import requests
import sys
sys.path.append('../Scene_Analyzer')
sys.path.append('../Image_Generation')

from recorder_gui import run_gui
from send_prompt import send_to_sd
from yes_no_gui import get_user_input as yes_no_gui
import argparse
from icecream import ic
from send_prompt import get_service_urls
import requests
from gpt_call import separate_random

import os
# TODO: add __init__.py to the other modules
# add path to the other modules to enable import
os.chdir(os.path.dirname(__file__))


# os.chdir(os.path.dirname(__file__))
URL = get_service_urls()['whisper']


class HelloWorldWindow:
    def __init__(self, master):
        self.master = master
        self.initial_message = "Hello there! I'm BotLisa! what do you want to draw?\n please click on record\n"

        # Create and place "Hello World" label at top middle
        hello_label = tk.Label(self.master, text=self.initial_message)
        hello_label.pack(side=tk.TOP)
        
        self.frames = []  # Initialize array to store frames
        self.p = pyaudio.PyAudio()  # Create an instance of PyAudio
        self.sample_format = pyaudio.paInt16  # 16 bits per sample
        self.channels = 2
        self.fs = 44100  # Record at 44100 samples per second
        self.chunk = 1024  # Record in chunks of 1024 samples

        self.recording = False

        self.record_button = tk.Button(master, text="Record", command=self.start_recording)
        self.stop_button = tk.Button(master, text="Stop", command=self.stop_recording)
        self.play_button = tk.Button(master, text="Play", command=self.play_recording)
        self.save_button = tk.Button(master, text="Save & Continue", command=self.save_recording)

        self.stop_button.config(state=tk.DISABLED)
        self.play_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)

        self.record_button.pack()
        self.stop_button.pack()
        self.play_button.pack()
        self.save_button.pack()

        # Create and place "Cancel" button at bottom left
        cancel_button = tk.Button(self.master, text="Cancel", command=self.on_cancel)
        cancel_button.pack(side=tk.BOTTOM, padx=10, pady=10, anchor=tk.SW)

        
    def start_recording(self):
        self.recording = True
        self.record_thread = threading.Thread(target=self._record)
        self.record_thread.start()

        self.record_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

    def on_cancel(self):
        # Display a messagebox asking if the user wants to cancel
        result = messagebox.askquestion("Cancel", "Are you sure you want to cancel?")
        if result == "yes":
            self.master.quit() # Exit the program
        else:
            pass # Do nothing and return to the window
        
    def clear_window(self):
        # Destroy all widgets in the window
        for widget in self.master.winfo_children():
            widget.destroy()

    def on_start(self):
        # Create and show the second window
        self.clear_window()
        self.second_window = FunWindow(self.master)
        
    def _record(self):
        self.stream = self.p.open(format=self.sample_format,
                                 channels=self.channels,
                                 rate=self.fs,
                                 frames_per_buffer=self.chunk,
                                 input=True)
        while self.recording:
            data = self.stream.read(self.chunk)
            self.frames.append(data)
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

    def stop_recording(self):
        self.recording = False
        self.record_thread.join()
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        self.record_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.play_button.config(state=tk.NORMAL)
        self.save_button.config(state=tk.NORMAL)

    def play_recording(self):
        self.p = pyaudio.PyAudio()  # Create an instance of PyAudio

        # Open a new stream to play the recorded audio
        stream = self.p.open(format=self.sample_format,
                            channels=self.channels,
                            rate=self.fs,
                            output=True)

        # Write the recorded frames to the stream
        for frame in self.frames:
            stream.write(frame)

        stream.stop_stream()
        stream.close()

        self.p.terminate

    def save_recording(self):
        # Open a file in write-binary mode
        #filename = filedialog.asksaveasfilename(title="Save file", filetypes=(("wav files", "*.wav"), ("all files", "*.*")))
        filename = "voice_input.wav"
        if filename:
            wf = wave.open(filename, "wb")

            # Set the parameters of the file
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.p.get_sample_size(self.sample_format))
            wf.setframerate(self.fs)

            # Write the frames as bytes to the file
            wf.writeframes(b"".join(self.frames))

            wf.close()
        self.frames = []
        self.play_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)
        
        # Create and show the second window
        self.clear_window()
        self.second_window = ValidateInputWindow(self.master)
        filename = 'voice_input.wav'
        url = URL+'/whisper'
        data = {'file': (filename, open(filename, 'rb'), 'audio/wav')}
        
        t = threading.Thread(target=self.send_request, args=(url , data, self.second_window))
        t.start()

        # global root
        # if messagebox.askokcancel("Save and exit", "Do you want to save and exit the recording?"):
        #     root.destroy()
        #root.protocol("WM_DELETE_WINDOW", on_closing)
        
        
    def send_request(self, url, data, validate_window):
        # Create a new thread to send the request
        response = requests.post(url, files=data, auth=('bdt', '12xmnxqgkpzj9cjb'))
        result = response.json()['results'][0]['transcript']
        
        validate_window.update(result)

class FunWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Fun!!!")

        # Create and place "Fun!!!" label at top middle
        fun_label = tk.Label(self.master, text="Fun!!!")
        fun_label.pack(side=tk.TOP)

        # Create a text box
        self.text_box = tk.Text(self.master, height=5, width=50)
        self.text_box.pack(side=tk.TOP, pady=10)

        # Create and place "Submit" button
        submit_button = tk.Button(self.master, text="Submit", command=self.on_submit)
        submit_button.pack(side=tk.TOP)

    def on_submit(self):
        # Get the text from the text box and print it to the console
        text = self.text_box.get("1.0", "end-1c")
        print(text)
        
class ValidateInputWindow:
    def __init__(self, master):
        self.master = master

        self.loading_label = tk.Label(master, text="Loading input...")
        self.loading_label.pack()

        
        
    def update(self, response_text):
        # Destroy the loading label
        self.loading_label.destroy()
        self.yes_button = tk.Button(self.master, text="Yes, continue", command=self.on_yes_button)
        self.yes_button.pack(side="left", padx=10, pady=10)

        self.no_button = tk.Button(self.master, text="No, go back", command=self.on_no_button)
        self.no_button.pack(side="right", padx=10, pady=10)

        # Show the response text in the new window
        self.concat_text = "Did you say: " + response_text + "?"
        
        self.response_label = tk.Label(self.master, text=self.concat_text, wraplength=200)
        self.response_label.pack()
    

    def on_yes_button(self):
        print("Yes button clicked")
        print("we can show the image")

    def on_no_button(self):
        print("No button clicked")
        self.clear_window()
        self.first_window = HelloWorldWindow(self.master)
        
    def clear_window(self):
        # Destroy all widgets in the window
        for widget in self.master.winfo_children():
            widget.destroy()

def on_closing():
    global root
    if messagebox.askokcancel("Abort", "Do you want to exit the program completely?"):
        root.destroy()
    quit()
    
    
if __name__ == "__main__":
    root = tk.Tk()
    # size of the window
    root.geometry("400x300")
    app = HelloWorldWindow(root)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

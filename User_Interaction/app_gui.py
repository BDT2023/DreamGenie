import tkinter as tk
from tkinter import messagebox
import wave
from tkinter import messagebox
from tkinter import filedialog
import pyaudio
import threading
import requests
import sys
from PIL import Image, ImageTk
sys.path.append('../Scene_Analyzer')
sys.path.append('../Image_Generation')

from send_prompt import send_to_sd
from send_prompt import get_service_urls
import requests
import customtkinter as ctk

import os
# TODO: add __init__.py to the other modules
# add path to the other modules to enable import
os.chdir(os.path.dirname(__file__))


# os.chdir(os.path.dirname(__file__))
URL = get_service_urls()['whisper']


class StartWindow:
    def __init__(self, master):
        self.master = master
        

        # Create two radio buttons for Text and Audio
        self.mode = tk.StringVar()
        self.mode.set("text")
        self.text_radio = ctk.CTkRadioButton(master, text="Text", variable=self.mode, value="text")
        self.audio_radio = ctk.CTkRadioButton(master, text="Audio", variable=self.mode, value="audio")
        self.text_radio.pack()
        self.audio_radio.pack()

        # Create a "proceed" button
        self.proceed_button = ctk.CTkButton(master, text="Proceed", command=self.next_window)
        self.proceed_button.pack()
        
    def clear_window(self):
        # Destroy all widgets in the window
        for widget in self.master.winfo_children():
            widget.destroy()

    def next_window(self):
        self.clear_window()
        # Open a new window based on the selected mode
        if self.mode.get() == "text":
            self.second_window = TextWindow(self.master)
        else:
            self.second_window = RecordWindow(self.master)


class TextWindow:
    def __init__(self, master):
        self.master = master
        self.initial_message = "Hello there! I'm BotLisa! what do you want to draw?\n" + \
        "Please write your dream\n"
        # self.font = ("Helvetica", 18, "normal", "roman")

        # Create and place "Hello World" label at top middle
        hello_label = ctk.CTkLabel(self.master, text=self.initial_message)
        hello_label.pack()
        
        # Create a text box
        # self.textbox = tk.Entry(master, width=50)
        # self.textbox.pack(padx=10, pady=10)
        self.textbox = ctk.CTkTextbox(master = self.master, width=300, 
                                      height=100, corner_radius=0)
        self.textbox.pack(padx=10, pady=10)
        # Set up an event listener to check for changes in the text box
        self.textbox.bind("<KeyRelease>", self.check_text)
        
        
        self.next_button = ctk.CTkButton(master, text="Save & Continue", 
                                         command=self.next, state=tk.DISABLED)
        self.next_button.pack()

        # Create and place "Cancel" button at bottom left
        cancel_button = ctk.CTkButton(self.master, text="Cancel", command=self.on_cancel)
        cancel_button.pack(side=tk.BOTTOM, padx=10, pady=10, anchor=tk.SW)

    
    def check_text(self, event):
        # Enable the Next button if the text box contains some text
        # "1.0" means that the input should be read from line one, character zero.
        # The end-1c is divided in 2 parts:
        # end: Read until the end of the text.
        # 1c: Remove 1 character starting from the end.
        if len(self.textbox.get("1.0",'end-1c')) > 0:
            self.next_button.configure(state=tk.NORMAL)
        else:
            self.next_button.configure(state=tk.DISABLED)

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

    
    def next(self):
        # Do something when Next is clicked
        self.text = self.textbox.get("1.0","end-1c")
        self.clear_window()

        self.second_window = ValidateInputWindow(self.master, self.text, mode = "text")
        


class RecordWindow:
    def __init__(self, master):
        self.master = master
        self.initial_message = "Hello there! I'm BotLisa! what do you want to draw?\n" + \
        "Please click on record\n"
        # self.font = ("Helvetica", 18, "normal", "roman")

        # Create and place "Hello World" label at top middle
        hello_label = ctk.CTkLabel(self.master, text=self.initial_message)
        hello_label.pack()
        
        self.frames = []  # Initialize array to store frames
        self.p = pyaudio.PyAudio()  # Create an instance of PyAudio
        self.sample_format = pyaudio.paInt16  # 16 bits per sample
        self.channels = 2
        self.fs = 44100  # Record at 44100 samples per second
        self.chunk = 1024  # Record in chunks of 1024 samples

        self.recording = False

        self.record_button = ctk.CTkButton(master, text="Record", command=self.start_recording)
        self.stop_button = ctk.CTkButton(master, text="Stop", command=self.stop_recording)
        self.play_button = ctk.CTkButton(master, text="Play", command=self.play_recording)
        self.save_button = ctk.CTkButton(master, text="Save & Continue", command=self.save_recording)

        self.stop_button.configure(state=tk.DISABLED)
        self.play_button.configure(state=tk.DISABLED)
        self.save_button.configure(state=tk.DISABLED)

        self.record_button.pack(padx=5, pady=5)
        self.stop_button.pack(padx=5, pady=5)
        self.play_button.pack(padx=5, pady=5)
        self.save_button.pack(padx=5, pady=5)

        # Create and place "Cancel" button at bottom left
        cancel_button = ctk.CTkButton(self.master, text="Cancel", command=self.on_cancel)
        cancel_button.pack(side=tk.BOTTOM, padx=10, pady=10, anchor=tk.SW)

        
    def start_recording(self):
        self.recording = True
        self.record_thread = threading.Thread(target=self._record)
        self.record_thread.start()

        self.record_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)

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
        self.record_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        self.play_button.configure(state=tk.NORMAL)
        self.save_button.configure(state=tk.NORMAL)

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
        self.play_button.configure(state=tk.DISABLED)
        self.save_button.configure(state=tk.DISABLED)
        
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
    def __init__(self, master, response_text = None, mode = "audio"):
        self.response_text = response_text
        self.master = master
        self.mode = mode
        self.loading_label = ctk.CTkLabel(master, text="Loading input...")
        self.loading_label.pack()
        
        if response_text is not None:
            self.update(response_text)

    def update(self, response_text):
        # Destroy the loading label
        self.loading_label.destroy()
        
        # Show the response text in the new window
        self.response_text = response_text
        self.concat_text = "Did you mean: " + response_text + "?"
        
        self.response_label = ctk.CTkLabel(self.master, text=self.concat_text)
        self.response_label.pack()
        
        self.yes_button = ctk.CTkButton(self.master, text="Yes, continue", command=self.on_yes_button)
        self.yes_button.pack(padx=10, pady=10)
        
        self.no_button = ctk.CTkButton(self.master, text="No, go back", command=self.on_no_button)
        self.no_button.pack(padx=10, pady=10)

        
    

    def on_yes_button(self):
        
        # Create and show the second window
        self.clear_window()
        self.show_image_window = ShowImageWindow(self.master)

        # TODO - destroy thread when window is closed
        t = threading.Thread(target=self.send_request, args=(self.show_image_window,))
        t.start()
    
    def send_request(self, show_image_window):
        # Create a new thread to send the request
        path = send_to_sd(self.response_text)
        
        show_image_window.update(path)

    def on_no_button(self):
        
        self.clear_window()
        if self.mode == "audio":
            self.first_window = RecordWindow(self.master)
        else:
            self.first_window = TextWindow(self.master)
        
    def clear_window(self):
        # Destroy all widgets in the window
        for widget in self.master.winfo_children():
            widget.destroy()
            
class ShowImageWindow:
    def __init__(self, master):
        self.master = master
        self.progressbar = ctk.CTkProgressBar(master=master, determinate_speed=0.1)
        self.progressbar.pack(padx=20, pady=10)
        self.progressbar.start()
        # self.loading_label = ctk.CTkLabel(master, text="Loading input...")
        # self.loading_label.pack()
        

    def update(self, path):
        # Destroy the loading label
        # self.loading_label.destroy()
        self.progressbar.destroy()

        # Create an object of tkinter ImageTk
        self.img = ImageTk.PhotoImage(Image.open(path))
        # Create a Label Widget to display the text or Image
        self.image_label = tk.Label(self.master, image = self.img)
        self.image_label.pack(fill=tk.BOTH, expand=True)


def on_closing():
    global root
    if messagebox.askokcancel("Abort", "Do you want to exit the program completely?"):
        root.destroy()
    quit()
    
    
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    # root = tk.Tk()
    root = ctk.CTk()
    # size of the window
    root.geometry("400x300")
    app = StartWindow(root)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

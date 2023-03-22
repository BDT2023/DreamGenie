import wave
import struct
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
import pyaudio
import threading

class AudioRecorder:
    def __init__(self, master):
        self.master = master
        master.title("Audio Recorder")
        
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
        self.save_button = tk.Button(master, text="Save", command=self.save_recording)

        self.stop_button.config(state=tk.DISABLED)
        self.play_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)

        self.record_button.pack()
        self.stop_button.pack()
        self.play_button.pack()
        self.save_button.pack()

    def start_recording(self):
        self.recording = True
        self.record_thread = threading.Thread(target=self._record)
        self.record_thread.start()

        self.record_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

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
        global root
        if messagebox.askokcancel("Save and exit", "Do you want to save and exit the recording?"):
            root.destroy()
        #root.protocol("WM_DELETE_WINDOW", on_closing)
        
def on_closing():
    global root
    if messagebox.askokcancel("Abort", "Do you want to exit the program completely?"):
        root.destroy()
    quit()

def run_gui():
    global root
    root = tk.Tk()
    my_gui = AudioRecorder(root)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
    
if __name__ == "__main__":
    run_gui()    
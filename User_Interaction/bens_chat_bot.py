import openai
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import io
import requests
import sys
sys.path.append('../Image_Generation')
sys.path.append('../Scene_Analyzer')
from send_prompt import send_to_sd
from gpt_call import call_openai
# Replace 'your_openai_api_key' with your actual API key

def record_audio(duration=20, fs=16000):
    print("Recording audio...")
    recorded_data = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype=np.int16)
    sd.wait()
    print("Recording complete.")
    return recorded_data

def transcribe_audio(audio_data, fs):
    wav_file = io.BytesIO()
    write(wav_file, fs, audio_data)
    wav_file.seek(0)
    url = f"https://api.openai.com/v1/engines/davinci-codex/completions"
    headers = {
        "Content-Type": "audio/wav",
        "Authorization": f"Bearer {openai.api_key}",
    }
    response = requests.post(url, headers=headers, data=wav_file)
    response.raise_for_status()
    return response.json()["choices"][0]["text"].strip()

def get_user_input(input_type):
    if input_type == "text":
        user_input = input()
    else:
        audio_data = record_audio()
        user_input = transcribe_audio(audio_data,audio_data.shape[0])
    return user_input


def main():
    while True:
        print("Hey, please tell me about a dream you had.")
        transcript = get_user_input("text")
        print("Before we continue, is this your desired prompt: \n\"" + transcript + "\"?")
        confirmation = input("Type 'yes' to confirm or 'no' to re-enter the prompt: ").lower().strip()
        
        if confirmation == 'yes':
            scenes = call_openai(transcript)
            for scene in scenes:
                send_to_sd(scene)
        elif confirmation == 'no':
            continue
        else:
            print("Invalid input. Please try again.")

    

if __name__ == '__main__':
    main()

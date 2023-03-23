import openai
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import io
import requests
import sys
from icecream import ic
sys.path.append('../Scene_Analyzer')
sys.path.append('../Image_Generation')
from send_prompt import send_to_sd
from gpt_call import call_openai
from send_prompt import get_service_urls


def get_voice_input():    
    ic("Running run_gui()")
    run_gui()
    ic("Finished run_gui(), Transcribing audio")
    filename = 'voice_input.wav'
    url = URL+'/whisper'
    data = {'file': (filename, open(filename,'rb'), 'audio/wav')}
    response = requests.post(url, files=data,auth=('bdt','12xmnxqgkpzj9cjb'))
    result = response.json()['results'][0]['transcript']
    ic("Finished Transcribing audio")
    ic(f'User says: "{result}"')
    return result

# TODO: remove this function
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
        user_input = get_voice_input()
    return user_input


def main():
    
    while True:
        print("Hey, please tell me about a dream you had.")
        #transcript = get_user_input("text")
        print("Before we continue, is this your desired prompt: \n\"" + transcript + "\"?")
        confirmation = input("Type 'yes' to confirm or 'no' to re-enter the prompt: ").lower().strip()
        
        if confirmation == 'yes':
            scenes = call_openai(transcript)
            for scene in scenes:
                if scene.strip():
                    send_to_sd(scene)
                    print(scene)
        elif confirmation == 'no':
            break
        else:
            print("Invalid input. Please try again.")


if __name__ == '__main__':
    main()

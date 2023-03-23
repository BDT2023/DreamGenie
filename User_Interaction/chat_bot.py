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

import os
# TODO: add __init__.py to the other modules
# add path to the other modules to enable import
os.chdir(os.path.dirname(__file__))
from gpt_call import separate_random

# os.chdir(os.path.dirname(__file__))
URL = get_service_urls()['whisper']


'''
A hard coded chat bot that will guide the user through the process of creating an image
'''

# here are some "magic words"
# that will make our promt better
magic_words = ["HDR", "UHD", "4K", "8K", "64K", "highly detailed",
               "studio lighting", "Professional", "trending on artstation",
               "unreal engine", "vivid colors", "bokeh", "cinematic",
               "High resolution scan"]
# some parameters
default_img_size = "512x512"
default_img_format = "png"
# good balance
default_cfg = 7
default_step_count = 50
default_seed = "random"
# recommended to beginners since it's fast and can usually generate
# good images with only 10 steps
default_sampler = "DDIM"
negative_prompt = "lowres, text, error, cropped, worst quality, low quality," \
                  " jpeg artifacts, ugly, duplicate, morbid, mutilated, out of" \
                  " frame, extra fingers, mutated hands, poorly drawn hands," \
                  " poorly drawn face, mutation, deformed, blurry, dehydrated, bad anatomy," \
                  " bad proportions, extra limbs, cloned face, disfigured, gross proportions," \
                  " malformed limbs, missing arms, missing legs, extra arms, extra legs," \
                  " fused fingers, too many fingers, long neck, username, watermark, signature"


'''
A function that gets voice input from the user using the recorder_gui.py module, and transcribes it using whisper.
'''
# def get_voice_input():
#     ic("Running run_gui()")
#     run_gui()
#     ic("Finished run_gui(), Transcribing audio")

#     result = model.transcribe('voice_input.wav')
#     ic("Finished Transcribing audio")
#     output_text = result["text"]
#     print(f'User says: "{output_text}"')
#     return output_text


def get_voice_input():
    ic("Running run_gui()")
    run_gui()
    ic("Finished run_gui(), Transcribing audio")
    filename = 'voice_input.wav'
    url = URL+'/whisper'
    data = {'file': (filename, open(filename, 'rb'), 'audio/wav')}
    response = requests.post(url, files=data, auth=('bdt', '12xmnxqgkpzj9cjb'))
    result = response.json()['results'][0]['transcript']
    ic("Finished Transcribing audio")
    ic(f'User says: "{result}"')
    return result

'''
Helper function that will validate the user input
'''
def input_validation(user_input, valid_input_list):
    while True:
        if user_input in valid_input_list:
            return user_input
        else:
            print("I'm sorry, I didn't understand that. Please answer:\n" + ' or\n'.join(valid_input_list) + '!')
            user_input = get_user_input()
            continue


def yes_no_validation(user_input):
    while True:
        if user_input == "yes":
            return True
        elif user_input == "no":
            return False
        else:
            print("I'm sorry, I didn't understand that. Please answer \"yes\" or \"no\"!")
            user_input = input()
            continue


def edit_component(component, list_of_options, user_input):
    print(f"Would you like to edit the {component} of the image?\n"
          "Please answer \"yes\" or \"no\" \n(answer \"no\" "
          f"if you already satisfied with the {component} or already mentioned it in the prompt)")
    
    fourth_input = yes_no_gui()
    if second_input == "Yes":
        print(f"Let's choose a {component}!")
        print("Please choose one of the following:")
        print('\n'.join(list_of_options))
        fifth_input = get_user_input()
        fifth_input = input_validation \
            (fifth_input, list_of_options)
        user_input = user_input + ", " + fifth_input + " " + component
        return answer, user_input
    else:
        print("Okay, let's continue!")
        return answer, user_input


def generate_image(user_input, mode="txt2img", flag=False):
    print("Okay, creating your image now! please wait a few seconds...")
    print("The prompt is: " + user_input)
    send_to_sd(prompt=user_input)
    print("Here's your image! I hope you like it!")
    if flag:
        print("We can make it better if you want to!")
    continue_or_exit()


def generate_or_edit(user_input, mode="txt2img"):
    print("Would you like to generate the image now or continue editing it?"
          " Please answer \"generate\" or \"continue\"")
    sixth_input = input()
    sixth_input = input_validation(sixth_input, ["generate", "continue"])
    if sixth_input == "generate":
        print("Okay, generating your image now! please wait a few seconds...")
        generate_image(user_input, mode)
    else:
        print("Okay, let's continue editing!")
        return


def continue_or_exit():
    print("Do you want to continue the process of editing the image?\n"
          "Please answer \"yes\" or \"no\"")

    third_input = input()
    if yes_no_validation(third_input):
        print("Great! Let's continue!")
    else:
        print("Okay, I hope you liked the image! Bye!")
        # TODO: add a way to save the image
        exit()


def get_user_input():
    global INPUT
    if INPUT == "text":
        INPUT = input()
    else:
        INPUT = get_voice_input()
    ic(INPUT)
    return INPUT


if __name__ == "__main__":
    global INPUT
    # parse the arguments, if there are any,access with args.{argument name}
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", type=str, default="random", help="prompt for the image")
    parser.add_argument("--mode", type=str, default="auto", help="auto or manual")
    parser.add_argument("--input", type=str, default="text", help="text or voice")
    args = parser.parse_args()
    
    INPUT = args.input
    
    print("Hello there! I'm Lisa! so nice to meet you"
          " here!\nI'm a chatbot, so I can't really "
          "talk to you, but I can help you with drawing"
          " some nice images!\nSo, what do you want to draw?\n"
          "please mention also if you want image or painting, for better results!\n")
    user_input = ""

    # loop to get the user input
    while True:
        # if we don't want user prompt, we will generate a random one from the dreams
        # TODO: fix bug - if we choose --input as 'voice' we do not want args.mode to be 'auto'
        if args.mode == "auto":
            user_input = separate_random()
        else:
            user_input = get_user_input()
        print("Before we continue, is this your desired prompt: \n\"" + user_input + "\"?")
        second_input = yes_no_gui()
        if second_input == "Yes":
            print("Great! Let's continue!")
            break
        else:
            print("Oh, I'm sorry! Let's try again!")
            continue
    generate_image(user_input, "txt2img", flag=True)

    # we will try to enhance the prompt, and then show the image again - hopefully better
    # we used the prompt guide from the paper:
    # https://cdn.openart.ai/assets/Stable%20Diffusion%20Prompt%20Book%20From%20OpenArt%2011-13.pdf

    # lighting_list = ["Daylight", "Overcast", "Night", "Flash", "Fluorescent", "Incandescent", "Soft",
    #                  "Ambient", "Sunlight", "Shade", "Backlight", "Candlelight", "Cinematic", "Nostalgic",
    #                  "Sun Rays", "Purple Haze", "Neon"]

    # answer, user_input = edit_component("lighting", lighting_list, user_input)
    # if answer: generate_or_edit(user_input, "img2img")
    # environment_list = ["Indoor", "Outdoor", "Urban", "Rural", "Natural", "Artificial", "Cinematic", "Fantasy",
    #                     "In Space", "In Water", "In Air", "In a Room", "In a Building", "In a Forest", "In a City"]
    # answer, user_input = edit_component("environment", environment_list, user_input)
    # if answer: generate_or_edit(user_input, "img2img")
    # color_scheme_list = ["Monochrome", "Grayscale", "Color", "Vibrant", "Pastel", "dark",
    #                      "light", "warm", "cool", "Complementary", "Analogous", "Triadic", "split-complementary"]
    # answer, user_input = edit_component("color scheme", color_scheme_list, user_input)
    # if answer: generate_or_edit(user_input, "img2img")
    # shot_type_list = ["Close-up", "Mid-shot", "Long-shot", "Extreme close-up", "Extreme long-shot", "POV"]
    # answer, user_input = edit_component("shot type", shot_type_list, user_input)
    # if answer: generate_or_edit(user_input, "img2img")
    # style_list = ["Realistic", "Abstract", "Cartoon", "Fantasy", "Photorealistic", "Surreal", "Polaroid",
    #               "Sketch", "Line Art", "Watercolor", "Oil Painting", "Acrylic Painting", "Digital Painting",
    #               "Mixed Media"
    #     , "Graffiti", "Manga", "Anime", "Comic", "Illustration", "3D", "3D Cartoon", "3D Realistic",
    #               "chalk", "pencil sketch", "caricature", "pop art", "pixel art", "vector art", "collage", "mosaic",
    #               "horror"]
    # answer, user_input = edit_component("style", style_list, user_input)
    # if answer: generate_or_edit(user_input, "img2img")
    # emotion_list = ["Happy", "Sad", "Angry", "Fearful", "Surprised", "Disgusted", "Calm", "Bored", "Excited",
    #                 "Romantic", "Sexy", "Gloomy", "Eerie", "Mysterious", "Elegant", "Glamorous", "Playful",
    #                 "Childish", "Cute", "Funny", "Grim", "Gory"]
    # answer, user_input = edit_component("emotion", emotion_list, user_input)
    # if answer: generate_or_edit(user_input, "img2img")

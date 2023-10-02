"""
This module contains functions for sending a prompt to the Stable Diffusion API and saving the resulting image.
"""
import sys

sys.path.append("../Utils")
from utils import get_service_urls
import requests
from icecream import ic
from PIL import Image
import base64
from io import BytesIO
import argparse
import json
import re

import os
from datetime import datetime
import time
import concurrent.futures

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")


counter = 0
URL = ""
URLS = {}  # dictionary of urls for each service (whisper, sd, etc)
session = requests.Session()
session.auth = (USERNAME, PASSWORD)


def save_image(img, folder, filename, isWeb):
    """
    Save an image to a specified folder.
    If isWeb is True, the function creates a subfolder called "static" inside the specified folder if it doesn't already exist.
    Then, it saves the image to the subfolder with the specified filename.
    Otherwise, if isWeb is False, the function checks if the specified folder exists and creates it if it doesn't.
    Then, it saves the image to the folder with the specified filename.

    Parameters:
        img (PIL.Image.Image): The image to be saved.
        folder (str): The folder where the image will be saved.
        filename (str): The name of the saved image file.
        isWeb (bool): Flag indicating whether we are working with the web app or not.

    Returns:
        str: The path where the image is saved.
    """
    if isWeb:
        static_folder = os.path.join("static", folder)
        if not os.path.exists(static_folder):
            os.makedirs(static_folder)
        save_path = os.path.join(static_folder, filename)
    else:
        if not os.path.exists(folder):
            os.makedirs(folder)
        save_path = os.path.join(folder, filename)

    img.save(save_path)
    return save_path


def poll_results():
    """
    Poll the results of the API call, using the progress endpoint of the Stable Diffusion on server.

    Returns:
        float: The progress of the API call.

    """
    response = session.get(URL + "/sdapi/v1/progress")
    if response.status_code != 200:
        raise Exception(f"API request failed: {response.text}")
    return round(float(response.json()["progress"]), 2)


def poll_results_until_done():
    """
    Polls the results until the process is done.

    This function continuously calls the `poll_results` function to check the progress of the process.
    It keeps polling until one of the following conditions is met:
    - The progress is less than or equal to 0.
    - The progress is greater than or equal to 99.
    - The timeout period of 50 seconds has elapsed.

    """
    time_started = time.time()
    TIMEOUT = 50  # seconds
    while True:
        progress = poll_results()
        if progress <= 0 or progress >= 99 or time.time() > time_started + TIMEOUT:
            break
        print(f"Progress: {progress}%")
        time.sleep(1)


def check_style_api():
    """
    Check the style API to see if the "project_tokens" style exists.

    Returns:
        bool: True if the style exists, False otherwise.
    """
    response = session.get(URL + "/sdapi/v1/prompt-styles")
    if response.status_code != 200:
        raise Exception(f"API request failed: {response.text}")
    for style in response.json():
        if style["name"] == "project_tokens":
            return True
    return False


def check_model_api():
    """
    Check the model API for available options.

    Returns:
        str: The model checkpoint for the sd_model.
    """
    response = session.get(URL + "/sdapi/v1/options")
    if response.status_code != 200:
        raise Exception(f"API request failed: {response.text}")
    return response.json()["sd_model_checkpoint"]


def check_and_load_model_api(model_name="dreamlikeDiffusion10_10.ckpt"):
    """
    Checks if the specified model is loaded in Stable diffusion and loads it if it is not already loaded.

    Args:
        model_name (str): The name of the model to be loaded. Default is "dreamlikeDiffusion10_10.ckpt".

    Returns:
        None
    """
    response = session.get(URL + "/sdapi/v1/options")
    curr_model = response.json()["sd_model_checkpoint"]
    print(f"Current model: {curr_model}")
    if model_name not in curr_model:
        response = session.post(
            URL + "/sdapi/v1/options", json={"sd_model_checkpoint": model_name}
        )
        if response.status_code != 200:
            raise Exception(f"API request failed: {response.text}")
        print(f"Loaded model: {model_name}")


def check_nsfw(response_text):
    pattern = r'\{\\"nsfw\\"\: \[(true|false)\]\}'
    # Use re.search to find the pattern in the text
    match = re.search(pattern, response_text)
    if match:
        # The pattern was found in the text
        bool_val = match.group(1)
        return True if bool_val in ("true", "True") else False
    else:
        # The pattern was not found in the text
        print("Pattern not found")
        return False


def send_to_sd(prompt, isWeb=False):
    """
    Sends a prompt to the sdapi/v1/txt2img endpoint and saves the resulting image.

    Args:
        prompt (str): The prompt to be sent to the API.
        isWeb (bool, optional): Indicates whether the function is being called from a web application. Defaults to False.

    Returns:
        str: The path to the saved image.

    Raises:
        Exception: If the API request fails.
    """
    print(f"web= {isWeb}")
    global counter, URL

    if URL == "":
        URLS = get_service_urls()
        URL = URLS["sd"]

    check_and_load_model_api()
    tokens = ""
    negative_prompt = ""
    tokens = """
    dream,expressive oil painting, whimsical atmosphere,
    trending on artstation HQ, amazing,artistic,vibrant,detailed,award winning,
    concept art, intricate details, realistic, Hyperdetailed, 8K resolution, Dramatic light,By Salvador Dalí
    """
    negative_prompt = """
    lowres, text, error, cropped, worst quality, low quality,jpeg artifacts, ugly, duplicate, morbid, mutilated, out of frame, extra fingers, mutated hands, poorly drawn hands,poorly drawn face, mutation, deformed, blurry, bad proportions, extra limbs, cloned face, disfigured, gross proportions, dehydrated, bad anatomy,malformed limbs,
    missing arms, missing legs, extra arms, extra legs,fused fingers, too many fingers, long neck, username, watermark, signature
    """
    style = ""

    # Experimental: trying to use premade negative embeddings for stable diffusion
    negative_embeddings = [
        "easynegative",
        "Unspeakable-Horrors-Composition-4v",
        "ng_deepnegative_v1_75t",
        "bad_prompt_version2",
    ]
    model_name = check_model_api()  # Get the name of the currently loaded sd checkpoint

    # The illuminati 2.0 sd checkpoint requires a different negative prompt
    if "illuminati" in model_name:
        negative_prompt += "nfixer,nartfixer,nrealfixer"
    else:
        tokens += "<lora:epi_noiseoffset_v2:1>"
    # https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/API
    payload = {
        "enable_hr": "false",
        "denoising_strength": 0,
        "firstphase_width": 0,
        "firstphase_height": 0,
        "prompt": f"{prompt + tokens}",
        "styles": [f"{style}"],  # maybe we don't need to add all the tokens
        "seed": -1,
        "subseed": -1,
        "subseed_strength": 0,
        "seed_resize_from_h": -1,
        "seed_resize_from_w": -1,
        "sampler_name": "DPM++ 2M Karras",  # can be changed to change the quality of the results
        "batch_size": 1,
        "n_iter": 1,
        "steps": 20,  # can be changed to affect the speed and quality of the results
        "cfg_scale": 7.5,
        "width": 768,
        "height": 512,
        "restore_faces": "false",
        "tiling": "false",
        "negative_prompt": f"{negative_prompt}",
        "script_name": "CensorScript",  # TODO: check how to implement this https://github.com/IOMisaka/sdapi-scripts
        "script_args": [True, False],  # Pass the script its arguments as a list
        # "script_args": [('put_at_start','false'),('different_seeds','true')], #Pass the script its arguments as a list
        "eta": 0,  # TODO: check about the following parameters
        "s_churn": 0,
        "s_tmax": 0,
        "s_tmin": 0,
        "s_noise": 1
        # "override_settings": {"sd_model_checkpoint": "dreamlikeart-diffusion-1.0.ckpt"},
    }

    def post_prompt(payload):
        return session.post(URL + "/sdapi/v1/txt2img", json=payload)

    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        ic(f'sending prompt: {payload["prompt"]}')
        future = executor.submit(post_prompt, payload)
        executor.submit(poll_results_until_done)
        x = future.result()
    ic(x)
    if x.status_code != 200:
        raise Exception(f"API request failed: {x.text}")
    # check if the image wasn't filtered due to nsfw
    nsfw = check_nsfw(x.text)
    with open("response.txt", "w") as f:
        f.write(x.text)

    ic(f"Time taken: {time.time() - start_time} seconds")
    for i in range(0, len(x.json()["images"])):
        im = Image.open(BytesIO(base64.b64decode(x.json()["images"][i])))
        extrema = im.convert("L").getextrema()
        if not extrema == (0, 0) and not nsfw:
            date_folder = datetime.now().strftime("%Y-%m-%d")
            counter += 1
            now = datetime.now().strftime("%H%M")
            save_path = save_image(im, date_folder, f"image_{counter}_{now}.png", isWeb)
            return save_path
        else:
            ic("Not safe for work!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", type=str, default="", help="url for the api server")
    args = parser.parse_args()

    if args.url != "":
        URL = args.url
    else:
        get_service_urls()["sd"]
    # prompt = input("Enter prompt: ")
    prompt = "A painting of a forest with a river flowing through it."
    prompt = "I am again in my mom's house -city- and there is all this preparation going on  and i suddenly find out that a war is about to break out. THere are foreign soldiers and lots of guns around. We don't know the language but sounds like Arabic and my kids are trying to send a text message to my husband to ask for help without being caught ..."
    prompt = "two cats fighting each other"
    prompt = "a wolf loping through the forest"
    send_to_sd(prompt)

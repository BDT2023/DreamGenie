import sys

sys.path.append("../Utils")
from utils import get_service_urls
import requests
from icecream import ic
from PIL import Image
import base64
from io import BytesIO
import argparse
#from my_secrets_ig import USERNAME, PASSWORD
import os
from datetime import datetime
import time
import concurrent.futures

USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')


counter = 0
URL = ""
URLS = {}  # dictionary of urls for each service (whisper, sd, etc)
session = requests.Session()
session.auth = (USERNAME, PASSWORD)


def save_image(img, folder, filename, isWeb):
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


# Deprecated
def get_url():
    global URL
    api_url = "https://api.ngrok.com/endpoints"
    headers = {"Authorization": f"Bearer {API_KEY}", "Ngrok-Version": "2"}
    response = session.get(api_url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"API request failed: {response.text}")
    if len(response.json()["endpoints"]) == 0:
        raise Exception(f"No endpoints found")
    URL = response.json()["endpoints"][0]["public_url"]
    return URL


# TODO: check edge cases
def poll_results():
    # s.auth = (USERNAME, PASSWORD)
    response = session.get(URL + "/sdapi/v1/progress")
    if response.status_code != 200:
        raise Exception(f"API request failed: {response.text}")
    # return response.json()['progress']
    return round(float(response.json()["progress"]), 2)


def poll_results_until_done():
    time_started = time.time()
    TIMEOUT = 50  # seconds
    while True:
        progress = poll_results()
        if progress <= 0 or progress >= 99 or time.time() > time_started + TIMEOUT:
            break
        print(f"Progress: {progress}%")
        time.sleep(1)


def check_style_api():
    response = session.get(URL + "/sdapi/v1/prompt-styles")
    if response.status_code != 200:
        raise Exception(f"API request failed: {response.text}")
    for style in response.json():
        if style["name"] == "project_tokens":
            return True
    return False


def check_model_api():
    response = session.get(URL + "/sdapi/v1/options")
    if response.status_code != 200:
        raise Exception(f"API request failed: {response.text}")
    return response.json()["sd_model_checkpoint"]


def send_to_sd(prompt, isWeb=False):
    print(f"web= {isWeb}")
    global counter, URL

    if URL == "":
        URLS = get_service_urls()
        URL = URLS["sd"]
    # BACKUP URL FOR PRESENTATION
    # URL = "https://9d6dbf0643353de5a3.gradio.live"

    # is_style = check_style_api()  # check if the style is already added
    # ic(is_style)
    is_style = True
    tokens = ""
    negative_prompt = ""

    # style = "project_tokens"
    # ic.disable()
    # if not is_style:
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
    negative_embeddings = [
        "easynegative",
        "Unspeakable-Horrors-Composition-4v",
        "ng_deepnegative_v1_75t",
        "bad_prompt_version2",
    ]
    model_name = check_model_api()
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
        "sampler_name": "DPM++ 2M",  # TODO: play with the results
        "batch_size": 1,
        "n_iter": 1,
        "steps": 30,
        "cfg_scale": 8.5,
        "width": 768,
        "height": 512,
        "restore_faces": "false",
        "tiling": "false",
        "negative_prompt": f"{negative_prompt}",
        # "script_name": "CensorScript",
        # "script_args": ['true','false'], #Pass the script its arguments as a list
        # "script_args": [('put_at_start','false'),('different_seeds','true')], #Pass the script its arguments as a list
        "eta": 0,  # TODO: check about the following parameters
        "s_churn": 0,
        "s_tmax": 0,
        "s_tmin": 0,
        "s_noise": 1
        # "override_settings": {"sd_model_checkpoint":'dreamlikeart-diffusion-1.0.ckpt [14e1ef5d]'}
    }

    def post_prompt(payload):
        return session.post(URL + "/sdapi/v1/txt2img", json=payload)

    # TODO: add timing meter to check how long it takes to get a result
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        ic(f'sending prompt: {payload["prompt"]}')
        future = executor.submit(post_prompt, payload)
        executor.submit(poll_results_until_done)
        x = future.result()
    # x = session.post(URL + '/sdapi/v1/txt2img', json=payload)
    ic(x)
    if x.status_code != 200:
        raise Exception(f"API request failed: {x.text}")
    # check if the image wasn't filterd due to nsfw
    ic(f"Time taken: {time.time() - start_time} seconds")
    for i in range(0, len(x.json()["images"])):
        im = Image.open(BytesIO(base64.b64decode(x.json()["images"][i])))
        extrema = im.convert("L").getextrema()
        if not extrema == (0, 0):
            # im.show()
            date_folder = datetime.now().strftime("%Y-%m-%d")
            counter += 1
            now = datetime.now().strftime("%H%M")
            save_path = save_image(im, date_folder, f"image_{counter}_{now}.png", isWeb)
            return save_path
        else:
            ic("Image completely black!")


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
    prompt = "A wolf starts loping around the person, panting"
    send_to_sd(prompt)

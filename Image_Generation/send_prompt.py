import sys

sys.path.append("../Utils")
from utils import get_service_urls
import requests
from icecream import ic
from PIL import Image
import base64
from io import BytesIO
import argparse
from my_secrets_ig import USERNAME, PASSWORD
import os
from datetime import datetime
import time
import concurrent.futures
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

counter = 0
URL = ""
URLS = {}  # dictionary of urls for each service (whisper, sd, etc)
session = requests.Session()
session.auth = (USERNAME, PASSWORD)
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount("http://", adapter)
session.mount("https://", adapter)


def save_image(img, folder, filename):
    if not os.path.exists(folder):
        os.makedirs(folder)
    img.save(os.path.join(folder, filename))


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


# '''
# A method to populate the URLS dictionary with the urls for each service, so that we can use them later
# '''
# def get_service_urls():
# ic.disable()
# global URLS
# api_url = "https://api.ngrok.com/tunnels"
# headers = {'Authorization': f'Bearer {API_KEY}', 'Ngrok-Version': '2'}
# response = requests.get(api_url, headers=headers)
# if response.status_code != 200:
#     raise Exception(f'API request failed: {response.text}')

# response = response.json()
# ic(response)
# tunnels = {}
# # iterate through the tunnels and get the public url, save it in the tunnels dictionary as a value, where the key is the tunnel session id
# for tunnel in response['tunnels']:
#     tunnels[tunnel['tunnel_session']['id']] = (tunnel['public_url'])

# # a dictionary of credential ids and the corresponding  service name
# credential_id = {'cr_2NFNS09sQ2z2nMSTrIkn5ZsMz80': 'whisper',
#                  'cr_2Ava69iIPmwypV1AyMlXHJ0MMvK': 'sd'}

# api_url = "https://api.ngrok.com/tunnel_sessions"
# headers = {'Authorization': f'Bearer {API_KEY}', 'Ngrok-Version': '2'}
# response = requests.get(api_url, headers=headers)
# if response.status_code != 200:
#     raise Exception(f'API request failed: {response.text}')
# tunnel_sessions = {}
# # match the tunnel session id with the credential id to use in locating the service name
# for tunnel in response.json()['tunnel_sessions']:
#     tunnel_sessions[tunnel['id']] = (tunnel['credential']['id'])
# ic(tunnel_sessions)
# # iterate through the tunnel sessions and add the corresponding url to the URLS dictionary
# for t in tunnel_sessions.keys():
#     URLS[credential_id[tunnel_sessions[t]]] = tunnels[t]
# ic(URLS)
# return URLS


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


def interrogate_image(img):
    global URL
    if URL == "":
        URLS = get_service_urls()
        URL = URLS["sd"]
    payload = {"image": f"{img}", "model": "clip"}
    x = session.post(URL + "/sdapi/v1/interrogate", json=payload)
    if x.status_code != 200:
        raise Exception(f"API request failed: {x.text}")
    print(x.json()["caption"].split(",")[0])


def send_to_sd(prompt):
    global counter, URL

    if URL == "":
        URLS = get_service_urls()
        URL = URLS["sd"]

    # is_style = check_style_api()  # check if the style is already added
    # ic(is_style)
    is_style = True
    style = ""
    tokens = """expressive oil painting, oil paints, whimsical atmosphere, matte painting trending on artstation HQ, amazing,artistic,vibrant,detailed,award winning, concept art, intricate details, realistic, Hyperdetailed, 8K resolution, Dramatic light"""
    negative_prompt = """lowres, text, error, cropped, worst quality, low quality,jpeg artifacts, ugly, duplicate, morbid, mutilated, out of frame, extra fingers, mutated hands, poorly drawn hands,poorly drawn face, mutation, deformed, blurry, bad proportions, extra limbs, cloned face, disfigured, gross proportions, dehydrated, bad anatomy,malformed limbs,missing arms, missing legs, extra arms, extra legs,fused fingers, too many fingers, long neck, username, watermark, signature
    """

    latent_couple = False
    if "AND" in prompt:
        latent_couple = True
        prompt.split("AND")
        temp = ""
        for s in prompt.split("AND"):
            temp += s + " " + tokens + " AND"
        # remove the last "AND"
        temp = temp.rsplit(' ', 1)[0]
        prompt = temp
    else:
        # ic.disable()
        if is_style:
            tokens = ""
            negative_prompt = ""
            style = "project_tokens"
    # model_name = check_model_api()
    # if 'illuminati' in model_name:
    #     negative_prompt += 'nfixer,nartfixer,nrealfixer'
    # else:
    #     tokens += "<lora:epi_noiseoffset_v2:1>"
    # https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/API
    #
    # Using scripts that are always on: Check "title" field in the Script class of the extension source code
    # to get arguments check "process_script_params" function in the extension source code
    payload = {
        "prompt": f"{prompt + tokens}",
        "styles": [f"{style}"],  # maybe we don't need to add all the tokens
        "seed": -1,
        "sampler_name": "DPM++ 2M",  # TODO: play with the results
        "batch_size": 1,
        "n_iter": 1,
        "steps": 30,
        "cfg_scale": 13,
        "width": 768,
        "height": 512,
        "restore_faces": "false",
        "negative_prompt": f"{negative_prompt}",
        # """
        # enabled: bool,
        # raw_divisions: str, raw_positions: str,
        # raw_weights: str, raw_end_at_step: int):"""
        "alwayson_scripts": {
            "Latent Couple extension": {
                "args": [
                    f"{latent_couple}",
                    "1:1,1:2,1:2",
                    "0:0,0:0,0:1",
                    "0.5,0.8,0.8",
                    30,
                ]
            }
        },
        # "script_name": "CensorScript",
        # "script_args": ['true','false'], #Pass the script its arguments as a list
        # "script_args": [('put_at_start','false'),('different_seeds','true')], #Pass the script its arguments as a list
        "save_images": "true",
        "override_settings": {
            "sd_model_checkpoint": "dreamlikeDiffusion10_10.ckpt [0aecbcfa2c]"
        },
    }

    def post_prompt(payload):
        return session.post(URL + "/sdapi/v1/txt2img", json=payload)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        ic(f"sending prompt: {prompt}")
        future = executor.submit(post_prompt, payload)
        executor.submit(poll_results_until_done)
        x = future.result()
    # x = session.post(URL + '/sdapi/v1/txt2img', json=payload)
    ic(x)
    if x.status_code != 200:
        raise Exception(f"API request failed: {x.text}")
    # check if the image wasn't filterd due to nsfw
    for i in range(0, len(x.json()["images"])):
        im_b64 = x.json()["images"][i]
        im = Image.open(BytesIO(base64.b64decode(im_b64)))
        # interrogate_image(img=im_b64)
        extrema = im.convert("L").getextrema()
        if not extrema == (0, 0):
            # im.show()
            date_folder = datetime.now().strftime("%Y-%m-%d")
            counter += 1
            now = datetime.now().strftime("%H%M%S")
            save_image(im, date_folder, f"image_{counter}_{now}.png")

            return f".\{date_folder}\image_{counter}_{now}.png"
        else:
            ic("Image completley black!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", type=str, default="", help="url for the api server")
    args = parser.parse_args()

    if args.url != "":
        URL = args.url
    else:
        get_service_urls()["sd"]
    # prompt = input("Enter prompt: ")
    # prompt = "A person stands in a cold stark landscape at twilight."
    # prompt = "I am again in my mom's house -city- and there is all this preparation going on  and i suddenly find out that a war is about to break out. THere are foreign soldiers and lots of guns around. We don't know the language but sounds like Arabic and my kids are trying to send a text message to my husband to ask for help without being caught ..."
    prompt = (
        "snowy landscape background AND two cats fighting each other AND a dog dancing"
    )
    # prompt = "an industrial warehouse pharmacy AND A person and Soraya's father are standing in front of an automatic door"
    send_to_sd(prompt)

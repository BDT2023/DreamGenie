import requests
from icecream import ic
from PIL import Image
import base64
from io import BytesIO
import argparse

URL = "https://db91-132-70-60-180.ngrok.io"

def send_to_sd(prompt):
    ic.disable()
    tokens = """
    ,expressive oil painting,whimsical atmosphere,amazing,artistic,vibrant,detailed,award winning, concept art, intricate details, realistic, Hyperdetailed, 8K resolution. Dramatic light, Octane render
    """  
    negative_prompt = """
    lowres, text, error, cropped, worst quality, low quality,jpeg artifacts, ugly, duplicate, morbid, mutilated, out of frame, extra fingers, mutated hands, poorly drawn hands,poorly drawn face, mutation, deformed, blurry,  bad proportions, extra limbs, cloned face, disfigured, gross proportions, dehydrated, bad anatomy,malformed limbs,
    missing arms, missing legs, extra arms, extra legs,fused fingers, too many fingers, long neck, username, watermark, signature
    """
    negative_prompt = ""
    payload = {
    "enable_hr": 'false',
    "denoising_strength": 0,
    "firstphase_width": 0,
    "firstphase_height": 0,
    "prompt": f'{prompt}',
    "styles": [
        "project_tokes"
    ],
    "seed": -1,
    "subseed": -1,
    "subseed_strength": 0,
    "seed_resize_from_h": -1,
    "seed_resize_from_w": -1,
    "sampler_name": "DPM++ 2M",
    "batch_size": 1,
    "n_iter": 1,
    "steps": 30,
    "cfg_scale": 7.5,
    "width": 512,
    "height": 512,
    "restore_faces": 'false',
    "tiling": 'false',
    "negative_prompt": f'{negative_prompt}',
    "eta": 0,
    "s_churn": 0,
    "s_tmax": 0,
    "s_tmin": 0,
    "s_noise": 1  
    }
    #{'prompt': 'A painting of a forest,oil paints','sampler_index':'DDIM','steps':'15'}
    x = requests.post(URL+'/sdapi/v1/txt2img',json = payload)
    ic(x)

    # check if the image wasn't filterd due to nsfw
    for i in range(0,len(x.json()['images'])):
        im = Image.open(BytesIO(base64.b64decode(x.json()['images'][i])))
        extrema = im.convert("L").getextrema()
        if not extrema == (0, 0):
            im.show()
        else:
            ic("Image completley black!")
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", type=str, default="", help="url for the api server")
    args = parser.parse_args()
    if args.url != "":
        URL = args.url
    #prompt = input("Enter prompt: ")
    prompt = "A painting of a forest,oil paints"
    send_to_sd(prompt)
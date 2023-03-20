import requests
from icecream import ic
from PIL import Image
import base64
from io import BytesIO
import argparse
from my_secrets import API_KEY
URL = ""


def get_url():
    global URL
    api_url = "https://api.ngrok.com/endpoints"
    headers = {'Authorization': f'Bearer {API_KEY}', 'Ngrok-Version': '2'}
    response = requests.get(api_url,headers=headers)
    if response.status_code != 200:
        raise Exception(f'API request failed: {response.text}')
    if len(response.json()['endpoints'])==0:
        raise Exception(f'No endpoints found')
    URL = response.json()['endpoints'][0]['public_url']
 
def check_style_api():
    response = requests.get(URL+'/sdapi/v1/prompt-styles')
    if response.status_code != 200:
        raise Exception(f'API request failed: {response.text}')
    for style in response.json():
        if style['name'] == 'project_tokens':
            return True
    return False

    

        
def send_to_sd(prompt):
    if URL == "":
        get_url()
        
    is_style = check_style_api() #check if the style is already added
    ic(is_style)
    tokens = ''
    negative_prompt = ''
    style = 'project_tokens'
    #ic.disable()
    if not is_style:
        tokens = """
        ,dream,by Salvador Dali,expressive oil painting,oil paints,whimsical atmosphere,amazing,artistic,vibrant,detailed,award winning, concept art, intricate details, realistic, Hyperdetailed, 8K resolution, Dramatic light
        """  
        negative_prompt = """
        lowres, text, error, cropped, worst quality, low quality,jpeg artifacts, ugly, duplicate, morbid, mutilated, out of frame, extra fingers, mutated hands, poorly drawn hands,poorly drawn face, mutation, deformed, blurry,  bad proportions, extra limbs, cloned face, disfigured, gross proportions, dehydrated, bad anatomy,malformed limbs,
        missing arms, missing legs, extra arms, extra legs,fused fingers, too many fingers, long neck, username, watermark, signature
        """
        style = ''
    
    #https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/API
    payload = {
    "enable_hr": 'false',
    "denoising_strength": 0,
    "firstphase_width": 0,
    "firstphase_height": 0,
    "prompt": f'{prompt+tokens}',
    "styles": [
        f'{style}' #maybe we don't need to add all the tokens
    ],
    "seed": -1,
    "subseed": -1,
    "subseed_strength": 0,
    "seed_resize_from_h": -1,
    "seed_resize_from_w": -1,
    "sampler_name": "DPM++ 2M", #TODO: play with the results
    "batch_size": 1,
    "n_iter": 1,
    "steps": 30,
    "cfg_scale": 13,
    "width": 768,
    "height": 512,
    "restore_faces": 'false',
    "tiling": 'false',
    "negative_prompt": f'{negative_prompt}',
    "script_name": "CensorScript",
    "script_args": ['true','false'], #Pass the script its arguments as a list
    #"script_args": [('put_at_start','false'),('different_seeds','true')], #Pass the script its arguments as a list
    "eta": 0, #TODO: check about the following parameters
    "s_churn": 0,
    "s_tmax": 0,
    "s_tmin": 0,
    "s_noise": 1
    #"override_settings": {"sd_model_checkpoint":'dreamlikeart-diffusion-1.0.ckpt [14e1ef5d]'}
    }

    x = requests.post(URL+'/sdapi/v1/txt2img',json = payload)

    ic(x)
    if x.status_code != 200:
        raise Exception(f'API request failed: {x.text}')
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
    else:
        get_url()
    #prompt = input("Enter prompt: ")
    prompt = "A painting of a forest with a river flowing through it."
    send_to_sd(prompt)
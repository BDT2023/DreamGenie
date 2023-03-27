import requests
from icecream import ic
URLS = {}  # dictionary of urls for each service (whisper, sd, etc)
from my_secrets import NGROK_API_KEY

'''
A method to populate the URLS dictionary with the urls for each service, so that we can use them later
'''
def get_service_urls():
    #ic.disable()
    global URLS
    api_url = "https://api.ngrok.com/tunnels"
    headers = {'Authorization': f'Bearer {NGROK_API_KEY}', 'Ngrok-Version': '2'}
    response = requests.get(api_url, headers=headers)
    if response.status_code != 200:
        raise Exception(f'API request failed: {response.text}')

    response = response.json()
    ic(response)
    tunnels = {}
    # iterate through the tunnels and get the public url, save it in the tunnels dictionary as a value, where the key is the tunnel session id
    for tunnel in response['tunnels']:
        tunnels[tunnel['tunnel_session']['id']] = (tunnel['public_url'])

    # a dictionary of credential ids and the corresponding  service name
    credential_id = {'cr_2NFNS09sQ2z2nMSTrIkn5ZsMz80': 'whisper',
                     'cr_2Ava69iIPmwypV1AyMlXHJ0MMvK': 'sd'}

    api_url = "https://api.ngrok.com/tunnel_sessions"
    headers = {'Authorization': f'Bearer {NGROK_API_KEY}', 'Ngrok-Version': '2'}
    response = requests.get(api_url, headers=headers)
    if response.status_code != 200:
        raise Exception(f'API request failed: {response.text}')
    tunnel_sessions = {}
    # match the tunnel session id with the credential id to use in locating the service name
    for tunnel in response.json()['tunnel_sessions']:
        tunnel_sessions[tunnel['id']] = (tunnel['credential']['id'])
    ic(tunnel_sessions)
    # iterate through the tunnel sessions and add the corresponding url to the URLS dictionary
    for t in tunnel_sessions.keys():
        URLS[credential_id[tunnel_sessions[t]]] = tunnels[t]
    ic(URLS)
    return URLS
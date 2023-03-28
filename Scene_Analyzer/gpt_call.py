import openai
from icecream import ic # for debugging https://github.com/gruns/icecream
from my_secrets import API_KEY_OPENAI
import os
import random as rand
import re
import pandas as pd
openai.api_key = API_KEY_OPENAI


def load_dreams(file_name='sample_texts_normalized.csv'):

    dream_list = pd.read_csv('..\\Scene_Analyzer\\sample_texts_normalized.csv', header=None)
    return dream_list


def get_samples():
    """
    Open the file with the manually separated scenes and return a list of the separated dreams.
    """
    with open("manual_scene_separation_data.txt", "r") as f:
        data = f.read()
        samples = data.split("###")[1:-1]
        counter = 1
        temp = []
        for counter,s in enumerate(samples):
            s = s.replace("IN:", "").strip()
            temp.append(s)
            #print(s)
            counter+=1
        return temp

def build_prompt(dream,command="Give short visual descriptions of the scenes in the following:",n = 0):
    """
    Build the prompt for the API call.
    n = number of examples of manual separation to pass to the model
    """
    examples = ""
    samples = get_samples()
     # build the examples string from the manual separation data
    for i in range(0,min(len(samples),n)):
        examples+=samples[i]
        examples+=os.linesep
    #print(examples)
    
    # If we are passing examples in the prompt, we need to add "Examples:" to the prompt, otherwise we don't.
    if examples!="":
        prompt = (f"{command}{os.linesep}Examples:\
    {examples.strip()}\
    {dream}") 
    else:
        prompt = (f"{command}{os.linesep}{dream}")
    #print(prompt)
    return prompt

def call_openai(dream,command="Give short visual descriptions of the scenes in the following:", test=True):
    """
    A function to call the OpenAI API and return a list of scenes resulting from the separation.
    
    dream = the dream to be analyzed
    command = the command to be passed to the model
    test = if True, the function will return a temporary text instead of calling the API
    """
    
    # temporary text to not spend tokens on the API
    if test == True:
        text = ''' Scene 1:
Output:  Two cats are facing each other, their fur bristling, their backs arched and their tails lashing. They are hissing and growling at each other, their ears flat against their heads. 
Scene 2:
    The two cats are now in mid-air, their claws outstretched, their fur standing on end. They are yowling and screeching, their eyes wide and their teeth bared.
        ########################'''
        return text.split('Scene')
    #model_engine = "text-curie-001"
    model_engine = "text-davinci-003"

    
    #API call to OpenAI GPT-3 using this schema:
    #https://beta.openai.com/docs/api-reference/completions/create
    generated_text ="\n\n1. The first scene is of a person on an escalator, with plastic squares and water rolling along the side. The person later learns that they are filters. \n\n2. The second scene is of a large church where a mardi gras parade is taking place inside while mass is being celebrated in peace. \n\n3. The third scene is of a clerk coming to collect a bill which has already been paid. He has with him graded papers from a school, but the person does not see their son's name."
    prompt = build_prompt(dream,command,n=3)
    completions = openai.Completion.create(
        engine=model_engine,
        prompt=prompt,
        max_tokens=256,
        n=1,
        stop=None, #optional token that stops the generation
        temperature=0.45, # not too high
    )

    # # Print the generated text
    generated_text = completions.choices[0].text
    # Append the generated text to the output file to keep track of the results.
    with open("out.txt", "a+") as f:
        f.write(f'Prompt: {prompt}')
        ic(f'Prompt: {prompt}')
        f.write(f'Output: {generated_text}')
        ic(f'Output: {generated_text}')
        f.write(os.linesep)
        f.write(f'########################')
        ic(f'########################')
        f.write(os.linesep)
    gen_list = generated_text.split("Scene")[1:]
    gen_list = [re.sub(r'[0-9]\: ',"",x) for x in gen_list]
    return gen_list


def separate():
    """
    return a random dream from the csv
    """
    # load the dreams from the csv
    dream_list = load_dreams()
    # show a random dream
    rand.seed(os.urandom(32))
    return dream_list[0][rand.randint(0, len(dream_list)-1)]


def separate_random():
    """
    load a random dream from the csv and return the call to openai scene separator on it.
    """
    text = separate()
    ic(text)
    return call_openai(text, test=False)
    


if __name__ == "__main__":
    # Load a random dream from the csv and call the openai scene separator on it.
    separate_random()
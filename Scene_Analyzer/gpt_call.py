import openai
from icecream import ic # for debugging https://github.com/gruns/icecream
from my_secrets import API_KEY_OPENAI
import os
import random as rand
import pandas as pd
openai.api_key = API_KEY_OPENAI


def load_dreams(file_name='sample_texts_normalized.csv'):

    dream_list = pd.read_csv('..\\Scene_Analyzer\\sample_texts_normalized.csv', header=None)
    return dream_list



def call_openai(text,command="Give short visual descriptions of the scenes in the following:"):
    #model_engine = "text-curie-001"
    text = ''' Scene 1:
    Output:  Two cats are facing each other, their fur bristling, their backs arched and their tails lashing. They are hissing and growling at each other, their ears flat against their heads. 

    Scene 2:
        The two cats are now in mid-air, their claws outstretched, their fur standing on end. They are yowling and screeching, their eyes wide and their teeth bared.

    ########################'''
    return text.split('Scene')
    model_engine = "text-davinci-003"
    #command = "Give short augmented visual descriptions of the scenes in the following:"
    '''
    API call to OpenAI GPT-3 using this schema:
    https://beta.openai.com/docs/api-reference/completions/create
    '''
    
    prompt = (f"""{command} {text}
    Scene 1:
    """)
    completions = openai.Completion.create(
        engine=model_engine,
        prompt=prompt,
        max_tokens=512,
        n=1,
        stop=None, #optional token that stops the generation
        temperature=0.45, # not too high
    )

    # Print the generated text
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
    gen_list = generated_text.split("Scene")
    return gen_list


def separate_random():
    # load the dreams from the csv
    dream_list = load_dreams()
    # show a random dream
    rand.seed(os.urandom(32))
    text = dream_list[0][rand.randint(0, len(dream_list)-1)]
    ic(text)
    return call_openai(text)
    


if __name__ == "__main__":
    # Load a random dream from the csv and call the openai scene separator on it.
    separate_random()
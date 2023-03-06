import openai
from icecream import ic
from my_secrets import API_KEY
import os
import random as rand
import pandas as pd
openai.api_key = API_KEY


def load_dreams(file_name='sample_texts_normalized.csv'):
    dream_list = pd.read_csv('G:\\Coding\\final project\\DreamGenie\\Scene_Analyzer\\sample_texts_normalized.csv', header=None)
    return dream_list



def call_openai(text,command="Give short visual descriptions of the scenes in the following:"):
    #model_engine = "text-curie-001"
    model_engine = "text-davinci-003"
    command = "Give short augmented visual descriptions of the scenes in the following:"
    '''
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
        stop=None,
        temperature=0.45,
    )

    # Print the generated text
    generated_text = completions.choices[0].text

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
    return generated_text

def separate_random():
    dream_list = load_dreams()
    # show a random dream
    rand.seed(os.urandom(32))
    text = dream_list[0][rand.randint(0, len(dream_list)-1)]
    ic(text)
    call_openai(text)


if __name__ == "__main__":
    separate_random()
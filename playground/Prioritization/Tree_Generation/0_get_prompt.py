import json, jsonlines
import re

instruction = '\n'.join([_.strip() for _ in open('prompt.txt').readlines()])

# raw_data = jsonlines.open("../../../released_data/hotpotqa__v2_test_random_500.jsonl", "r")
raw_data = jsonlines.open("../../../released_data/hotpotqa__v2_dev_random_100.jsonl", "r")

prompts = []
for item in raw_data:
    question = item["question_text"].strip()
    # Normalize spaces (e.g., replace multiple spaces between words with a single space).
    # Important since the llm repeat the question when answering, and i have seen it really affect its performance
    question = re.sub(r'\s+', ' ', question)
    prompt = instruction + '\nQ: ' + question + '\nA:'
    prompts.append(prompt)
    # print(prompt)
    # break    

# TODO:: ensure_ascii=False that is very important, before the prompt contained a lot of \u2200 unicode characters which made model hallucinates
json.dump(prompts, open('prompts.json', 'w'), indent = 2, ensure_ascii=False)
print(len(prompts))
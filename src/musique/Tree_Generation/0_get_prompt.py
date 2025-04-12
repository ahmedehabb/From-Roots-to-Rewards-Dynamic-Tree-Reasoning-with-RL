import json, jsonlines, re

instruction = '\n'.join([_.strip() for _ in open('prompt.txt').readlines()])

raw_data = jsonlines.open("../../../released_data/musique_ans__v2_test_random_500.jsonl", "r")
# raw_data = jsonlines.open("../../../released_data/musique_ans__v2_dev_random_100.jsonl", "r")

prompts = []
for item in raw_data:
    question = item['question_text'].strip()
    question = re.sub(r'\s+', ' ', question)
    prompt = instruction + '\nQ: ' + question + '\nA:'
    prompts.append(prompt)

json.dump(prompts, open('prompts.json', 'w'), indent = 2)
print(len(prompts))
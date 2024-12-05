import json, jsonlines

instruction = '\n'.join([_.strip() for _ in open('prompt.txt').readlines()])

raw_data = jsonlines.open("../../../released_data/hotpotqa__v2_test_random_500.jsonl", "r")

prompts = []
for item in raw_data:
    question = item["question_text"].strip()
    prompt = instruction + '\nQ: ' + question + '\nA:'
    prompts.append(prompt)
    # print(prompt)
    # break    

# TODO:: ensure_ascii=False that is very important, before the prompt contained a lot of \u2200 unicode characters which made model hallucinates
json.dump(prompts, open('prompts.json', 'w'), indent = 2, ensure_ascii=False)
print(len(prompts))
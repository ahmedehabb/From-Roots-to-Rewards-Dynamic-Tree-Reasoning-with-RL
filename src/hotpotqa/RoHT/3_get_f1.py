import json

import json
from tqdm import tqdm
from termcolor import colored
from evaluate import update_answer
import math
# import re

q2a = {}
raw_data = [json.loads(line.strip()) for line in open('../../../released_data/hotpotqa__v2_test_random_500.jsonl')]
# raw_data = [json.loads(line.strip()) for line in open('../../../released_data/hotpotqa__v2_dev_random_100.jsonl')]
q2dq = json.load(open("../Tree_Generation/question_decompositions.json"))
q2gold = {}
for item in raw_data:
    try:
        question = item['question_text'].strip()
        question = list(q2dq[question].keys())[0]
        # should add it later but run prompts again 
        # question = re.sub(r'\s+', ' ', question)
        gold = item['answers_objects'][0]['spans'][0]
        q_type = item["type"]
        q2gold[question] = (gold, q_type)
    except Exception as e:
        # If question not found in question_decompositions, this means something went wrong in the proccess maybe in json parsing in prev steps of tree generation
        print("ERROR CASE", e)

trees = json.load(open("results/test.json", "r"))
metrics = {}
for q_type in ["all", "bridge", "comparison"]:
    metrics[q_type] = {'em': 0, 'f1': 0, 'prec': 0, 'recall': 0, 'N': 0}

print(len(trees))
for i, tree in enumerate(trees):
    node = tree[-1]
    question, answer = node["question"], node["answer"][0]
    gold, q_type = q2gold[question]
    print("question", question)
    print("question type", q_type)
    print("answer", answer)
    print("gold", gold)
    print("------------------------------")
    q2a[question] = (i, answer, gold)
    em, f1, prec, recall = update_answer(metrics["all"], answer, gold)
    update_answer(metrics[q_type], answer, gold)

for q_type in ["all", "bridge", "comparison"]:
    print(q_type)
    print(metrics[q_type]['N'])

    for k in metrics[q_type].keys():
        metrics[q_type][k] /= metrics[q_type]['N']
    print(metrics[q_type])


json.dump(q2a, open("q2a.json", "w"), indent=2)
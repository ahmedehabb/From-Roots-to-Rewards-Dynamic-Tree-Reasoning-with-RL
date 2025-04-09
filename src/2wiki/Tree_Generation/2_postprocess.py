import json
from tqdm import tqdm
from termcolor import colored
import os

def findAllFile(base):
    for root, ds, fs in os.walk(base):
        for f in fs:
            if f == "predictions.json":
                continue
            yield f
base = './outputs'
data = []
for file_name in findAllFile(base):
    data += [json.loads(line.strip()) for line in open(os.path.join(base, file_name))]
    # data.update(json.load(open(os.path.join(base, file_name))))
print(len(data))
json.dump(data, open(os.path.join(base, 'predictions.json'), 'w'), indent = 2, ensure_ascii=False)

raw_data = json.load(open('outputs/predictions.json'))
error_questions = []
data = {}
for item in tqdm(raw_data):
    prompt = item['prompt']
    question = prompt.split('\n')[-2][len('Q: '):].strip()
    print(colored(question, 'red'))
    # print(item['response']['text'])
    try:
        # to match together.ai response
        qds = item['response']['message']['content'].strip()
        # qds = item['response']['text'].strip()
        if qds.endswith('.'):
            qds = qds[:-1]
        # print(qds)
        # if question.startswith('Who is the actress who plays the role of the Queen of Eng'):
        #     continue
        hqdt = json.loads(qds)
    except Exception as e:
        #TODO:: some jsons are not correctly formulated, especially the large ones !! see how can we solve them ? 
        print("Got an error", e)
        error_questions.append(question)
        hqdt = None
        continue
    



    tokens = item['response']['logprobs']['tokens']
    token_logprobs = item['response']['logprobs']['token_logprobs']
    if len(token_logprobs) == 0:
        continue

    if tokens[-1] == '.':
        token_logprobs = token_logprobs[:-1]
        # print(answer_logprobs)
    # else:
    #     answer_logprobs = token_logprobs[pos+6:]

    # print(tokens[pos+6:-1])
    
    st, ed = 0, 0
    pos = 0
    qds = {}
    for sub_question, qd in hqdt.items():
        # TODO:: some questions are decomposed "[]" so we should treat them as leaf nodes !
        if len(qd) == 0:
            print("got subquestion with empty decomposition !")
            continue

        while pos < len(tokens):
            #print("".join(tokens[max(pos-1, 0): min(pos+2, len(tokens))]))
            # This all depends on the tokenizer of the model you are using ? sadly maybe we can generalize it later to check if the token[pos] contains "[" or "]"
            # if "[" in tokens[pos] and ": [\"" in "".join(tokens[max(pos-1, 0): min(pos+2, len(tokens))]):
            # removed : from ': [\"' because sometimes the llm adds a newline before it

            # Problem in using this that llm can do it like ' [\n\"' by adding the new line after [ and then this parsing fails !!
            # if "[" in tokens[pos] and " [\"" in "".join(tokens[max(pos-1, 0): min(pos+2, len(tokens))]):

            # Lets keep it simple assuming we only have one [ in the response (TODO:: may need to check that later on)
            if "[" in tokens[pos]:
                st = pos
                break
            pos += 1
        while pos < len(tokens):
            # " ],\n" means we just decomposed one of them but still have some other subquestions
            # " ]\n" means its the last subquestion
            # if " ],\n" in tokens[pos] or " ]\n" in tokens[pos]:
            
            # if "]" in tokens[pos] and "\"]" in "".join(tokens[max(pos-1, 0): min(pos+2, len(tokens))]):

            if "]" in tokens[pos]:
                ed = pos
                break
            pos += 1
        
        print("tokens[st:ed + 1]", tokens[st:ed + 1])
        print("sub_question, qd", sub_question, qd)
        # TODO:: we usually get that problem when we had multiple arrays [] in the result, we should do the prompt in a correct way to prevent multiple decompositions 
        # and do only one layer of decomposition !!
        assert pos < len(tokens), question + ' | ' + str(st) + " | " + str(ed)
        qd_score = sum(token_logprobs[st:ed+1]) / len(token_logprobs[st:ed+1])
        
        # this is handling when the decomposition contains the same question
        if any([x == sub_question for x in qd]):
            qd, qd_score = [], None
        
        qds[sub_question] = (qd, qd_score)
        print(colored(sub_question, 'blue'))
        print("".join(tokens[st:ed+1]))
    
    
    # answer_logprob = sum(token_logprobs) / len(token_logprobs)
    # data[question] = [hqdt, answer_logprob]
    data[question] = qds

print(len(data))
print("error_questions", error_questions)
json.dump(data, open('question_decompositions.json', 'w'), indent = 2)
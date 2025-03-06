import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import requests
from Tree_Generation.openai_req import OpenaiReq
from Tree_Generation.together_req import TogetherReq

# openai_caller = OpenaiReq("./cache.jsonl")
togetherai_caller = TogetherReq()


def bm25_search(question, k):
    web = "http://localhost:1440"
    data = {
        "query": question,
        "k": k
    }
    for i in range(3):
        try:
            r = requests.get(web, json=data)
            if r.status_code != 200:
                raise Exception(r.text)
            return r.json()
        except Exception as e:
            print(e)

def postprocess(response):
    response = response[0]
    # response['finish_reason'] was eos ? why is that considered wrong and will output prompt too long ? shitty code 
    # if response == 'too long' or response['finish_reason'] != 'stop':
    #     return 'ERROR: prompt too long', -100, ""
    tokens = response['logprobs']['tokens']
    token_logprobs = response['logprobs']['token_logprobs']
    # added this here to be same as other api, better fix it form the source where we expect the response and before returning it back !! 
    response['text'] = response['message']['content']
    cot = response['text'].strip()
    if len(token_logprobs) == 0:
        return 'ERROR: empty output', -100, cot
    # TODO:: Why is this commented ? this leds into some outputs with unknown but returning probabilities.
    # if "Unknown" in cot:
    #     return "Unknow", sum(token_logprobs) / len(token_logprobs), cot
    pos = 0
    for idx, token in enumerate(tokens):
        if token.strip() == 'So' and idx + 1 <= len(tokens) and tokens[idx + 1].strip() == 'the' and idx + 2 <= len(tokens) and tokens[idx + 2].strip() == 'answer' and idx + 3 <= len(tokens) and tokens[idx + 3].strip() == 'is' and idx + 4 <= len(tokens) and tokens[idx + 4].strip() == ':':
            pos = idx
            break
    if tokens[-1] == '.':
        answer_logprobs = token_logprobs[pos+5:-1]
        answer = cot.split('So the answer is: ')[-1][:-1]
    else:
        answer_logprobs = token_logprobs[pos+5:]
        answer = cot.split('So the answer is: ')[-1]
    cot_process = cot.split('So the answer is: ')[0].strip()
    cot_process_logprobs = token_logprobs[:pos]
    if len(cot_process_logprobs) == 0:
        cot_process_logprob = -100
    else:
        cot_process_logprob = sum(cot_process_logprobs) / len(cot_process_logprobs)
    return answer, cot_process_logprob, cot, token_logprobs

def get_cb_answer(question):
    instruction = '\n'.join([_.strip() for _ in open('cb/prompt.txt').readlines()])
    prompt = instruction + '\nQ: ' + question + '\nA:'
    print(prompt)
    # response, tag = togetherai_caller.req2provider(prompt=prompt, max_tokens=None, stop='\n\n', use_cache=True)
    response, tag = togetherai_caller.req2provider(prompt=prompt, max_tokens=None, stop= None, use_cache=True)

    return postprocess(response)

def get_singlehop_ob_answer(question, topic_entities):
    instruction = '\n'.join([_.strip() for _ in open('ob/singlehop_prompt.txt').readlines()])
    k = 5
    contexts = []
    hist = set()
    r = bm25_search(question, k) 
    for datum in r:
        title, text = datum["title"], datum["paragraph_text"]
        stamp = title + text
        if not stamp in hist:
            hist.add(stamp)
            contexts.append([title, text])
        
    prompt = instruction + '\n'
    for idx, (title, text) in enumerate(contexts):
        prompt += '\n#' + str(idx + 1) + ' Wikipedia Title: ' + title + '\nText: ' + text 
    prompt += '\nQ: ' + question + '\nA:'
    print("single hop prompt", prompt)
    # response, tag = togetherai_caller.req2provider(prompt=prompt, max_tokens=None, stop='\n\n\n', use_cache=True)
    response, tag = togetherai_caller.req2provider(prompt=prompt, max_tokens=None, stop=None, use_cache=True)
    print("single hop response", response)
    return postprocess(response)

def aggregate_singlehop_answer(cb_answer, ob_answer):
    cb_ans, cb_score, cb_cot, cb_token_logprobs = cb_answer
    ob_ans, ob_score, ob_cot, ob_token_logprobs = ob_answer
    if "ERROR" in cb_ans or 'Unknown' in cb_ans:
        cb_ans, cb_score = "", -100
    if "ERROR" in ob_ans or 'Unknown' in ob_ans:
        ob_ans, ob_score = "", -100
    return max([(cb_ans, cb_score, cb_cot, cb_token_logprobs), (ob_ans, ob_score, ob_cot, ob_token_logprobs)], key=lambda x:x[1])

def get_multihop_ob_answer(node, tree):
    
    def is_descendant(a, b):
        while "fa" in tree[a]:
            a = tree[a]["fa"]
            if a == b:
                return True
        return False
    
    question = node["question"]
    instruction = '\n'.join([_.strip() for _ in open('ob/multihop_prompt.txt').readlines()])
    k = 5
    contexts = []
    hist = set()
    r = bm25_search(question, k)
    for datum in r:
        title, text = datum["title"], datum["paragraph_text"]
        stamp = title + text
        if stamp not in hist:
            hist.add(stamp)
            contexts.append([title, text])

    for idx in range(node["idx"]):
        if is_descendant(idx, node["idx"]):
            sub_question = tree[idx]["question"]
            r = bm25_search(sub_question, 3)
            for datum in r:
                title, text = datum["title"], datum["paragraph_text"]
                stamp = title + text
                if stamp not in hist:
                    hist.add(stamp)
                    contexts.append([title, text])
    
    prompt = instruction + '\n'
    for idx, (title, text) in enumerate(contexts):
        prompt += '\n#' + str(idx + 1) + ' Wikipedia Title: ' + title + '\nText: ' + text 
    prompt += '\nQ: ' + question + '\nA:'
    # response, tag = openai_caller.req2openai(prompt=prompt, max_tokens=256, stop='\n\n', use_cache=True)
    # response, tag = togetherai_caller.req2provider(prompt=prompt, max_tokens=None, stop='\n\n\n', use_cache=True)
    response, tag = togetherai_caller.req2provider(prompt=prompt, max_tokens=None, stop=None, use_cache=True)
    return postprocess(response)

def calculate_score1(cot_process_logprob, qd_score, sub_answer_scores):
    return cot_process_logprob + qd_score + sum(sub_answer_scores)

def calculate_score2(cot_process_logprob, qd_score, sub_answer_scores):
    return (cot_process_logprob + qd_score + sum(sub_answer_scores)) / (len(sub_answer_scores) + 2)

def aggregate_multihop_answer(node, tree):
    instruction = '\n'.join([_.strip() for _ in open('aggregate/prompt.txt').readlines()])
    question = node["question"]
    qd_score = node["qd_logprob"]
    context = ''
    sub_answer_scores = []
    for son_idx in node["sons"]:
        sub_question = tree[son_idx]["question"]
        sub_answer = tree[son_idx]["answer"][0]
        sub_answer_scores.append(tree[son_idx]["answer"][1])
        context += '\n' + sub_question + ' ' + sub_answer
    prompt = instruction + '\nContext:\n{}\n\nQuestion:\n{}\n\nAnswer:'.format(context, question)
    print(prompt)
    # response, tag = togetherai_caller.req2provider(prompt=prompt, max_tokens=None, stop='\n\n\n', use_cache=True)
    response, tag = togetherai_caller.req2provider(prompt=prompt, max_tokens=None, stop=None, use_cache=True)
    child_answer, cot_process_logprob, child_cot, child_token_logprobs = postprocess(response)
    
    child_ans = child_answer
    # TODO:: V.I Need to make sure log probs we got from children are != -100, since otherwise we will get bad results as -75, -50, -25 based on length ... 
    child_score = calculate_score2(cot_process_logprob, qd_score, sub_answer_scores)
    res1 = (child_ans, child_score, child_cot, child_token_logprobs)
    cb_ans, cb_score, cb_cot, cb_token_logprobs = node["cb_answer"]
    ob_ans, ob_score, ob_cot, ob_token_logprobs = node["ob_answer"]
    if "ERROR" in cb_ans or 'Unknown' in cb_ans:
        cb_ans, cb_score = "", -100
    if "ERROR" in ob_ans or 'Unknown' in ob_ans:
        ob_ans, ob_score = "", -100
    if "ERROR" in child_ans or "Unknown" in child_ans:
        child_ans, child_score = "", -100
    res2 = max([(cb_ans, cb_score, cb_cot, cb_token_logprobs), (ob_ans, ob_score, ob_cot, ob_token_logprobs), (child_ans, child_score, child_cot, child_token_logprobs)], key=lambda x:x[1])
    return res1, res2
    
        
    
if __name__ == "__main__":
    question = "Who is Joan Of Savoy's father?"
    r = bm25_search(question, k=5)
    for x in r:
        print(x["title"])
        print(x["paragraph_text"])
        print()
    
    
    


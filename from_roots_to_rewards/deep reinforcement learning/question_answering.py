import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), './search')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import requests
from transformers import AutoTokenizer
import random
from Tree_Generation.openai_req import OpenaiReq
from Tree_Generation.together_req import TogetherReq


serp_api_key = "" # put you serp API key here
os.environ["SERP_API_KEY"] = serp_api_key


# openai_caller = OpenaiReq("./cache.jsonl")
# TEMPERATURE = 0.7
# togetherai_caller = TogetherReq(cache_path=f"./cache_{TEMPERATURE}.jsonl")
togetherai_caller = TogetherReq()

tokenizer = AutoTokenizer.from_pretrained("gpt2")
random.seed(666)

def bm25_search(question, k, use_serpapi=False):
    web = "http://localhost:1439"
    data = {
        "query": question,
        "k": k
    }
    for i in range(3):
        try:
            r = requests.get(web, json=data)
            if r.status_code != 200:
                raise Exception(r.text)
            contexts = r.json()
            return contexts
        except Exception as e:
            print(e)

def postprocess(response):
    try: 
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
    except Exception as e:
        return 'ERROR: Failed to calculate', -100, "", []

def get_cb_answer(question):
    #return "Unknow", -100
    instruction = '\n'.join([_.strip() for _ in open('cb/prompt.txt').readlines()])
    prompt = instruction + '\nQ: ' + question + '\nA:'
    # print("get_cb_answer \n", prompt)
    # response, tag = togetherai_caller.req2provider(prompt=prompt, max_tokens=None, stop='\n\n', use_cache=True, temperature=TEMPERATURE)
    response, tag = togetherai_caller.req2provider(prompt=prompt, max_tokens=None, stop= None, use_cache=True) #, temperature=TEMPERATURE)

    return postprocess(response)

def get_singlehop_ob_answer(question, topic_entities):
    #return "Unknow", -100
    instruction = '\n'.join([_.strip() for _ in open('ob/singlehop_prompt.txt').readlines()])
    for k in range(5, 0, -1):
        contexts = []
        hist = set()
        # i have made serpapi off, since the quota is 100 only / month ! :(
        r = bm25_search(question, k, use_serpapi=False) 
        for datum in r:
            title, text = datum["title"], datum["text"]
            stamp = title + text
            if not stamp in hist:
                hist.add(stamp)
                contexts.append([title, text])
        for e in topic_entities:
            r = bm25_search(e, k, use_serpapi=False)
            for datum in r:
                title, text = datum["title"], datum["text"]
                stamp = title + text
                if stamp not in hist:
                    contexts.append([title, text])
                    hist.add(stamp)
        
        
        prompt = instruction + '\n'
        for idx, (title, text) in enumerate(contexts):
            prompt += '\n#' + str(idx + 1) + ' Wikipedia Title: ' + title + '\nText: ' + text 
        prompt += '\nQ: ' + question + '\nA:'
        if len(tokenizer(prompt).input_ids) + 256 <= 4097:
            break
    
    # print("single hop prompt", prompt)

    # response, tag = togetherai_caller.req2provider(prompt=prompt, max_tokens=None, stop='\n\n\n', use_cache=True, temperature=TEMPERATURE)
    response, tag = togetherai_caller.req2provider(prompt=prompt, max_tokens=None, stop=None, use_cache=True) #, temperature=TEMPERATURE)

    # print("get_singlehop_ob_answer \n", response)
    return postprocess(response)

def aggregate_singlehop_answer(cb_answer, ob_answer):
    cb_ans, cb_score, cb_cot, cb_token_logprobs = cb_answer
    ob_ans, ob_score, ob_cot, ob_token_logprobs = ob_answer
    if "ERROR" in cb_ans or 'Unknown' in cb_ans:
        cb_ans, cb_score = "", -100
    if "ERROR" in ob_ans or 'Unknown' in ob_ans:
        ob_ans, ob_score = "", -100
    return max([(cb_ans, cb_score, cb_cot, cb_token_logprobs), (ob_ans, ob_score, ob_cot, ob_token_logprobs)], key=lambda x:x[1])
    #return random.choice([(cb_ans, cb_score), (ob_ans, ob_score)])

def get_multihop_ob_answer(node, tree):
    #return "Unknow", -100
    question = node["question"]
    instruction = '\n'.join([_.strip() for _ in open('ob/multihop_prompt.txt').readlines()])
    k = 5
    for sub_k in range(3, 0, -1):
        contexts = []
        hist = set()
        r = bm25_search(question, k, use_serpapi=False)
        for datum in r:
            title, text = datum["title"], datum["text"]
            stamp = title + text
            if stamp not in hist:
                hist.add(stamp)
                contexts.append([title, text])
                
        # for son_idx in node["sons"]:
        #     sub_question = tree[son_idx]["question"]
        #     r = bm25_search(sub_question, sub_k, use_serpapi=True)
        #     for datum in r:
        #         title, text = datum["title"], datum["text"]
        #         stamp = title + text
        #         if stamp not in hist:
        #             hist.add(stamp)
        #             contexts.append([title, text])
                    
        # for son_idx in node["sons"][:-1]:
        #     sub_answer = tree[son_idx]["answer"][0]
        #     r = bm25_search(sub_answer, sub_k, use_serpapi=False)
        #     for datum in r:
        #         title, text = datum["title"], datum["text"]
        #         stamp = title + text
        #         if stamp not in hist:
        #             hist.add(stamp)
        #             contexts.append([title, text])
        
        prompt = instruction + '\n'
        for idx, (title, text) in enumerate(contexts):
            prompt += '\n#' + str(idx + 1) + ' Wikipedia Title: ' + title + '\nText: ' + text 
        prompt += '\nQ: ' + question + '\nA:'
        if len(tokenizer(prompt).input_ids) + 256 <= 4097:
            break
    # print("get_multihop_ob_answer \n", prompt)
    # response, tag = togetherai_caller.req2provider(prompt=prompt, max_tokens=None, stop='\n\n\n', use_cache=True, temperature=TEMPERATURE)
    response, tag = togetherai_caller.req2provider(prompt=prompt, max_tokens=None, stop=None, use_cache=True) #, temperature=TEMPERATURE)

    return postprocess(response)

def calculate_score1(cot_process_logprob, qd_score, sub_answer_scores):
    return cot_process_logprob + qd_score + sum(sub_answer_scores)

def calculate_score2(cot_process_logprob, qd_score, sub_answer_scores):
    return (cot_process_logprob + qd_score + sum(sub_answer_scores)) / (len(sub_answer_scores) + 2)

def calculate_score3(cot_process_logprob, qd_score, sub_answer_scores):
    return (cot_process_logprob + sum(sub_answer_scores)) / (len(sub_answer_scores) + 1)

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

    # print("aggregate_multihop_answer \n", prompt)
    # response, tag = togetherai_caller.req2provider(prompt=prompt, max_tokens=None, stop='\n\n\n', use_cache=True, temperature=TEMPERATURE)
    response, tag = togetherai_caller.req2provider(prompt=prompt, max_tokens=None, stop=None, use_cache=True) #, temperature=TEMPERATURE)
    child_answer, cot_process_logprob, child_cot, child_token_logprobs = postprocess(response)
    child_ans = child_answer
    # TODO:: V.I Need to make sure log probs we got from children are != -100, since otherwise we will get bad results as -75, -50, -25 based on length ... 
    child_score = calculate_score2(cot_process_logprob, qd_score, sub_answer_scores)
    res1 = (child_ans, child_score, child_cot, child_token_logprobs)
    # cb_ans, cb_score, cb_cot, cb_token_logprobs = node["cb_answer"]
    # ob_ans, ob_score, ob_cot, ob_token_logprobs = node["ob_answer"]
    # now we need to recompute them because they are not available by default
    cb_ans, cb_score, cb_cot, cb_token_logprobs = get_cb_answer(question)
    ob_ans, ob_score, ob_cot, ob_token_logprobs = get_singlehop_ob_answer(question, [])
    if "ERROR" in cb_ans or 'Unknown' in cb_ans:
        cb_ans, cb_score = "", -100
    if "ERROR" in ob_ans or 'Unknown' in ob_ans:
        ob_ans, ob_score = "", -100
    if "ERROR" in child_ans or "Unknown" in child_ans:
        child_ans, child_score = "", -100
    res2 = max([(cb_ans, cb_score, cb_cot, cb_token_logprobs), (ob_ans, ob_score, ob_cot, ob_token_logprobs), (child_ans, child_score, child_cot, child_token_logprobs)], key=lambda x:x[1])
    #res2 = random.choice([(cb_ans, cb_score), (ob_ans, ob_score), (child_ans, child_score)])
    return res1, res2
    
        
    
if __name__ == "__main__":
    question = "毛泽东"
    
    
    


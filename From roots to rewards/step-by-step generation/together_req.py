import openai
import requests
import time
import os
import json, jsonlines
from provider_req import ProviderReq

class TogetherReq(ProviderReq):
    # meta-llama/Llama-Vision-Free is free but doesnt support log_probs which are necessary for probtree
    # meta-llama/Meta-Llama-3-8B-Instruct-Turbo : bad answers but provide log_prob
    # meta-llama/Llama-3.2-3B-Instruct-Turbo ? bad answers tpp
    # meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo ? very nice but no log_prob !! 
    # meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo ? niceeee and log probs !! :) 
    # meta-llama/Meta-Llama-3-70B-Instruct-Lite ?
    def __init__(self, cache_path="./cache.jsonl", model="meta-llama/Meta-Llama-3-70B-Instruct-Lite"):
        super().__init__(url="http://127.0.0.1:10001/api/together/completion", cache_path=cache_path, model=model)

    def make_request(self, prompt, model, temperature, max_tokens, stop, logprobs):
        return requests.post(self.url, json={
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stop": stop,
            "logprobs": logprobs,
        })

    def parse_response(self, response_json):
        return response_json['choices']

if __name__ == "__main__":
    caller = TogetherReq()
    res = caller.req2provider("Hello, guess my name !", use_cache=True)
    print(res)
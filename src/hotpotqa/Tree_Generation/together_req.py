import openai
import requests
import time
import os
import json, jsonlines
from hotpotqa.Tree_Generation.provider_req import ProviderReq

class TogetherReq(ProviderReq):
    def __init__(self, cache_path="./cache.jsonl", model="meta-llama/Llama-Vision-Free"):
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
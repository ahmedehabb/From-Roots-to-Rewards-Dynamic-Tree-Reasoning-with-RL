import openai
import requests
import time
import os
import json, jsonlines



class ProviderReq:
    def __init__(self, url, cache_path="./cache.jsonl", model=None):
        self.url = url
        self.cache = {}
        self.cache_path = cache_path
        self.model = model  # Default model is set to None, but can be overridden in child classes
        if os.path.exists(self.cache_path):
            print("Loading cache from %s" % self.cache_path)
            with open(self.cache_path, "r") as f:
                for line in f:
                    datum = json.loads(line.strip())
                    self.cache[tuple(datum["input"])] = datum["response"]
            print("Loaded %d cached responses" % len(self.cache))

    def req2provider(self, prompt, temperature=0, max_tokens=None, stop=None, logprobs=1, use_cache=True):
        assert isinstance(prompt, str)
        input = (prompt, self.model, max_tokens, stop, logprobs)
        if use_cache and temperature == 0 and input in self.cache:
            return self.cache[input], True

        # Retry logic
        for i in range(3):
            try:
                response = self.make_request(prompt, self.model, temperature, max_tokens, stop, logprobs)
                if response.status_code != 200:
                    raise Exception(response.text)
                break
            except Exception as e:
                err_msg = str(e)
                print(e)
                if "reduce your prompt" in err_msg:  # this is because the input string is too long
                    return ['too long'], False

        try:
            response_json = response.json()
            response = self.parse_response(response_json)
        except:
            return ['error'], False

        # Cache the result if temperature is 0
        if temperature == 0:
            self.cache_result(input, response)

        return response, True

    def make_request(self, prompt, model, temperature, max_tokens, stop, logprobs):
        """To be implemented in the subclass"""
        raise NotImplementedError("Subclasses should implement this method")

    def parse_response(self, response_json):
        """To be implemented in the subclass"""
        raise NotImplementedError("Subclasses should implement this method")

    def cache_result(self, input, response):
        """Cache the result if it's not already cached"""
        if input not in self.cache:
            self.cache[input] = response
            with open(self.cache_path, "a") as f:
                f.write("%s\n" % json.dumps({"input": input, "response": response}))


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
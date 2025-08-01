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
            with open(self.cache_path, "r") as f:
                for line in f:
                    datum = json.loads(line.strip())
                    self.cache[tuple(datum["input"])] = datum["response"]

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

class OpenaiReq(ProviderReq):
    def __init__(self, cache_path="./cache.jsonl", model="text-davinci-003"):
        super().__init__(url="http://127.0.0.1:10001/api/openai/completion", cache_path=cache_path, model=model)

    def make_request(self, prompt, model, temperature, max_tokens, stop, logprobs):
        return requests.post(self.url, json={
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stop": stop,
            "logprobs": logprobs,
        })

    def parse_response(self, response_json):
        return response_json['choices']


if __name__ == "__main__":
    caller = OpenaiReq()
    res = caller.req2provider("你好", use_cache=True)
    print(res)
    
    
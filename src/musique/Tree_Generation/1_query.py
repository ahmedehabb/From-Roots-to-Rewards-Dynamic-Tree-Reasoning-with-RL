import json
import re
# from openai_req import OpenaiReq
from together_req import TogetherReq
import random
from tqdm import tqdm
import os
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor, as_completed
from termcolor import colored
from dotenv import load_dotenv
load_dotenv()
random.seed(42)

MAX_SPLIT = 64
STEP = 4

key_pool = os.getenv('TOGETHER_API_KEY').split(',')
NUM_WORKERS = len(key_pool)  # Match the number of workers to the number of clients
RETRY_LIMIT = 3

def query(rank, prompts):
    print('Process rank {} PID {} begin...'.format(rank, os.getpid()))
    # reqor = OpenaiReq()
    reqor = TogetherReq()
    queries = prompts[int(len(prompts) * rank / MAX_SPLIT) : int(len(prompts) * (rank + 1) / MAX_SPLIT)]
    try:
        fout = open('outputs/rank_{}.json'.format(rank), 'w')
        if rank == 0:
            bar = tqdm(range(len(queries) // STEP + 1))
        else:
            bar = range(len(queries) // STEP + 1)
        for idx in bar:
            inputs = queries[idx * STEP : (idx + 1) * STEP]
            if len(inputs) == 0:
                break
            gpt_results = []
            for prompt in inputs:
                success = False
                retries = 0
                while not success and retries < RETRY_LIMIT:
                    try:
                        # Attempt to call the LLM
                        result, tag = reqor.req2provider(prompt, max_tokens=None, stop=None, temperature=0.6)
                        gpt_results.append(result[0])
                        success = True
                    except Exception as e:
                        retries += 1
                        print(
                            f"Error encountered for prompt (rank {rank}, idx {idx}). Retrying ({retries}/{RETRY_LIMIT}).\nError: {e}"
                        )
                        if retries == RETRY_LIMIT:
                            print(f"Failed to process prompt after {RETRY_LIMIT} retries: {prompt}")
                            gpt_results.append({"error": f"Failed after {RETRY_LIMIT} retries", "prompt": prompt})
            for prompt, res in zip(inputs, gpt_results):
                # print(res)
                fout.write(json.dumps({'prompt': prompt, 'response': res}) + '\n')
                fout.flush()
        fout.close()
    except Exception as err:
        print(Exception, err)

if __name__=='__main__':
    prompts = json.load(open('prompts.json'))
    os.makedirs("outputs", exist_ok=False)
    # print("number of prompts: {}".format(len(prompts)))
    # print('Parent process %s.' % os.getpid())
    # p = Pool(MAX_SPLIT)
    # for i in range(MAX_SPLIT):
    #     p.apply_async(query, args=(i, prompts))
    # print('Waiting for all subprocesses done...')
    # p.close()
    # p.join()
    # print('All subprocesses done.')

    # Use ThreadPoolExecutor to process requests in parallel
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = []
        for i in range(MAX_SPLIT):
            futures.append(executor.submit(query, i, prompts))

        # Wait for all tasks to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error in task: {e}")

    print("Finished processing all ranks.")
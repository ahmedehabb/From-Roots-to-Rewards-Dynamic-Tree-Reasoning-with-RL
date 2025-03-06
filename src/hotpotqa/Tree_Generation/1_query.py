import json
import re
from openai_req import OpenaiReq
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
                # Passing max_tokens with None to prevent truncation of the prompt
                # stop = '\n\n' this stop is actually so bad sometimes !! i changed it to none
                # bec he might start the answer with "Here is the hierarchical question decomposition tree (HQDT) in JSON format for the given question: \n\n" and complete the json tree after
                result, tag = reqor.req2provider(prompt, max_tokens = None, stop = None)
                gpt_results.append(result[0])
            for prompt, res in zip(inputs, gpt_results):
                # print(res)
                fout.write(json.dumps({'prompt': prompt, 'response': res}, ensure_ascii = False) + '\n')
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

    # Process each rank sequentially
    # for i in range(MAX_SPLIT):
    #     query(i, prompts)  # Call query function to process each segment of prompts
    #     print(f'Finished processing rank {i}.')
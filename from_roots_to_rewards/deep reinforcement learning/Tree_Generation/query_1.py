# import json
# import re
# from openai_req import OpenaiReq
# from together_req import TogetherReq
# import random
# from tqdm import tqdm
# import os
# from multiprocessing import Pool
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from termcolor import colored
# from dotenv import load_dotenv
# load_dotenv()
# random.seed(42)

# MAX_SPLIT = 64
# STEP = 4

# key_pool = os.getenv('TOGETHER_API_KEY').split(',')
# NUM_WORKERS = len(key_pool)  # Match the number of workers to the number of clients

# def query(rank, prompts):
#     print('Process rank {} PID {} begin...'.format(rank, os.getpid()))
#     # reqor = OpenaiReq()
#     reqor = TogetherReq()
#     queries = prompts[int(len(prompts) * rank / MAX_SPLIT) : int(len(prompts) * (rank + 1) / MAX_SPLIT)]
#     try:
#         fout = open('outputs/rank_{}.json'.format(rank), 'w')
#         if rank == 0:
#             bar = tqdm(range(len(queries) // STEP + 1))
#         else:
#             bar = range(len(queries) // STEP + 1)
#         for idx in bar:
#             inputs = queries[idx * STEP : (idx + 1) * STEP]
#             if len(inputs) == 0:
#                 break
#             gpt_results = []
#             for prompt in inputs:
#                 # Passing max_tokens with None to prevent truncation of the prompt
#                 # stop = '\n\n' this stop is actually so bad sometimes !! i changed it to none
#                 # bec he might start the answer with "Here is the hierarchical question decomposition tree (HQDT) in JSON format for the given question: \n\n" and complete the json tree after
#                 result, tag = reqor.req2provider(prompt, max_tokens = None, stop = None)
#                 gpt_results.append(result[0])
#             for prompt, res in zip(inputs, gpt_results):
#                 # print(res)
#                 fout.write(json.dumps({'prompt': prompt, 'response': res}, ensure_ascii = False) + '\n')
#                 fout.flush()
#         fout.close()
#     except Exception as err:
#         print(Exception, err)

# if __name__=='__main__':
#     prompts = json.load(open('prompts.json'))
#     os.makedirs("outputs", exist_ok=False)
#     # print("number of prompts: {}".format(len(prompts)))
#     # print('Parent process %s.' % os.getpid())
#     # p = Pool(MAX_SPLIT)
#     # for i in range(MAX_SPLIT):
#     #     p.apply_async(query, args=(i, prompts))
#     # print('Waiting for all subprocesses done...')
#     # p.close()
#     # p.join()
#     # print('All subprocesses done.')

#     # Use ThreadPoolExecutor to process requests in parallel
#     with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
#         futures = []
#         for i in range(MAX_SPLIT):
#             futures.append(executor.submit(query, i, prompts))

#         # Wait for all tasks to complete
#         for future in as_completed(futures):
#             try:
#                 future.result()
#             except Exception as e:
#                 print(f"Error in task: {e}")

#     print("Finished processing all ranks.")

#     # Process each rank sequentially
#     # for i in range(MAX_SPLIT):
#     #     query(i, prompts)  # Call query function to process each segment of prompts
#     #     print(f'Finished processing rank {i}.')


import json
import os
from termcolor import colored
from dotenv import load_dotenv
from Tree_Generation.together_req import TogetherReq
# Uncomment the following if using OpenaiReq, but the default here is TogetherReq
# from openai_req import OpenaiReq

load_dotenv()

class PromptToTree:
    def __init__(self, output_dir='resampled_trees', output_file='query1_results.json', temperature=0.7, verbose=False):
        """
        Initializes the Prompt Processor for handling prompt-based requests.
        
        Args:
            output_dir (str): Directory where outputs will be stored.
            output_file (str): File where results will be appended.
        """
        self.script_dir = os.path.dirname(os.path.abspath(__file__))  # Directory of the script
        self.output_dir = os.path.join(self.script_dir, output_dir)  # Directory for outputs
        self.output_file = os.path.join(self.output_dir, output_file)  # Full path to the output file
        self.temperature = temperature  # Temperature for the API request
        self.verbose = verbose  # Verbosity flag

        # Ensure the output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        if verbose:
            print(colored(f"Output directory: {self.output_dir}", "green"))

        # Initialize the request handler (use TogetherReq or OpenaiReq)
        self.reqor = TogetherReq(cache_path=f"./cache_{self.temperature}.jsonl")

    def process_single_prompt(self, prompt: int):
        """
        Processes a single prompt, querying the API and appending the result to the output file.
        
        Args:
            prompt_index (int): The index of the prompt to process (0-based).
        """

        try:
            # Query API and fetch the result
            if self.verbose:
                print(f"Processing prompt: {prompt[:50]}...")
            result, tag = self.reqor.req2provider(prompt, max_tokens=None, stop=None, temperature=self.temperature)

            # Prepare the output dictionary
            output_entry = {
                "prompt": prompt,
                "response": result[0],  # The first result in the response
            }

            # Append the result to the output file
            self.save_result(output_entry)
            if self.verbose:
                print(colored(f"Successfully processed prompt!", "green"))
            return output_entry

        except Exception as e:
            print(colored(f"Error while processing prompt: {str(e)}", "red"))
    
    def save_result(self, output_entry: dict):
        """
        Appends a result to the output JSON file (newline-delimited).
        
        Args:
            output_entry (dict): The result to append, including 'prompt' and 'response'.
        """
        with open(self.output_file, 'a', encoding='utf-8') as outfile:
            outfile.write(json.dumps(output_entry, ensure_ascii=False) + "\n")
        
        if self.verbose:
            print(colored(f"Result saved to: {self.output_file}", "cyan"))


# import json
# from tqdm import tqdm
# from termcolor import colored
# import os

# def findAllFile(base):
#     for root, ds, fs in os.walk(base):
#         for f in fs:
#             if f == "predictions.json":
#                 continue
#             yield f
# base = './outputs'
# data = []
# for file_name in findAllFile(base):
#     data += [json.loads(line.strip()) for line in open(os.path.join(base, file_name))]
#     # data.update(json.load(open(os.path.join(base, file_name))))
# print(len(data))
# json.dump(data, open(os.path.join(base, 'predictions.json'), 'w'), indent = 2, ensure_ascii=False)

# raw_data = json.load(open('outputs/predictions.json'))

# data = {}
# for item in tqdm(raw_data):
#     prompt = item['prompt']
#     question = prompt.split('\n')[-2][len('Q: '):].strip()
#     print(colored(question, 'red'))
#     # print(item['response']['text'])
#     try:
#         # to match together.ai response
#         qds = item['response']['message']['content'].strip()
#         # qds = item['response']['text'].strip()
#         if qds.endswith('.'):
#             qds = qds[:-1]
#         # print(qds)
#         # if question.startswith('Who is the actress who plays the role of the Queen of Eng'):
#         #     continue
#         hqdt = json.loads(qds)
#     except Exception as e:
#         #TODO:: some jsons are not correctly formulated, especially the large ones !! see how can we solve them ? 
#         print("Got an error", e)
#         hqdt = None
#         continue
    



#     tokens = item['response']['logprobs']['tokens']
#     token_logprobs = item['response']['logprobs']['token_logprobs']
#     if len(token_logprobs) == 0:
#         continue

#     if tokens[-1] == '.':
#         token_logprobs = token_logprobs[:-1]
#         # print(answer_logprobs)
#     # else:
#     #     answer_logprobs = token_logprobs[pos+6:]

#     # print(tokens[pos+6:-1])
    
#     st, ed = 0, 0
#     pos = 0
#     qds = {}
#     for sub_question, qd in hqdt.items():
#         # TODO:: some questions are decomposed "[]" so we should treat them as leaf nodes !
#         if len(qd) == 0:
#             print("got subquestion with empty decomposition !")
#             continue

#         while pos < len(tokens):
#             #print("".join(tokens[max(pos-1, 0): min(pos+2, len(tokens))]))
#             # This all depends on the tokenizer of the model you are using ? sadly maybe we can generalize it later to check if the token[pos] contains "[" or "]"
#             # if "[" in tokens[pos] and ": [\"" in "".join(tokens[max(pos-1, 0): min(pos+2, len(tokens))]):
#             # removed : from ': [\"' because sometimes the llm adds a newline before it

#             # Problem in using this that llm can do it like ' [\n\"' by adding the new line after [ and then this parsing fails !!
#             # if "[" in tokens[pos] and " [\"" in "".join(tokens[max(pos-1, 0): min(pos+2, len(tokens))]):

#             # Lets keep it simple assuming we only have one [ in the response (TODO:: may need to check that later on)
#             if "[" in tokens[pos]:
#                 st = pos
#                 break
#             pos += 1
#         while pos < len(tokens):
#             # " ],\n" means we just decomposed one of them but still have some other subquestions
#             # " ]\n" means its the last subquestion
#             # if " ],\n" in tokens[pos] or " ]\n" in tokens[pos]:
            
#             # if "]" in tokens[pos] and "\"]" in "".join(tokens[max(pos-1, 0): min(pos+2, len(tokens))]):

#             if "]" in tokens[pos]:
#                 ed = pos
#                 break
#             pos += 1
        
#         print("tokens[st:ed + 1]", tokens[st:ed + 1])
#         print("sub_question, qd", sub_question, qd)
#         # TODO:: we usually get that problem when we had multiple arrays [] in the result, we should do the prompt in a correct way to prevent multiple decompositions 
#         # and do only one layer of decomposition !!
#         assert pos < len(tokens), question + ' | ' + str(st) + " | " + str(ed)
#         qd_score = sum(token_logprobs[st:ed+1]) / len(token_logprobs[st:ed+1])
        
#         # this is handling when the decomposition contains the same question
#         if any([x == sub_question for x in qd]):
#             qd, qd_score = [], None
        
#         qds[sub_question] = (qd, qd_score)
#         print(colored(sub_question, 'blue'))
#         print("".join(tokens[st:ed+1]))
    
    
#     # answer_logprob = sum(token_logprobs) / len(token_logprobs)
#     # data[question] = [hqdt, answer_logprob]
#     data[question] = qds

# print(len(data))
# json.dump(data, open('question_decompositions.json', 'w'), indent = 2)


import json
from termcolor import colored
from tqdm import tqdm
import os
import re

class PostProcessor:
    def __init__(self, output_dir='resampled_trees', output_file='single_question_decomposition.json', verbose=False):
        """
        Initialize the SingleOutputProcessor class for processing a single result.
        """
        self.script_dir = os.path.dirname(os.path.abspath(__file__))  # Directory of the script
        self.output_dir = os.path.join(self.script_dir, output_dir)  # Directory for outputs
        self.output_file = os.path.join(self.output_dir, output_file)  # Full path to the output file
        self.verbose = verbose  # Verbosity flag
        # Ensure the output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        if self.verbose:
            print(colored(f"Output directory: {self.output_dir}", "green"))
        pass
    
    def fix_unescaped_quotes_in_keys(self, json_string):
        """
        Fix unescaped quotes in JSON keys.
        This function specifically looks for keys between {" and ":, 
        and ensures all quotes are properly escaped.

        Args:
            json_string (str): A raw JSON string with potential unescaped quotes in keys.

        Returns:
            str: A fixed JSON string with properly escaped quotes in keys.
        """

        # Regex to match problematic keys: anything between {" and ":
        def replace_unescaped_key_quotes(match):
            # Extract the key from the regex match
            key = match.group(1)

            # Replace unescaped `"` inside the key with `\"`
            fixed_key = re.sub(r'(?<!\\)"', r'\\"', key)  # Only escape quotes not already escaped

            # Return the reconstructed key-value pair
            return f'{{"{fixed_key}":'

        # Apply the regex to find and fix keys
        fixed_json = re.sub(r'\{"(.*?)":', replace_unescaped_key_quotes, json_string)

        return fixed_json

    def process_item(self, item):
        """
        Process a single result generated by the previous script, extracting decompositions and token log probabilities.
        
        Args:
            item (dict): The result to process (generated by the first script). 
        
        Returns:
            tuple: A tuple containing the question and processed decomposition data.
        """
        prompt = item['prompt']
        question = prompt.split('\n')[-2][len('Q: '):].strip()  # Extract question
        if self.verbose:
            print(colored(f"Processing question: {question}", 'red'))

        try:
            # Handle the model's response structure (Together API's `message['content']`)
            qds = item['response']['message']['content'].strip()
            if qds.endswith('.'):
                qds = qds[:-1]
            # Fix unescaped quotes in keys
            qds = self.fix_unescaped_quotes_in_keys(qds)
            # Parse the JSON structure
            hqdt = json.loads(qds)  # Parse the hierarchical decomposition tree (JSON structure)
        except Exception as e:
            print(colored(f"Error parsing response: {e}", "red"))
            return question, None

        # Extract tokens and log probabilities from the LLM response
        tokens = item['response']['logprobs']['tokens']
        token_logprobs = item['response']['logprobs']['token_logprobs']

        # Skip if logprobs are missing
        if not token_logprobs:
            return question, None

        # Ignore the final period in tokens (if present)
        if tokens[-1] == '.':
            token_logprobs = token_logprobs[:-1]

        st, ed = 0, 0
        pos = 0
        qds_processed = {}  # Store decompositions and associated scores

        # Process each sub-question and decomposition
        for sub_question, qd in hqdt.items():
            if not qd:  # Skip empty decompositions
                if self.verbose:
                    print(colored("Got a sub-question with no decomposition!", "yellow"))
                continue

            # Locate decomposition tokens in the log probabilities
            while pos < len(tokens):
                if "[" in tokens[pos]:  # Detect start of decomposition tokens
                    st = pos
                    break
                pos += 1
                
            while pos < len(tokens):
                if "]" in tokens[pos]:  # Detect end of decomposition tokens
                    ed = pos
                    break
                pos += 1

            # Ensure valid token ranges
            assert pos < len(tokens), f"Invalid token position for question: {question} | {st} | {ed}"

            # Compute scores for the decompositions
            qd_score = sum(token_logprobs[st:ed + 1]) / len(token_logprobs[st:ed + 1])

            # Handle circular decomposition where the sub-question matches itself
            if any([x == sub_question for x in qd]):
                qd, qd_score = [], None  # Skip such cases

            qds_processed[sub_question] = (qd, qd_score)  # Save processed decomposition and score
            if self.verbose:
                print(colored(sub_question, 'blue'))
                print("Decomposition tokens:", "".join(tokens[st:ed + 1]))

        # Save the processed results to a file
        final_data = {
            question: qds_processed
        }
        self.save_to_file(final_data)
        return final_data

    def save_to_file(self, final_data):
        """
        Save the processed results for a single question to a JSON file.
        If the file already exists, append the new data without overwriting the previous content.

        Args:
            final_data (dict): The processed data to save.
        """
        # Try to load the existing file if it exists
        try:
            with open(self.output_file, 'r', encoding='utf-8') as infile:
                existing_data = json.load(infile)  # Load existing data
        except FileNotFoundError:
            print(colored(f"No existing file found. Creating a new file: {self.output_file}", "yellow"))
            existing_data = {}  # Start with empty data if the file doesn't exist

        # Merge the new data with the existing data
        for key, value in final_data.items():
            if key in existing_data:
                if self.verbose:
                    print(colored(f"Warning: Overwriting existing question: {key}", "red"))
            existing_data[key] = value  # Update or add new entries

        # Write the merged data back to the JSON file
        with open(self.output_file, 'w', encoding='utf-8') as outfile:
            json.dump(existing_data, outfile, indent=2, ensure_ascii=False)
        if self.verbose:        
            print(colored(f"Saved processed question to {self.output_file}.", "cyan"))


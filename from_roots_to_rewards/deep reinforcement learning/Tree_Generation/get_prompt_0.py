import json, jsonlines
import re

# instruction = '\n'.join([_.strip() for _ in open('prompt.txt').readlines()])

# # raw_data = jsonlines.open("../../../released_data/hotpotqa__v2_test_random_500.jsonl", "r")
# raw_data = jsonlines.open("../../../released_data/hotpotqa__v2_dev_random_100.jsonl", "r")

# prompts = []
# for item in raw_data:
#     question = item["question_text"].strip()
#     # Normalize spaces (e.g., replace multiple spaces between words with a single space).
#     # Important since the llm repeat the question when answering, and i have seen it really affect its performance
#     question = re.sub(r'\s+', ' ', question)
#     prompt = instruction + '\nQ: ' + question + '\nA:'
#     prompts.append(prompt)
#     # print(prompt)
#     # break    

# # TODO:: ensure_ascii=False that is very important, before the prompt contained a lot of \u2200 unicode characters which made model hallucinates
# json.dump(prompts, open('prompts.json', 'w'), indent = 2, ensure_ascii=False)
# print(len(prompts))

import os
class PromptGenerator:
    def __init__(self, instruction_file: str = 'prompt.txt'):
        """
        Initializes the Prompt Generator with caching.

        Args:
            instruction_file (str): Path to the file containing the instructions.
        """
        # To ensure the files is always in the same directory as this script
        self.script_dir = os.path.dirname(os.path.realpath(__file__))
        self.instruction_file = os.path.join(self.script_dir, instruction_file)

    def generate_prompt(self, question: str) -> str:
        """
        Generates a prompt for a single question.

        Args:
            question (str): The input question that needs to be processed.

        Returns:
            str: The generated prompt.
        """
        # Normalize the question
        normalized_question = re.sub(r'\s+', ' ', question.strip())

        # Read and prepare instruction text
        with open(self.instruction_file, "r", encoding="utf-8") as f:
            instruction = '\n'.join([line.strip() for line in f.readlines()])

        # Create the formatted prompt
        prompt = f"{instruction}\nQ: {normalized_question}\nA:"

        return prompt

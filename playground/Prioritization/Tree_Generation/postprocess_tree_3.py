# import json
# import re

# raw_data = json.load(open('question_decompositions-testset-1.json'))
# print(len(raw_data.keys()))

# def check(question):
#     # if '<1>' in question or '<2>' in question or '<3>' in question or '<4>' in question:
#     if re.search(r'<\d+>', question):
#         return True
# tree = {}
# for father in raw_data:
#     # print("----------------------------------------------------------------")
#     # print("father", father)
#     if check(father):
#         # print("checked father returned true", father)
#         print(father)
#         continue
#     qds = raw_data[father]
#     # print("qds", qds)
#     if qds is None:
#         continue
#     tree[father] = {}
#     for question in qds:
#         # print("question in qds", question)
#         if check(question):
#             # print("checked question returned true", question)
#             continue
#         # print("qds[question]", qds[question])
#         # print("qds[question][0]", qds[question][0])
#         if any([x == question for x in qds[question][0]]):
#             # print("any([x == question for x in qds[question][0]]) returned true")
#             # print("found !!!")
#             # exit(1)
#             tree[father][question] = [[], None]
#         else:
#             # print("any([x == question for x in qds[question][0]]) returned false")
#             tree[father][question] = qds[question]
#     # if len(qds[question]) > 3:
#     #     print(father)
#     #     print(qds[question])
#     #     print('haha')

# # json.dump(tree, open('valid_tree.json', 'w'), indent = 2)
# print(len(tree))
# question_decompositions = {}
# for father in tree:
#     qds = tree[father]
#     for q in qds:
#         if q not in question_decompositions:
#             question_decompositions[q] = qds[q]
#         else:
#             if question_decompositions[q] != qds[q]:
#                 print(question_decompositions[q])
#                 print(qds[q])
#             else:
#                 print('haha')

# json.dump(question_decompositions, open('tree-testset-1.json', 'w'), indent = 2)

# print(len(tree))

import json
import re
import os
from termcolor import colored

class TreeFatherChildrenProcessor:
    def __init__(self, output_dir="resampled_trees", output_file="tree-father-children.json"):
        """
        Initializes the TreeFatherChildrenProcessor, which processes all father-child trees
        and generates processed subtrees and subquestion decompositions.

        Args:
            output_dir (str): The directory for saving the processed tree files.
            output_file (str): The file name to save the processed father-child tree.
        """
        self.script_dir = os.path.dirname(os.path.abspath(__file__))  # Directory of this script
        self.output_dir = os.path.join(self.script_dir, output_dir)  # Output directory for trees
        self.output_file = os.path.join(self.output_dir, output_file)  # Save final output file
        
        # Ensure the output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        print(colored(f"Output directory: {self.output_dir}", "green"))

    @staticmethod
    def check(question):
        """
        Check if the question contains a specific invalid pattern `<N>`.

        Args:
            question (str): The question string to check.

        Returns:
            bool: True if the question contains `<N>`, else False.
        """
        return bool(re.search(r"<\d+>", question))  # Matches patterns like <1>, <2>, etc.

    def process_tree(self, raw_data):
        """
        Process a dictionary of father trees (each tree has questions and their decompositions).

        Args:
            raw_data (dict): The raw data where keys are father questions and values are trees.
                Example:
                {
                    "What is the capital of France?": {
                        "What is the population of France?": [["How many people live in France?"], -2.3],
                        "What is the largest city in France?": [["Which city is the largest geographically?"], -1.8]
                    }
                }

        Returns:
            dict: A processed tree where invalid questions are removed, and subquestions are validated.
        """
        tree = {}
        print(colored(f"Processing {len(raw_data)} father questions...", "blue"))
        for father in raw_data:
            qds = raw_data[father]  # Get the tree (questions and decompositions) for this father
            if self.check(father):  # Skip invalid father questions
                print(colored(f"Skipped invalid father: {father}", "yellow"))
                continue

            if qds is None:  # If no decompositions exist for this father
                continue

            # Initialize the tree structure for this father
            tree[father] = {}
            print(colored(f"Processing father question: {father}", "green"))

            for question in qds:
                if self.check(question):  # Skip invalid subquestions
                    print(colored(f"Skipped invalid subquestion: {question}", "yellow"))
                    continue

                # Handle circular decompositions (sub-question matching itself)
                if any([x == question for x in qds[question][0]]):
                    print(colored(f"Detected circular decomposition in: {question}", "magenta"))
                    tree[father][question] = [[], None]
                else:
                    tree[father][question] = qds[question]

        print(colored(f"Processed tree with {len(tree.keys())} valid father questions.", "green"))
        return tree

    def construct_question_decompositions(self, processed_tree):
        """
        Build a global question decompositions dictionary from all trees.

        Args:
            processed_tree (dict): The processed tree with validated questions and decompositions.

        Returns:
            dict: A global dictionary of questions and their decompositions.
        """
        question_decompositions = {}
        print(colored(f"Building question decompositions from processed tree...", "blue"))

        for father, qds in processed_tree.items():
            for question in qds:
                # Add unique subquestions or validate existing decompositions
                if question not in question_decompositions:
                    question_decompositions[question] = qds[question]
                else:
                    if question_decompositions[question] != qds[question]:  # Check consistency
                        print(colored(f"Inconsistent decomposition for question: {question}", "red"))
                        print(colored(f"Existing: {question_decompositions[question]}", "red"))
                        print(colored(f"New: {qds[question]}", "red"))
                    else:
                        print(colored(f"Duplicate (consistent) decomposition found for: {question}", "cyan"))

        print(colored(f"Constructed {len(question_decompositions.keys())} unique question decompositions.", "green"))
        return question_decompositions

    def save_tree(self, tree, question_decompositions):
        """
        Save the processed question decompositions to the output file without overwriting the previous content.

        Args:
            tree (dict): The processed father-child tree (not used in this method; kept for consistency).
            question_decompositions (dict): The global question decompositions dictionary to save.
        """
        # Try to load the existing data if the output file already exists
        try:
            with open(self.output_file, "r", encoding="utf-8") as infile:
                existing_data = json.load(infile)  # Load existing decompositions
        except FileNotFoundError:
            print(colored(f"No existing file found. Creating a new file: {self.output_file}", "yellow"))
            existing_data = {}  # Start with an empty dictionary

        # Merge the new question decompositions with the existing data
        for question, decomposition in question_decompositions.items():
            if question in existing_data:
                print(colored(f"Warning: Overwriting existing decomposition for question: {question}", "red"))
            existing_data[question] = decomposition  # Update or add the new decompositions

        # Write the updated data back to the file
        with open(self.output_file, "w", encoding="utf-8") as outfile:
            json.dump(existing_data, outfile, indent=2, ensure_ascii=False)
        print(colored(f"Saved updated question decompositions to '{self.output_file}'.", "cyan"))


    def run(self, raw_data):
        """
        Run the entire process: process trees, validate questions, and save results.

        Args:
            raw_data (dict): The raw input data containing father-child trees.
        """
        # Step 1: Process the father-child trees
        processed_tree = self.process_tree(raw_data)

        # Step 2: Build a global question decomposition dictionary
        question_decompositions = self.construct_question_decompositions(processed_tree)

        # Step 3: Save outputs
        self.save_tree(processed_tree, question_decompositions)

        # Step 4: Return the processed tree and question decompositions
        return question_decompositions

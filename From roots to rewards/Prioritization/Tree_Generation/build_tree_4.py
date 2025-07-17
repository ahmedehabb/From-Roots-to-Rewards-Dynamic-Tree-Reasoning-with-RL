# import json
# from collections import defaultdict

# # raw_data = [json.loads(line.strip()) for line in open('../../../released_data/hotpotqa__v2_test_random_500.jsonl')]
# raw_data = [json.loads(line.strip()) for line in open('../../../released_data/hotpotqa__v2_dev_random_100.jsonl')]
# q2sub_q = json.load(open("../Tree_Generation/tree.json"))
# q2dq = json.load(open("../Tree_Generation/question_decompositions.json"))
# trees = []

# def dfs(q, tree):
#     # we can have cycles !!!! we must detect them otherwise we will fall in infinite loop :( 
#     sons = []
#     for sub_q in q2sub_q.get(q, [[]])[0]:
#         son_idx = dfs(sub_q, tree)
#         sons.append(son_idx)
#     idx = len(tree)
#     tree.append({
#         "idx": idx,
#         "question_text": q,
#         "sons": sons,
#         "qd_logprob": q2sub_q.get(q, [[], None])[1]
#     })    
#     for son_idx in sons:
#         tree[son_idx]["fa"] = idx
#     return idx

# for item in raw_data:
#     question = item['question_text'].strip()
#     # just added this since we dont have answers for all 500 questions now, just some of them
#     try:
#         question = list(q2dq[question].keys())[0]
#     except:
#         continue
#     assert question in q2sub_q, question
#     tree = []
#     # just added this to overcome the cyclic problem for now
#     try:
#         dfs(question, tree)
#     except:
#         continue
#     trees.append(tree)

# json.dump(trees, open("trees.json", "w"), indent=2)
    

import json
from termcolor import colored
import os

class TreeDFSProcessor:
    """
    Processes a single tree (DFS traversal) for a given question from the provided dataset.
    The tree structure uses `father`-to-`sons` relationships to construct a directed graph.
    """

    def __init__(self, output_dir="resampled_trees", output_file="dfs_trees.json", verbose=False):
        """
        Initializes the TreeDFSProcessor class.

        Args:
            output_file (str): Path to save the constructed tree for a single question.
        """
        self.script_dir = os.path.dirname(os.path.abspath(__file__))  # Directory of the script
        self.output_dir = os.path.join(self.script_dir, output_dir)  # Directory for outputs
        self.verbose = verbose  # Verbosity flag

        # Ensure the output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        self.output_file = os.path.join(self.output_dir, output_file)  # Full path to the output file
        if self.verbose:
            print(colored(f"Output directory: {self.output_dir}", "green"))

    def dfs(self, q, tree, q2sub_q, visited):
        """
        Depth-First-Search (DFS) function to construct a tree for a given question.

        Args:
            q (str): The current question being processed.
            tree (list): The tree being constructed.
            q2sub_q (dict): A question-to-subquestions mapping (TreeFatherChildrenProcessor output).
            visited (set): A set to track visited questions (to prevent cycles).

        Returns:
            int: The index of the current node in the tree.
        """
        if q in visited:
            if self.verbose:
                print(colored(f"Cycle detected at question: {q}", "red"))
            return None  # Prevent infinite recursion in case of cycles
        
        visited.add(q)  # Mark the question as visited
        sons = []  # Collect children nodes (sub-questions)

        # Process sub-questions (if any) from q2sub_q
        for sub_q in q2sub_q.get(q, [[]])[0]:  # Sub-questions are at index 0 of the tuple
            son_idx = self.dfs(sub_q, tree, q2sub_q, visited)
            if son_idx is not None:
                sons.append(son_idx)

        # Create the current tree node
        idx = len(tree)  # The current node index based on tree size
        tree.append({
            "idx": idx,
            "question_text": q,
            "sons": sons,
            "qd_logprob": q2sub_q.get(q, [[], None])[1]  # Log probability of decomposition
        })

        # Assign the current node as the "father" (`fa`) of its children
        for son_idx in sons:
            tree[son_idx]["fa"] = idx

        visited.remove(q)  # Remove the question from the visited set after processing
        return idx

    def process_single_question(self, question, q2sub_q, q2dq):
        """
        Process a single question by constructing its tree using DFS.

        Args:
            question (str): The question to process (must be in raw_data).
            q2sub_q (dict): The output tree mapping from TreeFatherChildrenProcessor.
            q2dq (dict): The question-to-decomposition dictionary from PostProcessor.

        Returns:
            list: The constructed tree for the given question.
        """

        # Map the question using q2dq to match its decomposition key
        try:
            question = list(q2dq[question].keys())[0]  # Get standardized/mapped question
        except KeyError:
            print(colored(f"Question not found in decompositions: {question}", "red"))
            return []

        # Ensure the question exists in the q2sub_q structure
        if question not in q2sub_q:
            if self.verbose:
                print(colored(f"Question not found in sub-question tree: {question}", "red"))
            return []

        # Construct the tree using DFS
        if self.verbose:
            print(colored(f"Processing question: {question}", "green"))
        tree = []
        visited = set()  # Track visited nodes to prevent cycles
        try:
            self.dfs(question, tree, q2sub_q, visited)
        except Exception as e:
            print(colored(f"Error during tree construction for question '{question}': {e}", "red"))
            return []

        # Save the constructed tree to a file
        self.save_tree(tree)
        if self.verbose:
            print(colored(f"Final tree constructed for question '{question}'", "green"))
        
        # Return the constructed tree
        return tree

    def save_tree(self, tree):
        """
        Save the constructed tree to a JSON file without overwriting previous data.

        Args:
            tree (list): The constructed tree to save for a single question.
        """
        # Try to load the existing data if the output file already exists
        try:
            with open(self.output_file, "r", encoding="utf-8") as infile:
                existing_trees = json.load(infile)  # Load existing data
        except FileNotFoundError:
            print(colored(f"No existing file found. Creating a new file: {self.output_file}", "yellow"))
            existing_trees = []  # Start with an empty list if the file doesn't exist

        # Merge the new tree into the existing data
        existing_trees.append(tree)  # Append the new tree to the list of trees

        # Write the updated data back to the file
        with open(self.output_file, "w", encoding="utf-8") as outfile:
            json.dump(existing_trees, outfile, indent=2, ensure_ascii=False)
        if self.verbose:
            print(colored(f"Tree saved to '{self.output_file}'.", "cyan"))


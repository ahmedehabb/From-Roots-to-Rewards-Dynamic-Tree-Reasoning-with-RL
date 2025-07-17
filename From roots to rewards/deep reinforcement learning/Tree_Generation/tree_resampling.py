import os
import json
import random
from Tree_Generation.get_prompt_0 import PromptGenerator
from Tree_Generation.query_1 import PromptToTree
from Tree_Generation.postprocess_2 import PostProcessor
from Tree_Generation.postprocess_tree_3 import TreeFatherChildrenProcessor
from Tree_Generation.build_tree_4 import TreeDFSProcessor

class TreeResamplingPipeline:
    """
    Encapsulates the pipeline to resample a tree from an input question.
    Handles the complete process: Prompt generation -> Tree generation -> Post-processing -> Father-child processing -> DFS tree construction.
    """
    
    def __init__(self, verbose=False, use_cache=False, cache_file="resampled_trees/dfs_trees.json"):
        """
        Initialize the pipeline components.
        """
        self.verbose = verbose
        self.prompt_generator = PromptGenerator()
        self.prompt_to_tree = PromptToTree(verbose=verbose)
        self.post_processor = PostProcessor(verbose=verbose)
        self.father_child_processor = TreeFatherChildrenProcessor(verbose=verbose)
        self.dfs_processor = TreeDFSProcessor(verbose=verbose)
        self.use_cache = use_cache
        self.script_dir = os.path.dirname(os.path.realpath(__file__))
        self.cache_file = os.path.join(self.script_dir, cache_file)
        self.cache = {}
        if self.use_cache:
            self.load_cache()

    def load_cache(self):
        """
        Load the cache if use_cache is enabled.
        """
        # Read the data from the file
        with open(self.cache_file, "r") as file:
            data = json.load(file)

        # Initialize an empty cache
        self.cache = {}

        # Iterate over the data to populate the cache
        for group in data:
            for node in group:
                # Check if a node has the "sons" attribute, is a "father," and lacks the key "fa"
                if "sons" in node and isinstance(node["sons"], list) and "fa" not in node:
                    key = node["question_text"]
                    # Add the node to the list under the key (initialize list if not already present)
                    if key not in self.cache:
                        self.cache[key] = []
                    
                    # we need to add the group to the cache, so we can get a random one later
                    self.cache[key].append(group)

        # Print the self.cache for verification
        if self.verbose:
            print(self.cache)

    def clean_question(self, question: str) -> str:
        # Remove extra spaces by splitting and joining
        return " ".join(question.split())


    def resample_tree(self, question):
        """
        Resample a tree for a single input question.

        Args:
            question (str): The input question for which the tree will be resampled.

        Returns:
            list: The final tree constructed using DFS.
        """
        # First of all clean the question by removing extra spaces inside it
        question = self.clean_question(question)
        
        # Check if the question is already in the cache
        if self.use_cache and question in self.cache:
            # Return the cached tree if available, note that we save all the instances of the trees even if we got the same question
            # so we can return a random one
            return random.choice(self.cache[question])

        while True:
            try:
                # Step 1: Generate the prompt from the input question
                prompt = self.prompt_generator.generate_prompt(question)

                # Step 2: Generate the raw tree from the model using the prompt
                raw_tree = self.prompt_to_tree.process_single_prompt(prompt)

                # Step 3: Post-process the raw tree into a valid question decomposition
                post_processed_tree = self.post_processor.process_item(raw_tree)

                # Step 4: Run tree processing to handle father-child relationships
                father_child_tree = self.father_child_processor.run(post_processed_tree)

                # Step 5: Construct the final tree using DFS
                final_tree = self.dfs_processor.process_single_question(
                    question=question,
                    q2sub_q=father_child_tree,
                    q2dq=post_processed_tree,
                )

                # If final tree is empty, retry
                if not final_tree:
                    raise ValueError("Final tree is empty after processing.")

                # If using cache, save the final tree to the cache
                if self.use_cache:
                    # Check if the question is already in the cache
                    if question not in self.cache:
                        # Initialize the cache for this question
                        self.cache[question] = []
                    
                    # Append the final tree to the cache
                    self.cache[question].append(final_tree)

                    # Dont update the file here, since its updated in the processes not here

                # Return the final tree structure
                return final_tree
            except Exception as e:
                if self.verbose:
                    print(f"Error during tree resampling: {e}")
                # Retry the process in case of an error
                continue


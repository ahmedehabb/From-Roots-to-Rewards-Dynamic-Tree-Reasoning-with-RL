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
    
    def __init__(self):
        """
        Initialize the pipeline components.
        """
        self.prompt_generator = PromptGenerator()
        self.prompt_to_tree = PromptToTree()
        self.post_processor = PostProcessor()
        self.father_child_processor = TreeFatherChildrenProcessor()
        self.dfs_processor = TreeDFSProcessor()

    def resample_tree(self, question):
        """
        Resample a tree for a single input question.

        Args:
            question (str): The input question for which the tree will be resampled.

        Returns:
            list: The final tree constructed using DFS.
        """
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

        # Return the final tree structure
        return final_tree

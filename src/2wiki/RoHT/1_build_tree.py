import json
from collections import defaultdict

raw_data = [json.loads(line.strip()) for line in open('../../../released_data/2wikimultihopqa__v2_test_random_500.jsonl')]
# raw_data = [json.loads(line.strip()) for line in open('../../../released_data/2wikimultihopqa__v2_dev_random_100.jsonl')]
q2sub_q = json.load(open("../Tree_Generation/tree.json"))

trees = []
error_questions = []
def dfs(q, tree):
    # we can have cycles !!!! we must detect them otherwise we will fall in infinite loop :( 
    sons = []
    print(q)
    for sub_q in q2sub_q.get(q, [[]])[0]:
        son_idx = dfs(sub_q, tree)
        sons.append(son_idx)
    idx = len(tree)
    tree.append({
        "idx": idx,
        "question_text": q,
        "sons": sons,
        "qd_logprob": q2sub_q.get(q, [[], None])[1]
    })    
    for son_idx in sons:
        tree[son_idx]["fa"] = idx
    return idx

for item in raw_data:
    try:
        # just added this since we dont have answers for all 500 questions now, just some of them
        question = item['question_text'].strip()
    except:
        error_questions.append({"question_text": item['question_text'], "error": "No question"})
        continue
    if question not in q2sub_q:
        error_questions.append({"question_text": item['question_text'].strip(), "error": "No subquestions"})
        continue
    assert question in q2sub_q
    tree = []
    # just added this to overcome the cyclic problem for now
    try:
        dfs(question, tree)
    except:
        error_questions.append({"question_text": question, "error": "Cyclic"})
        continue
    trees.append(tree)

json.dump(trees, open("trees.json", "w"), indent=2)
print("Errors:", [{"question_text": item['question_text'], "error": item['error']} for item in error_questions])
    
    


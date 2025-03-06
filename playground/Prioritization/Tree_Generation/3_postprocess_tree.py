import json
import re

raw_data = json.load(open('question_decompositions-testset-1.json'))
print(len(raw_data.keys()))

def check(question):
    # if '<1>' in question or '<2>' in question or '<3>' in question or '<4>' in question:
    if re.search(r'<\d+>', question):
        return True
tree = {}
for father in raw_data:
    # print("----------------------------------------------------------------")
    # print("father", father)
    if check(father):
        # print("checked father returned true", father)
        print(father)
        continue
    qds = raw_data[father]
    # print("qds", qds)
    if qds is None:
        continue
    tree[father] = {}
    for question in qds:
        # print("question in qds", question)
        if check(question):
            # print("checked question returned true", question)
            continue
        # print("qds[question]", qds[question])
        # print("qds[question][0]", qds[question][0])
        if any([x == question for x in qds[question][0]]):
            # print("any([x == question for x in qds[question][0]]) returned true")
            # print("found !!!")
            # exit(1)
            tree[father][question] = [[], None]
        else:
            # print("any([x == question for x in qds[question][0]]) returned false")
            tree[father][question] = qds[question]
    # if len(qds[question]) > 3:
    #     print(father)
    #     print(qds[question])
    #     print('haha')

# json.dump(tree, open('valid_tree.json', 'w'), indent = 2)
print(len(tree))
question_decompositions = {}
for father in tree:
    qds = tree[father]
    for q in qds:
        if q not in question_decompositions:
            question_decompositions[q] = qds[q]
        else:
            if question_decompositions[q] != qds[q]:
                print(question_decompositions[q])
                print(qds[q])
            else:
                print('haha')

json.dump(question_decompositions, open('tree-testset-1.json', 'w'), indent = 2)

print(len(tree))
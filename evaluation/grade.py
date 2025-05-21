import json
import os
from collections import defaultdict
import matplotlib.pyplot as plt
categorys = ["aircraft", "cub", "dog", "flowers102", "food101", "vegfru"]
models = ["glm-4v-plus", "hunyuan-vision", "doubao_pro", "qwen-vl-max-2024-10-30", "step-1v","LLaVA_NEXT"]
# models = ["gpt4o"]
result = defaultdict(lambda: defaultdict(dict))
score_model = "gpt-4o-mini"
for category in categorys:
    json_root = f"./scores/{category}"
    for root, _, filenames in os.walk(json_root):
        for filename in filenames:
            model_name = filename.split(f"_{category}_score_{score_model}.jsonl")[0]
            print(model_name)
            if model_name not in models:
                continue
            json_path = os.path.join(root, filename)
            lines = open(json_path).readlines()
            score_ = 0
            item_score = 0
            fact_score = 0
            for line in lines:
                line = json.loads(line)
                score_ += ((float(line['Fact_accuracy_score']) + (float(line['Item_accuracy_score']))) / 2)
                fact_score += float(line['Fact_accuracy_score'])
                item_score += float(line['Item_accuracy_score'])
                # print(float(line['Item_accuracy_score']))
            cnt = len(lines)
            result[model_name][category]['final_score'] = score_ / (2.5*cnt) * 100
            result[model_name][category]['Item_accuracy'] = item_score / (2*cnt) * 100
            result[model_name][category]['Fact_accuracy'] = fact_score / (3*cnt) * 100

for category in categorys:
    for k in models:
        v = result[k]
        final_score = v[category]['final_score']
        Item_accuracy = v[category]['Item_accuracy']
        Fact_accuracy = v[category]['Fact_accuracy']
        print(k, category, '\t',f'final score: {final_score:.2f}', f'rec_score: {Item_accuracy:.2f}', f'fact_score: {Fact_accuracy:.2f}')
        
    
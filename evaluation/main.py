import json
import os
import argparse
from multiprocessing import Process
from PIL import Image
from models.gpt_api import AzureChat
from models.claude import chat

def grade(sample_list):
    for line in sample_list:
        image = line['image']
        question = line['question']
        reference = line['reference']
        answer = line['answer']
        name = line['name']
        prompt = f'''
## CONTEXT ##
You are strict grading expert who is good at scoring model answers given reference answers and questions.

## OBJECTIVE ##
According to the provided <<<reference>>> and question, <<<answer>>> is scored specifically scored from two dimensions: item_accuracy, fact_accuracy.

## Standard ##
Item_accuracy_score: 
0: The answer doesn't contain any item name in the picture or the item name is wrong compared with the reference answer.
1: The most coarse class name is right, but it is not spcific.
2: The item name is right and is consistent with the reference answer.

Fact_accuracy_score:
0: The factual part of the answer, except for the item name, is inconsistent with the reference answer.
1-2: The factual part of the answer, except for the item name, is partly inconsistent with the reference answer.
3: The factual part of the answer, except for the item name, is consistent with the reference answer.

## REQUEST ##
1. All item accuracy scores are within 0-2 points and Fact accuracy scores are within 0-3 points.
2. The reason must be given first and then the score.
3. The final score is the average of the two scores.
4. The score must be an integer.

## DETAILS ##
1. The item may exist other names, the similar expression is also acceptable.
2. The finer the recognition, the higher the score. For example, the score of boeing 747-300 is higher than boeing 747.

## RESPONSE ##
Grade the answer and give me the final answer with json format.
{{
    "Item_accuracy": xxx, # The reason of grading in terms of accuracy
    "Item_accuracy_score": xxx, # The score of accuracy
    "Fact_accuracy": xxx, # The reason of grading in terms of relevance,
    "Fact_accuracy_score": xxx, # The score of relevance
    "final_score": xxx, # The average of the scores
}}

<<<reference>>>
{reference}
<<<answer>>>
{answer}

## QUESTION ##
{question}

'''
        print(image)
        exit()
        result = Chat(prompt, image)
        # no check format!!!
        result = json.loads(result)
        print(result)
            
        save_dic = {
            'name': name,
            'question': question,
            'image': image
        }
        
        save_dic.update(result)
        
        with open(save_path, 'a') as f:
            f.write(json.dumps(save_dic, ensure_ascii=False) + '\n')
            f.flush()          
  

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--category', type=str, default="aircraft")
    parser.add_argument('--model_name', type=str, default="gemini")
    parser.add_argument('--dataset_root', type=str, default="./data/aircraft/")
    parser.add_argument('--score_model', type=str, default="gpt-4o-mini")
    parser.add_argument('--candicate_model_json', type=str, default="./demo/demo_aircraft.jsonl")
    
    args = parser.parse_args()
    category = args.category
    model_name = args.model_name
    score_model = args.score_model
    origin_path = args.candicate_model_json
    
    cpu_num = 1
    save_path = f"./evaluation/scores/{category}/{model_name}_{category}_score_{score_model}.jsonl"
    
    if 'gpt' in score_model:
        Chat = AzureChat(deployment_name=score_model)
    elif 'claude' in score_model:
        Chat = chat
    else:
        assert "No support evaluating model!!!"
        
    exist_names = set()
    if os.path.exists(save_path):
        exist_lines = open(save_path).readlines()
        exist_lines = [json.loads(line) for line in exist_lines]
        exist_names = set([line['name'] for line in exist_lines])
    
    
    lines = open(origin_path).readlines()
    
    sample_lists = [[] for _ in range(cpu_num)]
    for i, line in enumerate(lines):
        line = json.loads(line)
        sample_lists[i % cpu_num].append(line)
    
    processes = []
    for i in range(cpu_num):
        process = Process(target=grade, args=(sample_lists[i], ))
        processes.append(process)
        process.start()
    
    for proc in processes:
        proc.join()

        

import os
import json
# 通过 pip install volcengine-python-sdk[ark] 安装方舟SDK
# from zhipuai import ZhipuAI
from openai import OpenAI
from multiprocessing import Process
import base64
from collections import defaultdict
import io
import random
from PIL import Image
from mimetypes import guess_type
def local_image_to_data_url(image_path):
        # Guess the MIME type of the image based on the file extension
        mime_type, _ = guess_type(image_path)
        if 's3://' in image_path:
            try:
                img_bytes = client_aws.get(image_path)
            except Exception as e:
                print(e)
                exit()
            img_mem_view = memoryview(img_bytes)
            image = io.BytesIO(img_mem_view)
            with Image.open(image) as img:
                byte_tream = image
                if image_path.endswith(".webp"):
                    byte_tream = io.BytesIO()
                    img.save(byte_tream, format="jpeg")
                    mime_type = 'image/jpeg'
                
                base64_encoded_data = base64.b64encode(byte_tream.getvalue()).decode('utf-8')
        else:
            with open(image_path, "rb") as image_file:
                base64_encoded_data = base64.b64encode(image_file.read()).decode('utf-8')
            print('encode success!!!')
        # Construct the data URL
        return f"data:image/jpeg;base64,{base64_encoded_data}"

# 替换为您的模型推理接入点
# model="ep-20250104174226-hcpqj"
# model="ep-20241211122931-7dp47"

# 初始化Ark客户端，从环境变量中读取您的API Key
client = OpenAI(
    # api_key='a84c2954-0535-4333-ad1e-d799f74aa04e'
    api_key='sk-ZbG00ZPO2hPt9MGN2K4ZTGAKMsGddzegcWDHHp7GNYrypKgk',
    base_url="https://api.302.ai/v1/chat/completions"
)

def chat(question, image_path):
    response = client.chat.completions.create(
        # 指定您部署了视觉理解大模型的推理接入点ID
        model = "claude-3-5-sonnet-20241022",
        messages = [
            {
                "role": "user",  # 指定消息的角色为用户
                "content": [  # 消息内容列表
                    {"type": "text", "text": question},  # 文本消息
                    {
                        "type": "image_url",  # 图片消息
                        # 图片的URL，需要大模型进行理解的图片链接
                        "image_url": {
                            "url": local_image_to_data_url(image_path)
                        }
                    },
                ],
            }
        ],
    )

    return response.choices[0].message.content

def worker(sample_list):
    for line in sample_list:
        # info = json.dumps(line['content'])
        name = line['name']
        if name in exist_names:
            continue
        image = name2image[line['name']][0]['image']
        question = line['questions'][0] + " Please output the category name of the object firstly."
        result = chat(question, image)
        print(result)
        save_dic = {
            'name': name,
            'question': question,
            'answer': result
        }
        # line['result'] = result
        # line['score'] = 1 if line['class'].lower().replace("-", "").replace(" ", "") in result.lower().replace("-", "").replace(" ", "") else 0
        with open(save_path, 'a') as f:
            f.write(json.dumps(save_dic, ensure_ascii=False) + '\n')
            f.flush() 

if __name__ == "__main__":
    categorys = ["aircraft", "cub", "dog", "flowers102", "food101", "vegfru"]
    for category in categorys:
        print(category)
        dic_key = f'{category}_eval_options_4_each_1'
        if category == "dog":
            dic_key = 'stanforddog_eval_options_4_each_1'
        all_file_pth = "/mnt/afs/user/pangcong/paper/benchmark/test_dataset/all.json"
        data = json.load(open(all_file_pth))
        path_image = data[dic_key]['annotation']
        lines = open(path_image).readlines()
        name2image = defaultdict(list)
        for line in lines:
            line = json.loads(line)
            name2image[line['class']].append(line)
        
        save_path = f"/mnt/afs/user/pangcong/paper/benchmark/generate/results/{category}/claude_{category}_result_question_with_prefix.jsonl"
        exist_names = set()
        if os.path.exists(save_path):
            exist_lines = open(save_path).readlines()
            exist_lines = [json.loads(line) for line in exist_lines]
            exist_names = set([line['name'] for line in exist_lines])
        
        origin_path = f"/mnt/afs/user/pangcong/paper/benchmark/raw_json/{category}/questions.jsonl"
        lines = open(origin_path).readlines()
        cpu_num = 5
        sample_lists = [[] for _ in range(cpu_num)]
        for i, line in enumerate(lines):
            line = json.loads(line)
            sample_lists[i % cpu_num].append(line)
        
        processes = []
        for i in range(cpu_num):
            process = Process(target=worker, args=(sample_lists[i], ))
            processes.append(process)
            process.start()
        
        for proc in processes:
            proc.join()
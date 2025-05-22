import os
import json
from volcenginesdkarkruntime import Ark
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

client = Ark(
    api_key=''
    )

def chat(question, image_path):
    response = client.chat.completions.create(
        model = "xxx",
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question}, 
                    {
                        "type": "image_url",
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
        name = line['name']
        if name in exist_names:
            continue
        image = line['image']
        question = line['question']
        result = chat(question, image)
        
        save_dic = {
            'image': image,
            'name': name,
            'question': question,
            'reference': line['ref_answer'],
            'answer': result
        }
        with open(save_path, 'a') as f:
            f.write(json.dumps(save_dic, ensure_ascii=False) + '\n')
            f.flush() 
        exit()

if __name__ == "__main__":
    category = "cub"
    origin_path = f"benchmark/{category}_with_reference.jsonl"
    
    save_path = f"./results/{category}/doubao_{category}_result.jsonl"
    exist_names = set()
    if os.path.exists(save_path):
        exist_lines = open(save_path).readlines()
        exist_lines = [json.loads(line) for line in exist_lines]
        exist_names = set([line['name'] for line in exist_lines])
    
    
    lines = open(origin_path).readlines()
    cpu_num = 8
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
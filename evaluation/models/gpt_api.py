import base64
from collections import defaultdict
import io
import random
from PIL import Image
from openai import AzureOpenAI
from mimetypes import guess_type

# from aoss_client.client import Client
# client_aws = Client('~/aoss.conf')
client_aws = None


API_KEY = "xxx"
API_BASE = "xxx"
API_VERSION = 'xxx'

class AzureChat():
    def __init__(self, api_key=API_KEY, api_version=API_VERSION, deployment_name='gpt-4o-2024-11-20') -> None:
        self.client = AzureOpenAI(
            api_key = api_key,  
            api_version = api_version,
            base_url = f"{API_BASE}openai/deployments/{deployment_name}"
        )
        self.model = deployment_name
        
    # Function to encode a local image into data URL 
    def _local_image_to_data_url(self, image_path):
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
    
    def chat(self, prompt, img_path=None):
        if img_path is not None:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    # { "role": "system", "content": "" },
                    { "role": "user", "content": [  
                        { 
                            "type": "text", 
                            "text": prompt 
                        },
                        { 
                            "type": "image_url",
                            "image_url": {
                                "url": self._local_image_to_data_url(img_path)
                            }
                        }
                    ] } 
                ],
                max_tokens=2000 
            )
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    # { "role": "system", "content": "You are a helpful assistant." },
                    { "role": "user", "content": [  
                        { 
                            "type": "text", 
                            "text": prompt 
                        }
                    ] } 
                ],
                max_tokens=2000,
            )
        return response.choices[0].message.content

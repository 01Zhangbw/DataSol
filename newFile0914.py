import json
import requests
import concurrent.futures
import os
import time
from typing import List
from tqdm import tqdm
# API配置
API_KEYS = ["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", "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"]

URLS = ["http://127.0.0.1:8004", "http://127.0.0.1:8001", "http://127.0.0.1:8002", "http://127.0.0.1:8003"]
# 文件夹优先级
FOLDER_PRIORITIES = {"folder_0": 0, "folder_1": 1, "folder_2": 2, "folder_3": 3}
def call_interact_api(prompt, url, api_key, max_retries=5):
    data = {"text": prompt, "api_key": api_key}
    for attempt in range(max_retries):
        response = requests.post(url, data=json.dumps(data))
        if response.status_code == 200:
            api_response = response.json()["response"]
            if api_response is not None:
                return api_response
            else:
                print(f"Empty response received, retrying ({attempt + 1}/{max_retries})")
                time.sleep(2)  # Optional: wait for 2 seconds before the next attempt
        else:
            print(f"Request failed with status {response.status_code}")
    return None


def task_scheduler(input_prompts: List[str], folder_priority) -> List[str]:
    # Total number of prompts
    total_prompts = len(input_prompts)

    # Results placeholder
    results = [None] * total_prompts

    # Create ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        # Schedule tasks
        future_to_index = {
            executor.submit(call_interact_api, input_prompts[i], URLS[i % 4], API_KEYS[i % 4]): i
            for i in range(total_prompts)
        }

        # Collect results
        for future in concurrent.futures.as_completed(future_to_index):
            index = future_to_index[future]
            try:
                results[index] = future.result()
            except Exception as exc:
                print(f"Prompt {input_prompts[index]} generated an exception: {exc}")
                results[index] = None

    return results

def process_folder(folder_path):
    for f in os.listdir(folder_path):
        file_path = os.path.join(folder_path, f)

        if os.path.isdir(file_path):  # 检查是否是文件夹
            process_folder(file_path)  # 递归处理文件夹
        elif f.endswith(".json"):  # 检查是否是JSON文件
            with open(file_path) as j:
                data = json.load(j)

            unprocessed = [i for i in data if 'output' not in i]

            for i in tqdm(range(0, len(unprocessed), 20)):

                batch = unprocessed[i:i + 20]
                prompts = [item['input'] for item in batch]

                outputs = task_scheduler(prompts)

                for item, output in zip(batch, outputs):
                    item['output'] = output

                for item in data:
                    if 'output' not in item:
                        for processed in batch:
                            if item['input'] == processed['input']:
                                item['output'] = processed['output']

            with open(file_path, 'w') as j:
                json.dump(data, j, indent=4)


if __name__ == '__main__':
    process_folder("E:\\File")

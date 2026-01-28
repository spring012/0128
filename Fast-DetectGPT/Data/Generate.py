import json
import sseclient
import time
import random
from tqdm import tqdm
from pathlib import Path

class RetryableTextGenerator:
    def __init__(self, api_key, max_retries=5, initial_delay=1):
        self.api_key = api_key
        self.url = 'http://8.217.90.53:22021/chatstreamGkV2'
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.responses_file = Path('ChatGLM_Generation.json')
        self.failed_file = Path('failed_requests.json')
        self.load_existing_data()
    
    def load_existing_data(self):
        if self.responses_file.exists():
            with open(self.responses_file, 'r', encoding='utf-8') as f:
                self.responses = json.load(f)
        else:
            self.responses = []
            
        if self.failed_file.exists():
            with open(self.failed_file, 'r', encoding='utf-8') as f:
                self.failed_requests = json.load(f)
        else:
            self.failed_requests = []

    def generate_single_response(self, question_data, attempt=1):
        import requests
        
        question_id = question_data['id']
        if any(r['id'] == question_id for r in self.responses):
            return None
            
        data = {
            'modelid': 'ChatGLM',
            "websearch": "0",
            "conversationId": "",
            "message": f"请详细分析并回答以下问题：{question_data['question']}"
        }
        params = {'apiKey': self.api_key}
        
        try:
            response = requests.post(self.url, params=params, data=data, stream=True)
            client = sseclient.SSEClient(response)
            
            full_text = ""
            for event in client.events():
                chunk = json.loads(event.data)
                new_s = chunk['message']
                
                if new_s.startswith('assmdx[DONE]assmdx'):
                    break
                elif new_s.startswith('assmdx[Error]assmdx'):
                    raise Exception("API错误")
                else:
                    full_text += new_s
                    
            return {
                "id": question_id,
                "llm": "ChatGLM",
                "content": full_text,
                # "attempts": attempt
            }
            
        except Exception as e:
            if attempt < self.max_retries:
                delay = self.initial_delay * (2 ** (attempt - 1)) + random.uniform(0, 1)
                print(f"问题{question_id}处理失败(尝试 {attempt}/{self.max_retries}): {str(e)}")
                print(f"等待 {delay:.2f} 秒后重试...")
                time.sleep(delay)
                return self.generate_single_response(question_data, attempt + 1)
            else:
                print(f"问题{question_id}最终处理失败: {str(e)}")
                self.failed_requests.append({
                    "id": question_id,
                    "question": question_data['question'],
                    "error": str(e),
                    "attempts": attempt
                })
                return {
                "id": question_id,
                "llm": "ChatGLM",
                "content": "",
                # "attempts": attempt
            }
    
    def save_data(self):
        with open(self.responses_file, 'w', encoding='utf-8') as f:
            json.dump(self.responses, f, ensure_ascii=False, indent=2)
        
        if self.failed_requests:
            with open(self.failed_file, 'w', encoding='utf-8') as f:
                json.dump(self.failed_requests, f, ensure_ascii=False, indent=2)
    
    def process_questions(self, questions_file):
        with open(questions_file, 'r', encoding='utf-8') as f:
            questions = json.load(f)
        
        for question in tqdm(questions, desc="处理问题"):
            result = self.generate_single_response(question)
            if result:
                self.responses.append(result)
                if len(self.responses) % 5 == 0:
                    self.save_data()
            time.sleep(random.uniform(1, 2))  # 随机延迟避免请求过快
                
        self.save_data()
        print(f"处理完成: 成功 {len(self.responses)} 个, 失败 {len(self.failed_requests)} 个")

def main():
    API_KEY = 'assmdx_apikey_5e87655341884a84zC'
    generator = RetryableTextGenerator(API_KEY)
    generator.process_questions('/root/fast-detect-gpt/scripts/analysis_questions.json')

if __name__ == "__main__":
    main()
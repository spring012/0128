import random
import numpy as np
import torch
import os
import glob
import argparse
import json
import time
from model import load_tokenizer, load_model
from fast_detect_gpt import get_sampling_discrepancy_analytic

class ProbEstimator:
    # ProbEstimator类保持不变...
    def __init__(self, args):
        self.real_crits = []
        self.fake_crits = []
        for result_file in glob.glob(os.path.join(args.ref_path, '*.json')):
            with open(result_file, 'r') as fin:
                res = json.load(fin)
                self.real_crits.extend(res['predictions']['real'])
                self.fake_crits.extend(res['predictions']['samples'])
        print(f'ProbEstimator: total {len(self.real_crits) + len(self.fake_crits)} samples.')

    def crit_to_prob(self, crit):
        all_crits = np.array(self.real_crits + self.fake_crits)
        if all_crits.size == 0:
            raise ValueError("real_crits 和 fake_crits 均为空，无法计算概率。")
        sorted_offsets = np.sort(np.abs(all_crits - crit))
        if sorted_offsets.size <= 100:
            raise IndexError("数组大小不足，无法访问索引 100。")
        offset = sorted_offsets[100]
        cnt_real = np.sum((np.array(self.real_crits) > crit - offset) & (np.array(self.real_crits) < crit + offset))
        cnt_fake = np.sum((np.array(self.fake_crits) > crit - offset) & (np.array(self.fake_crits) < crit + offset))
        return cnt_fake / (cnt_real + cnt_fake) if (cnt_real + cnt_fake) > 0 else 0.0

def process_text(text, scoring_tokenizer, scoring_model, reference_tokenizer, reference_model, criterion_fn, prob_estimator, args):
    tokenized = scoring_tokenizer(text, truncation=True, return_tensors="pt", padding=True, return_token_type_ids=False).to(args.device)
    labels = tokenized.input_ids[:, 1:]
    with torch.no_grad():
        logits_score = scoring_model(**tokenized).logits[:, :-1]
        if args.reference_model_name == args.scoring_model_name:
            logits_ref = logits_score
        else:
            tokenized = reference_tokenizer(text, truncation=True, return_tensors="pt", padding=True, return_token_type_ids=False).to(args.device)
            assert torch.all(tokenized.input_ids[:, 1:] == labels), "Tokenizer is mismatch."
            logits_ref = reference_model(**tokenized).logits[:, :-1]
        crit = criterion_fn(logits_ref, logits_score, labels)
    
    prob = prob_estimator.crit_to_prob(crit)
    return crit, prob

# 主要修改 run 函数来处理多条文本
def run(args):
    # 加载模型
    scoring_tokenizer = load_tokenizer(args.scoring_model_name, args.dataset, args.cache_dir)
    scoring_model = load_model(args.scoring_model_name, args.device, args.cache_dir)
    scoring_model.eval()
    
    if args.reference_model_name != args.scoring_model_name:
        reference_tokenizer = load_tokenizer(args.reference_model_name, args.dataset, args.cache_dir)
        reference_model = load_model(args.reference_model_name, args.device, args.cache_dir)
        reference_model.eval()
    else:
        reference_tokenizer = scoring_tokenizer
        reference_model = scoring_model

    criterion_fn = get_sampling_discrepancy_analytic
    prob_estimator = ProbEstimator(args)

    # 读取输入JSON文件
    with open(args.input_file, 'r', encoding='utf-8') as f:
        data_list = json.load(f)

    # 记录总开始时间
    total_start_time = time.time()
    
    # 处理每个文本条目
    for data in data_list:
        start_time = time.time()
        
        text = data['content']
        try:
            crit, prob = process_text(
                text, 
                scoring_tokenizer, 
                scoring_model,
                reference_tokenizer,
                reference_model,
                criterion_fn,
                prob_estimator,
                args
            )
            
            execution_time = time.time() - start_time
            
            # 更新结果
            data['detection'] = {
                'result': '机器生成' if prob > 0.5 else '人工写作',
                'probability': float(prob),
                'criterion': float(crit),
                'execution_time': float(execution_time)
            }
            
            print(f"处理完成 ID {data['id']}: {data['detection']['result']}")
            
        except Exception as e:
            print(f"处理ID {data['id']}时出错: {str(e)}")
            data['detection'] = {
                'error': str(e)
            }

    total_time = time.time() - total_start_time

    # 保存结果
    output_file = args.input_file.replace('.json', '_detected.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data_list, f, ensure_ascii=False, indent=4)

    print(f'全部处理完成. 结果已保存到 {output_file}')
    print(f'总执行时间: {total_time:.2f} 秒')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--reference_model_name', type=str, default="gpt-j-6B")
    parser.add_argument('--scoring_model_name', type=str, default="gpt-j-6B")
    parser.add_argument('--dataset', type=str, default="xsum")
    parser.add_argument('--ref_path', type=str, default="/root/fast-detect-gpt/local_infer_ref")
    parser.add_argument('--device', type=str, default="cuda")
    parser.add_argument('--cache_dir', type=str, default="../cache")
    parser.add_argument('--input_file', type=str, required=True, help='Input JSON file path')
    parser.add_argument('--batch_size', type=int, default=1, help='Batch size for processing')
    args = parser.parse_args()

    run(args)
# def run(args):
#     # 加载模型
#     scoring_tokenizer = load_tokenizer(args.scoring_model_name, args.dataset, args.cache_dir)
#     scoring_model = load_model(args.scoring_model_name, args.device, args.cache_dir)
#     scoring_model.eval()
    
#     if args.reference_model_name != args.scoring_model_name:
#         reference_tokenizer = load_tokenizer(args.reference_model_name, args.dataset, args.cache_dir)
#         reference_model = load_model(args.reference_model_name, args.device, args.cache_dir)
#         reference_model.eval()
#     else:
#         reference_tokenizer = scoring_tokenizer
#         reference_model = scoring_model

#     criterion_fn = get_sampling_discrepancy_analytic
#     prob_estimator = ProbEstimator(args)

#     # 读取输入JSON文件
#     with open(args.input_file, 'r', encoding='utf-8') as f:
#         data = json.load(f)

#     # 处理每个文本
#     start_time = time.time()
    
#     text = data['content']
#     crit, prob = process_text(
#         text, 
#         scoring_tokenizer, 
#         scoring_model,
#         reference_tokenizer,
#         reference_model,
#         criterion_fn,
#         prob_estimator,
#         args
#     )
    
#     execution_time = time.time() - start_time
    
#     # 更新结果
#     data['result'] = '机器生成' if prob > 0.5 else '人工写作'
#     data['probability'] = float(prob)
#     data['criterion'] = float(crit)
#     data['execution_time'] = float(execution_time)

#     # 保存结果
#     with open(args.input_file, 'w', encoding='utf-8') as f:
#         json.dump(data, f, ensure_ascii=False, indent=4)

#     print(f'处理完成. 结果已保存到 {args.input_file}')
#     print(f'执行时间: {execution_time:.2f} 秒')

# if __name__ == '__main__':
#     parser = argparse.ArgumentParser()
#     parser.add_argument('--reference_model_name', type=str, default="gpt-j-6B")
#     parser.add_argument('--scoring_model_name', type=str, default="gpt-j-6B")
#     parser.add_argument('--dataset', type=str, default="xsum")
#     parser.add_argument('--ref_path', type=str, default="/root/fast-detect-gpt/local_infer_ref")
#     parser.add_argument('--device', type=str, default="cuda")
#     parser.add_argument('--cache_dir', type=str, default="../cache")
#     parser.add_argument('--input_file', type=str, required=True, help='Input JSON file path')
#     args = parser.parse_args()

#     run(args)
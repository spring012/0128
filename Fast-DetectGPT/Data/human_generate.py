import json

def process_text_file(input_file, output_file, start_id, chunk_size=None):
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # 去除多余的空白字符
    text = text.replace('\r', '')

    if chunk_size:
        # 按固定长度切分文本
        paragraphs = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    else:
        # 按段落分割
        paragraphs = text.split('\n\n')  # 根据实际情况调整分割符

    data = []
    current_id = start_id
    for paragraph in paragraphs:
        content = paragraph.strip()
        if content:
            item = {
                "id": current_id,
                "llm": "human",
                "content": content
            }
            data.append(item)
            current_id += 1

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"{output_file} 已生成，共包含 {len(data)} 条内容。")

def main():
    # 处理《钢铁是怎样炼成的》
    process_text_file(
        input_file='/root/fast-detect-gpt/scripts/钢铁是怎样炼成的.txt',
        output_file='钢铁是怎样炼成的.json',
        start_id=1,
        chunk_size=500  # 可以根据需要调整，每500字符一个内容块
    )

    # 处理《基督山伯爵》
    process_text_file(
        input_file='/root/fast-detect-gpt/scripts/基督山伯爵.txt',
        output_file='基督山伯爵.json',
        start_id=1001,
        chunk_size=500  # 可以根据需要调整，每500字符一个内容块
    )

if __name__ == "__main__":
    main()
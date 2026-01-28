# -*- encoding:utf-8 -*- 
import torch
from langchain_openai import ChatOpenAI
import time
import jieba
from langchain_community.vectorstores.chroma import Chroma
from langchain_community.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

prompt = """文本：{context}
可用词汇：{word}
问题：请选择上述可用词汇对上述文本进行改写，使其内容更加学术化。
要求：可选择词汇表外合适词汇，可适量附带成语或添加形容词，具有较低的AIGC生成率，改写后字数和原句子保持一致。
"""
llm = ChatOpenAI(
    model_name="gpt-3.5-turbo",
    openai_api_key="sk-MQyGjC2f9WExF4ZABb756c3590754eFeB752744483F35597",
    temperature=1,
    base_url = "https://fast.bemore.lol/v1"
)
embedding_model = HuggingFaceEmbeddings(
            model_name='',
            model_kwargs={"device": 'cuda'},
            encode_kwargs={"normalize_embeddings": True},
        )

small_retriever = Chroma(persist_directory='D:\EmbeddingDatabase\small_word_database',
                   embedding_function=embedding_model).as_retriever(search_kwargs={"k": 3})
big_retriever = Chroma(persist_directory='D:\EmbeddingDatabase\\big_word_database',
                   embedding_function=embedding_model).as_retriever(search_kwargs={"k": 3})

def aigc(text):
    chain = ChatPromptTemplate.from_template(prompt) | llm | StrOutputParser()
    sent = text.split('。')
    data = []
    for item in sent:
        if len(item) > 1 and item[-1] != ']':
            words = []
            for split_word in jieba.lcut(item, cut_all=False):
                if len(split_word) > 1:
                    words.append(split_word)
            
            small_retrieve_word = small_retriever.batch(words)
            big_retrieve_word = big_retriever.batch(words)
            select_words = ''
            for i in range(len(words)):
                for word in small_retrieve_word[i]:
                    select_words += word.page_content + '，'
                for word in big_retrieve_word[i]:
                    select_words += word.page_content + '，'
            
            data.append({'context': item + '。', 'word': select_words[:-1] + '。'})
    
    content = ''
    if len(data) != 0:
        result = chain.batch(data)
        for item in result:
            content += item
    return content

paper = torch.load('D:\debug\slow\server_lm\C3')
with open('example.txt', 'w') as file:
    for index, (key, value) in enumerate(paper[0].items()):
        if index == '3':
            break
        for subkey, subvalue in value.items():
            if subkey == 'only_one_part':
                for item in subsubvalue['text']:
                    # item = llm.invoke(prompt.format(context=item)).content
                    item = aigc(item)
                    print(item)
                    file.write(item)
                continue
            for subsubkey, subsubvalue in subvalue.items():
                for item in subsubvalue['text']:
                    # item = llm.invoke(prompt.format(context=item)).content
                    item = aigc(item)
                    print(item)
                    file.write(item)
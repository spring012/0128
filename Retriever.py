from Interface import RetrieverFramework, MAX_PROMPT_LENGTH, Locker, PaperInfoAll
from DataProcess import ReferenceDataBase, process_file
from AbstractReferenceSpider import AbstractReferenceSpider
from Global import IS_DEBUG

from langchain_community.vectorstores.chroma import Chroma
from langchain_core.runnables import chain
from langchain_openai import ChatOpenAI
# from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_core.prompts import ChatPromptTemplate
import time
from langchain_text_splitters import CharacterTextSplitter
from langchain_core.documents import Document
import torch
import threading
import re
import os
import json
from PaperSearch import PaperSearch

class Retriever(RetrieverFramework):
    def __init__(self, paper_info: PaperInfoAll, ref_db: ReferenceDataBase, retrieve_num: int, max_online_search_num: int, lockk) -> None:
        self.paperlock = lockk
        self.is_English = paper_info.isEnglish
        self.ouline = paper_info.outline
        self.user_files = paper_info.referenceFileList
        self.aiPercent = paper_info.aiPercent

        self.user_retrieve_num = int(retrieve_num * self.aiPercent / 10)
        self.local_retrieve_num = retrieve_num - self.user_retrieve_num

        self.embedding_model = ref_db.embedding_model
        # self.embedding_model = None
        self.max_online_search_num = max_online_search_num

        self.user_chapter_retrievers = self.create_user_retriever()
        self.url_proprietary_sentence_databse = self.create_url_database(keyword=paper_info.abstract[1])

        self.local_chapter_retriever = ref_db.embedding_database.as_retriever(search_kwargs={"k": self.local_retrieve_num}, search_type="mmr")
        self.full_chapter_retriever = ref_db.embedding_database.as_retriever(search_kwargs={"k": retrieve_num}, search_type="mmr")
        pass
    
    def __create_proprietary_databse_from_url(self, keywords: list):
        if len(keywords) == 1 and ';' in keywords[0]:
            keywords = keywords[0].split(';')
        search_reslt = Locker()
        search_string = []
        
        if IS_DEBUG:
            search_reslt.content = torch.load('search_reslt')
        else:
            for item in keywords:
                if self.is_English:
                    search_string.append(item)  # 直接使用英文关键词
                else:
                    search_string.append('KY=xls(\'' + item + '\')')  # 中文关键词格式化
            max_online_search_num = self.max_online_search_num if len(search_string) > self.max_online_search_num else len(search_string)

            def search_data_parallel(index: int):
                print('开始调用摘要检索爬虫')
                if self.is_English:
                    paper_search = PaperSearch(search_string[index])  
                    result = paper_search.get_info_list(5)  # 获取 5 篇

                    for item in result:
                        item.setdefault("abstract", "No abstract available.")  # 如果没有摘要，就填充默认值
                else:
                    result = AbstractReferenceSpider().search(search_string[index])
                    
                if result is None:
                    result = []

                search_reslt.lock.acquire()
                search_reslt.content.extend(result)
                print('结束调用摘要检索爬虫')
                search_reslt.lock.release()

            # def search_data_parallel(index: int): # 测试时用
            #     local_data_path = r"D:\full-pdfs\工商管理-最新发表论文倒序-数据库3_11\data"
            #     cache_file = os.path.join(local_data_path, f"cache_{search_string[index]}.txt")
                
            #     if os.path.exists(cache_file):
            #         print('使用缓存数据')
            #         search_reslt.lock.acquire()
            #         with open(cache_file, 'r', encoding='utf-8') as f:
            #             search_reslt.content.extend(json.loads(f.read()))
            #         search_reslt.lock.release()
            #     else:
            #         print('开始调用摘要检索爬虫')
            #         result = AbstractReferenceSpider().search(search_string[index])
            #         search_reslt.lock.acquire()
            #         search_reslt.content.extend(result)
            #         # 保存爬取结果到缓存
            #         os.makedirs(local_data_path, exist_ok=True)
            #         with open(cache_file, 'w', encoding='utf-8') as f:
            #             f.write(json.dumps(result, ensure_ascii=False))
            #         print('结束调用摘要检索爬虫')
            #         search_reslt.lock.release()
                
            threads = []
            for i in range(max_online_search_num):
                one_thread = threading.Thread(target=search_data_parallel, name=search_string[i], args=(i, ))
                threads.append(one_thread)
                one_thread.start()

            for one_thread in threads:
                one_thread.join()
        print('请求锁')
        self.paperlock.acquire()
        print('获得锁')
        # torch.save(search_reslt.content, 'search_reslt')
        proprietary_data = []

        for item in search_reslt.content:
            # title = re.sub('\n', '', item['title'])
            proprietary_data.append(Document(item['abstract'], metadata={'reference': item['reference'][3:]}))

        sentence_data = []
        for item in proprietary_data:
            sentences = item.page_content.split('。')
            for sentence in sentences:
                sentence_data.append(Document(sentence, metadata=item.metadata))
        proprietary_sentence_databse = Chroma.from_documents(sentence_data, self.embedding_model, collection_name='sen_' + str(time.time()))

        return proprietary_sentence_databse
    
    def create_url_database(self, keyword: str):
        if isinstance(keyword, str):
            keywords = re.sub('。', '', keyword)
            keywords = re.sub('[*]', '', keywords)
            if not self.is_English:
                keywords = re.sub(' ', '', keyword)

            keywords = keywords.split('：')
            if len(keywords) == 1:
                keywords = keywords[0].split(':')
            keywords = keywords[-1].split('；')

            if len(keywords) == 1:
                keywords = keywords[0].split('，')
            if len(keywords) == 1:
                keywords = keywords[0].split('、')
            if len(keywords) == 1:
                keywords = keywords[0].split(',')
        else:
            keywords = keyword
            print(keywords)
        

        url_proprietary_sentence_databse = self.__create_proprietary_databse_from_url(keywords)
        return url_proprietary_sentence_databse
    
    def create_user_retriever(self):
        user_chapter_retriever = {}
        all_texts = process_file(self.user_files)
        index = 1
        for chapter in self.ouline:
            if len(chapter.sub) == 0:
                file_texts = process_file(chapter.referenceFileList) + all_texts
                if len(file_texts) != 0:
                    user_chapter_retriever[chapter.title] = Chroma.from_texts(file_texts, self.embedding_model, collection_name='aa' + str(index)).as_retriever(search_kwargs={"k": self.user_retrieve_num}, search_type="mmr")
                    index += 1
            for subpart in chapter.sub:
                if len(subpart.sub) == 0:
                    file_texts = process_file(subpart.referenceFileList) + all_texts
                    if len(file_texts) != 0:
                        user_chapter_retriever[subpart.title] = Chroma.from_texts(file_texts, self.embedding_model, collection_name='aa' + str(index)).as_retriever(search_kwargs={"k": self.user_retrieve_num}, search_type="mmr")
                        index += 1
                for subsubpart in subpart.sub:
                    file_texts = process_file(subsubpart.referenceFileList) + all_texts
                    if len(file_texts) != 0:
                        user_chapter_retriever[subsubpart.title] = Chroma.from_texts(file_texts, self.embedding_model, collection_name='aa' + str(index)).as_retriever(search_kwargs={"k": self.user_retrieve_num}, search_type="mmr")
                        index += 1
        return user_chapter_retriever
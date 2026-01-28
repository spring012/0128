import torch
from langchain_community.llms import HuggingFacePipeline
from langchain.chains import RetrievalQA
from transformers import BitsAndBytesConfig, AutoModelForCausalLM, AutoTokenizer, GenerationConfig, pipeline
from langchain_openai import ChatOpenAI
# from Interface import LargeLanguageModel
from langchain_community.chat_models import ChatZhipuAI
import httpx
from abc import ABC, abstractmethod

class LargeLanguageModel(ABC):
    def __init__(self, llm_name:str, **kwargs) -> None:
        """
        model_name: 本地生成式模型路径
        作用: 加载大语言模型
        """
        self.__llm_name = llm_name
        self.llm = None
        self.llm_conserve = None
        self.llm_abstract = None
    
    @abstractmethod
    def init_pipline(self, **kwargs):
        """
        作用: 根据llm_name初始化模型
        """
        pass
            
    
    @abstractmethod
    def query(self, input_text:str, **kwargs) -> str:
        """
        intput_text: 向大语言模型输入的句子
        Return: 模型的回答
        作用: 向大模型输入input_text，并返回输出结果
        """
        pass

class Wrapper:
    def __init__(self, wrapped_class):
        self.wrapped_class = wrapped_class

    def __getattr__(self, attr):
        original_func = getattr(self.wrapped_class, attr)

        def wrapper(*args, **kwargs):
            print(f"Calling function: {attr}")
            print(f"Arguments: {args}, {kwargs}")
            result = original_func(*args, **kwargs)
            print(f"Response: {result}")
            return result

        return wrapper
    
class OnlineModel(LargeLanguageModel):
    def __init__(self, llm_name:str) -> None:
        """
        model_name: 本地生成式模型路径
        """
        self.api_key = ['sk-MQyGjC2f9WExF4ZABb756c3590754eFeB752744483F35597',
                        'sk-mwTltOqYaGJGK2m143Be5c624780415b93017bE91cBb58D2',
                        'sk-b5qJs6cWIZ6YyAWQC4Fa49Fe6506463b98D2A20863De69Dd',
                        'sk-kxFwDVyBcUdpbZEyB0C3E3903084484e87Fa11A5E286B6C4',
                        'sk-JHM79ZutIvLg5DLcBf689216Db6b4446Ab0663BeB61b1c9b',
                        'sk-kFwihnlBAuTgfcZc5d183312767648Ef88C58eFa2bA07b80',
                        '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',
                        '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']

        self.llm_name = llm_name
        self.llm_abstract, self.llm = self.init_pipline()
    
    # reference: http代理服务器搭建 https://blog.csdn.net/chaishen10000/article/details/134023796
    # reference: https://blog.csdn.net/qq_40337012/article/details/124950080
    # reference: https://blog.csdn.net/DaiKeKun/article/details/90692962
    def init_pipline(self):
        """llm_abstract_pipline = ChatOpenAI(
                # model_name="gpt-4-turbo",
                model_name="gpt-4o-mini",
                openai_api_key=self.api_key[5],
                temperature=1.0,
                base_url = "https://api.oaipro.com/v1",
                # http_client=httpx.Client(proxies="http://8.217.90.53:3128")
            )"""
        """llm_abstract_pipline = ChatOpenAI(
                # model_name="gpt-4-turbo",
                model_name="openai/gpt-4o-mini",
                openai_api_key=self.api_key[7],
                temperature=1.0,
                base_url = "https://openrouter.ai/api/v1",
                # http_client=httpx.Client(proxies="http://8.217.90.53:3128")
            )"""
        """llm_abstract_pipline = ChatZhipuAI(
                model="GLM-4-Plus",
                zhipuai_api_key="e9f82f9314ae409281847df47f99ce13.lrU8pA2cfmFyUtKZ",
            )"""
        llm_abstract_pipline = ChatOpenAI(
                model_name="gpt-4o-mini",
                openai_api_key="sk-maCJIs9iUQ9DedFByFeJAhoglC5qL3MeCgmxoCsHThHAdQbx",
                temperature=1.0,
                base_url = "https://api.deerapi.com/v1",
            )
        
        if self.llm_name == 'GPT3.5':
            """llm_pipline = ChatOpenAI(
                model_name="gpt-3.5-turbo",
                openai_api_key=self.api_key[5],
                temperature=1.0,
                base_url = "https://api.oaipro.com/v1",
                # http_client=httpx.Client(proxies="http://8.217.90.53:3128")
            )"""
            """llm_pipline = ChatOpenAI(
                model_name="openai/gpt-4o-mini",
                openai_api_key=self.api_key[7],
                temperature=1.0,
                base_url = "https://openrouter.ai/api/v1",
                # http_client=httpx.Client(proxies="http://8.217.90.53:3128")
            )"""
            """llm_pipline = ChatZhipuAI(
                model="GLM-4-Plus",
                zhipuai_api_key="e9f82f9314ae409281847df47f99ce13.lrU8pA2cfmFyUtKZ",
            )"""
            llm_pipline = ChatOpenAI(
                model_name="gpt-4o-mini",
                openai_api_key="sk-maCJIs9iUQ9DedFByFeJAhoglC5qL3MeCgmxoCsHThHAdQbx",
                temperature=1.0,
                base_url = "https://api.deerapi.com/v1",
            )
            # reference: https://github.com/langchain-ai/langchain/discussions/6511
            # debug 网络错误信息可以打开下面这行代码
            # llm_abstract_pipline.client = Wrapper(llm_pipline.client)
            """llm_pipline = ChatOpenAI(
                model_name="XVERSE-13B-2",
                openai_api_key='9kMHStM89gnFWNfwJxsF5Y3dxF92pLeu',
                base_url = "https://api.xverse.cn/v1"
            )"""
        elif self.llm_name == 'GPT4.0':
            llm_pipline = ChatOpenAI(
                model_name="gpt-4-turbo-preview",
                openai_api_key=self.api_key[0],
                temperature=1.0,
                base_url = "https://fast.bemore.lol/v1"
            )
        elif self.llm_name == 'Deepseek-Chinese':
            llm_pipline = ChatOpenAI(
                model_name="deepseek-chat",
                openai_api_key="sk-maCJIs9iUQ9DedFByFeJAhoglC5qL3MeCgmxoCsHThHAdQbx",
                temperature=2.0,
                base_url = "https://api.deerapi.com/v1",
            )
            # llm_pipline = ChatOpenAI(
            #     model_name="deepseek-chat",
            #     openai_api_key="sk-3bfb89dca6e045fa9cb84a775a303d39",
            #     temperature=2.0,
            #     base_url = "https://api.deepseek.com"
            # )
        elif self.llm_name == 'Deepseek-English':
            llm_pipline = ChatOpenAI(
                model_name="deepseek-chat",
                openai_api_key="sk-maCJIs9iUQ9DedFByFeJAhoglC5qL3MeCgmxoCsHThHAdQbx",
                temperature=1.0,
                base_url = "https://api.deerapi.com/v1",
            )
            # llm_pipline = ChatOpenAI(
            #     model_name="deepseek-chat",
            #     openai_api_key="sk-3bfb89dca6e045fa9cb84a775a303d39",
            #     temperature=1.0,
            #     base_url = "https://api.deepseek.com"
            # )
        elif self.llm_name == 'Zhipu-Chinese':
            llm_pipline = ChatOpenAI(
                model_name="glm-4-air",
                openai_api_key="e9f82f9314ae409281847df47f99ce13.lrU8pA2cfmFyUtKZ",
                temperature=1.0,
                base_url = "https://open.bigmodel.cn/api/paas/v4/"
            )
        elif self.llm_name == 'Zhipu-English':
            llm_pipline = ChatOpenAI(
                model_name="glm-4-air",
                openai_api_key="e9f82f9314ae409281847df47f99ce13.lrU8pA2cfmFyUtKZ",
                temperature=1.0,
                base_url = "https://open.bigmodel.cn/api/paas/v4/"
            )
        elif self.llm_name == 'Doubao-Chinese':
            llm_pipline = ChatOpenAI(
                model_name="ep-20250224194428-45ldg",
                openai_api_key="fe83aec7-a314-4662-9e6f-b490fe8afef6",
                temperature=1.0,
                top_p=1.0,
                base_url = "https://ark.cn-beijing.volces.com/api/v3"
            )   
        elif self.llm_name == 'Doubao-English':
            llm_pipline = ChatOpenAI(
                model_name="ep-20250224194428-45ldg",
                openai_api_key="fe83aec7-a314-4662-9e6f-b490fe8afef6",
                temperature=1.0,
                top_p=1.0,
                base_url = "https://ark.cn-beijing.volces.com/api/v3"
            )  
        elif self.llm_name == 'Deepseek-huoshan-Chinese':
            llm_pipline = ChatOpenAI(
                model_name="ep-20250219110634-w2x6v",
                openai_api_key="fe83aec7-a314-4662-9e6f-b490fe8afef6",
                temperature=1.0,
                top_p=1.0,
                frequency_penalty=0.15,
                base_url = "https://ark.cn-beijing.volces.com/api/v3"
            )  
        elif self.llm_name == 'Deepseek-huoshan-English':
            llm_pipline = ChatOpenAI(
                model_name="ep-20250219110634-w2x6v",
                openai_api_key="fe83aec7-a314-4662-9e6f-b490fe8afef6",
                temperature=1.0,
                top_p=1.0,
                frequency_penalty=0.15,
                base_url = "https://ark.cn-beijing.volces.com/api/v3"
            )    
        else:
            llm_pipline = ChatOpenAI(
                model_name="deepseek-chat",
                openai_api_key="sk-3bfb89dca6e045fa9cb84a775a303d39",
                temperature=2.0,
                base_url = "https://api.deepseek.com"
            )
        return llm_abstract_pipline, llm_pipline
    
    def query(self, setup_and_retrieval, prompt, input_text):
        chain = setup_and_retrieval | prompt | self._llm_pipline | self._output_parser
        result = chain.invoke(input_text)
    
        return result
    

class LocalModel(LargeLanguageModel):
    def __init__(self, llm_name:str) -> None:
        """
        model_name: 本地生成式模型路径
        """
        self.__llm_name = llm_name

        self._llm_pipline = self.__init_pipline()
    
    def init_pipline(self):
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )

        tokenizer = AutoTokenizer.from_pretrained(self.__llm_name, use_fast=True)
        tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            self.__llm_name, 
            torch_dtype=torch.float16,
            trust_remote_code=True,
            device_map="auto",
            quantization_config=quantization_config
        )

        generation_config = GenerationConfig.from_pretrained(self.__llm_name)
        generation_config.max_new_tokens = 1024
        generation_config.temperature = 0.0001
        generation_config.top_p = 0.95
        generation_config.do_sample = True
        generation_config.repetition_penalty = 1.15

        llm_pipline = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            return_full_text=True,
            generation_config=generation_config,
        )

        llm_pipline = HuggingFacePipeline(pipeline=llm_pipline)

        return llm_pipline
    
    def query(self, setup_and_retrieval, prompt, input_text):
        chain = RetrievalQA.from_chain_type(
            llm=self._llm_pipline,
            chain_type="stuff",
            retriever=setup_and_retrieval,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt},
        )

        result = chain(input_text)
    
        return result
    

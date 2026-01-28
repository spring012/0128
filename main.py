from PaperWriter import PaperWriter, AbstractWriter, OpeningReportWriter, TaskBookWriter
from PPTWriter import PPTWriter
from SurveyWriter import SurveyWriter
from DataProcess import LocalDataBase
from LargeModel import OnlineModel
from Interface import PaperInfo, PaperInfoAll, AIGCTool, AIGCContext, AIGCContextV2, AIGCFileContext, AIGCFileContextV2
from Retriever import Retriever
import Global 
from Utils import delete_folder

from oss import OSS
from fastapi import FastAPI
from pydantic import BaseModel
import random
from datetime import datetime
from typing import List, ForwardRef
import time
import requests
import json
import torch
import logging
import multiprocessing
from multiprocessing import Lock
import os
import tempfile
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# from langchain.globals import set_debug
# set_debug(True)


"""环境准备"""
# reference:
# 下载链接: https://pan.baidu.com/s/1cC7wl7lIkbFQ3fPCJab_Mg?pwd=tjzk 提取码: tjzk
SERVER = 'http://60.205.201.163:22020'
if Global.IS_DEBUG:
    SERVER = 'http://10.191.213.94:22020'

# 初始化
EmbeddingBase = LocalDataBase(Global.model_name, Global.data_path, Global.database_path, Global.device)
# EmbeddingBase = None
MyModel = OnlineModel(llm_name='GPT3.5')
app = FastAPI()

def errorMonitor(body: str):

    try:
        with smtplib.SMTP('smtp.163.com', 25) as server:  # 替换为您的SMTP服务器
            server.starttls()
    except Exception as e:
        logging.exception("Failed to send error email: %s", e)

## 定义返回数据的模型
class ResponseData(BaseModel):
    errCode: int
    msg: str
    data: dict

def calculate_outline_paper():
    # 获取当前时间
    now = datetime.now()
    hour = now.hour
    
    # 假设0点时outline的基数为100
    base_hour = 0
    
    # 计算outline的大小，假设其每小时增加100左右
    # 由于我们从0点开始计算，所以直接使用当前小时数乘以100
    outline = (hour - base_hour) * 100
    
    # 计算paper的大小，是outline的十分之一
    paper = outline / 10
    
    # 为outline和paper添加随机数，范围在-5到5之间
    random_number = random.uniform(-5, 5)
    outline_with_random = round(outline + random_number)
    paper_with_random = round(paper + random_number)
    if outline_with_random < 0:
        outline_with_random = 0
    if paper_with_random < 0:
        paper_with_random = 0
    return outline_with_random, paper_with_random

## 获取今日生成大纲数和论文API
@app.post('/paper/count')
def paperCount():
    try:
        outline, paper = calculate_outline_paper()
        response = {
            "errCode": 0,
            "msg": "",
            "data": {
                "outline": round(outline),
                "paper": round(paper)
            }
        }
        return ResponseData.parse_obj(response)
    except Exception as e:
        logging.exception(e)
        return ResponseData(errCode=1, msg="服务器错误，请稍后重试", data={})

## 检测后台是否正常在运行的API
@app.post('/areyouok')
def message():
    return "ok"

@app.post("/paper/legalCheck")
def genFullPaper(paper_info: PaperInfo):
    try:
        if paper_info is None:
            return ResponseData(errCode=1, msg="", data={})
        if paper_info.title is None or paper_info.title == '':
            return ResponseData(errCode=1, msg="参数错误", data={})
        if paper_info.wordCount not in [10000, 20000, 30000, 30000, 50000, 100000, 15000, 200000, 5000, 4500, 4800, 8000, 8100]:
            return ResponseData(errCode=1, msg="参数错误", data={})

        ##################################################
        abstract_writer = AbstractWriter(MyModel, EmbeddingBase, paper_info, Global.data_volume, log_path=Global.log_path)
        isLegal = abstract_writer.LegalCheck(min_abstract_word=500)

        response = {
            "errCode": 0,
            "msg": "",
            "data": {
                "isLegal": isLegal,
            }
        }
        return ResponseData.parse_obj(response)
    except Exception as e:
        logging.exception(e)
        errorMonitor(str(e))
        return ResponseData(errCode=1, msg="服务器错误，请稍后重试", data={})
    
## 生成大纲API：QPS为1
@app.post("/paper/genOutline")
def paperGenOutline(paper_info: PaperInfo):
    try:
        if paper_info is None:
            return ResponseData(errCode=1, msg="参数错误", data={})
        if paper_info.title is None or paper_info.title == '':
            return ResponseData(errCode=1, msg="参数错误", data={})
        if paper_info.wordCount not in [10000, 20000, 30000, 30000, 50000, 100000, 15000, 200000, 5000, 4500, 4800, 8000, 8100]:
            return ResponseData(errCode=1, msg="参数错误", data={})

        ##################################################
        abstract = None
        outlines = None
        for _ in range(3):
            abstract_writer = AbstractWriter(MyModel, EmbeddingBase, paper_info, Global.data_volume, log_path=Global.log_path)
            # abstract_writer = AbstractWriter(MyModel, None, paper_info, Global.data_volume, log_path=Global.log_path)
            isLegal = abstract_writer.LegalCheck(min_abstract_word=500)
            if not isLegal:
                return ResponseData(errCode=1, msg="非法输入，请检查!", data={})
            
            try:
                abstract = abstract_writer.GetAbstract(min_abstract_word=500)
            except Exception as oe1:
                logging.exception(oe1)
                errorMonitor(str(oe1))

            try:
                outlines = abstract_writer.GetOutline()
            except Exception as oe:
                logging.exception(oe)
                errorMonitor(str(oe))
                
            del abstract_writer
            torch.cuda.empty_cache()
            
            if outlines is not None:
                break
        
        ##################################################

        if outlines is None:
            errorMonitor("生成大纲失败")

        response = {
            "errCode": 0,
            "msg": "",
            "data": {
                "abstract": abstract,
                "outline": outlines
            }
        }
        return ResponseData.parse_obj(response)
    except Exception as e:
        logging.exception(e)
        errorMonitor(str(e))
        return ResponseData(errCode=1, msg="服务器错误，请稍后重试", data={})

def convert_model_to_dict(model: BaseModel) -> dict:
    if isinstance(model, list):
        return [convert_model_to_dict(item) for item in model]
    elif isinstance(model, BaseModel):
        return {k: convert_model_to_dict(v) for k, v in model.dict().items()}
    else:
        return model

def notifyServerPaperGenFinished(orderid, result): 
    url = SERVER + "/serverGenFinished561"
    d = {}
    d["result"] = result
    d["orderid"] = orderid
    requests.post(url, json=d)



def download_file(url):
    # print("download_file() 被调用")
    cache_dir = tempfile.gettempdir()
    os.makedirs(cache_dir, exist_ok=True)
    try:
        file_name = url.split('/')[-1]
        file_path = os.path.join(cache_dir, file_name)
        response = requests.get(url, stream=True, verify=False)
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024 * 8):
                    if chunk:
                        f.write(chunk)
            return file_path
        else:
            print(f"下载 {url} 失败，状态码：{response.status_code}")
            return None
    except Exception as e:
        logging.info(url)
        logging.exception(e)
        return None

def download_reference_files(paper_info: PaperInfoAll):
    cache_dir = tempfile.gettempdir()
    os.makedirs(cache_dir, exist_ok=True)
    print(paper_info.referenceFileList)
    index = 0
    for rf in paper_info.referenceFileList:
        fp = download_file(rf)
        paper_info.referenceFileList[index] = fp
        index+=1

    c1 = 0
    for chapter1 in paper_info.outline:
        index1 = 0
        for rf1 in chapter1.referenceFileList:
            print("rf1:" + rf1)
            fp1 = download_file(rf1)
            paper_info.outline[c1].referenceFileList[index1] = fp1
            index1 += 1
        if len(chapter1.sub) > 0:
            c2 = 0
            for chapter2 in chapter1.sub:
                index2 = 0
                for rf2 in chapter2.referenceFileList:
                    print("rf2:" + rf2)
                    fp2 = download_file(rf2)
                    paper_info.outline[c1].sub[c2].referenceFileList[index2] = fp2
                    index2 += 1
                if len(chapter2.sub) > 0:
                    c3 = 0
                    for chapter3 in chapter2.sub:
                        index3 = 0
                        for rf3 in chapter3.referenceFileList:
                            print("rf3:" + rf3)
                            fp3 = download_file(rf3)
                            paper_info.outline[c1].sub[c2].sub[c3].referenceFileList[index3] = fp3
                            index3 += 1
                        c3 += 1
                c2 += 1
        c1 += 1
def genFullPaperInternal(paper_info: PaperInfoAll, lock): 
    result = []
    # lock.acquire()
    try:
        # 把投喂的参考资料下载到本地
        download_reference_files(paper_info)
        ##################################################
        retriever = Retriever(paper_info, ref_db=EmbeddingBase, retrieve_num=Global.retrieve_num, max_online_search_num=Global.max_online_search_num, lockk=lock)
        # retriever = Retriever(paper_info, ref_db=None, retrieve_num=Global.retrieve_num, max_online_search_num=Global.max_online_search_num)
        paper_writer = PaperWriter(MyModel, retriever, paper_info, log_path=Global.log_path)

        # 完成英文摘要和全文
        timestamp_ms = int(time.time() * 1000)
        timestamp_ms_str = str(timestamp_ms)
        filename =  paper_info.title + '_' +timestamp_ms_str + '.docx'
        output_path = Global.paper_save_path + filename

        full_paper = paper_writer.GetFullPaper() # 获取全文
        paper_writer.WriteToDocx(output_path=output_path, forced_add_catalogs=True)
        if paper_info.wordCount != 4500 and paper_info.wordCount != 4800:
            result.extend(OSS().upload(filename, output_path))
            print(output_path + '生成完成')

        # 完成开题报告
        # needGenOpeningReport 为true或者字数为4500表示需要生成开题报告
        opening_writer = None
        if paper_info.needGenOpeningReport or paper_info.wordCount == 4500:
            filename1 = paper_info.title + '_' +timestamp_ms_str + '_开题报告.docx'
            output_path = Global.paper_save_path + filename1
            opening_writer = OpeningReportWriter(MyModel, paper_info, paper_writer)
            opening_writer.WriteOpeningReport(output_path)
            result.extend(OSS().upload(filename1, output_path))
            print(output_path + '生成完成')
            
        # 完成任务书
        if paper_info.needGenTaskBook or paper_info.wordCount == 4800:
            filename1 = paper_info.title + '_' +timestamp_ms_str + '_任务书.docx'
            output_path = Global.paper_save_path + filename1
            task_writer = TaskBookWriter(MyModel, paper_info, paper_writer, opening_writer)
            task_writer.WriteTaskBook(output_path)
            result.extend(OSS().upload(filename1, output_path))
            print(output_path + '生成完成')

        # 完成答辩ppt
        if paper_info.needGenPPT:
            filename1 = paper_info.title + '_' +timestamp_ms_str + '_答辩PPT.pptx'
            output_path = Global.paper_save_path + filename1
            ppt_writer = PPTWriter(MyModel, paper_info, full_paper) # 获取ppt，需要修改的是PPTWriter
            ppt_writer.GetPPT(output_path=output_path)
            result.extend(OSS().upload(filename1, output_path))
            print(output_path + '生成完成')

        # 完成调查问卷
        if paper_info.needSurvey:
            filename1 = paper_info.title + '_' +timestamp_ms_str + '_调查问卷.docx'
            output_path = Global.paper_save_path + filename1
            survey_writer = SurveyWriter(MyModel, paper_info)
            survey_writer.WriteSurvey(output_path)
            result.extend(OSS().upload(filename1, output_path))
            print(output_path + '生成完成')

        # 删除缓存
        retriever.url_proprietary_sentence_databse.delete_collection()
        del retriever
        del paper_writer
        delete_folder('C:\\Users\\REN\AppData\\Local\\Temp\\gen_py\\3.8\\00020905-0000-0000-C000-000000000046x0x8x7')
        torch.cuda.empty_cache()
        ##################################################
        
        # 通知服务器已生成完毕
        notifyServerPaperGenFinished(paper_info.orderid, result)
        lock.release()
        print('释放锁')
    except Exception as e:
        lock.release()
        print('释放锁')
        logging.exception(e)
        errorMonitor(str(e))
        notifyServerPaperGenFinished(paper_info.orderid, result)

    return 0
paperlock = Lock()

@app.post("/paper/genFullPaper")
def genFullPaper(paper_info: PaperInfoAll):
    # try:
    # print(str(paper_info.abstract))
    # print(str(paper_info.outline))
    try:
        p = multiprocessing.Process(target=genFullPaperInternal, args=(paper_info, paperlock))
        p.start()
        response = {
            "errCode": 0,
            "msg": "",
            "data": {}
        }
        return ResponseData.parse_obj(response)
    except Exception as e:
        logging.exception(e)
        return ResponseData(errCode=1, msg="服务器错误，请稍后重试", data={})

# 启动命令：$ uvicorn main:app --reload --host 0.0.0.0 --port 8000
# 后台常驻命令：nohup uvicorn main:app --host 0.0.0.0 --port 6006 > test.log 2>&1 &
# reference: https://blog.csdn.net/weixin_43021830/article/details/128243800
# reference: 设置监听端口https://blog.csdn.net/qq_43229040/article/details/112461691
# 内网映射 reference: https://github.com/sazima/proxynt

# @deprecated
@app.post("/nanvbnmsadAIGC")
def genFullPaper(aigc_context: AIGCContext):
    try:
        if aigc_context is None:
            return ResponseData(errCode=1, msg="参数错误", data={})
        if aigc_context.text is None or aigc_context.text == '':
            return ResponseData(errCode=1, msg="参数错误", data={})

        aigcTool = AIGCTool(OnlineModel(llm_name='Deepseek'))

        result = aigcTool.reduceAIGC(aigc_context.text)

        response = {
            "errCode": 0,
            "msg": "",
            "data": {
                "result": result,
            }
        }
        return ResponseData.parse_obj(response)
    except Exception as e:
        logging.exception(e)
        errorMonitor(str(e))
        return ResponseData(errCode=1, msg="服务器错误，请稍后重试", data={})

@app.post("/nanvbnmsadAIGCV2")
def genFullPaper(aigc_context: AIGCContextV2):
    try:
        if aigc_context is None:
            return ResponseData(errCode=1, msg="参数错误", data={})
        if aigc_context.text is None or aigc_context.text == '':
            return ResponseData(errCode=1, msg="参数错误", data={})
        if aigc_context.lang not in ['zh', 'en']:
            return ResponseData(errCode=1, msg="参数错误", data={})
        
        aigcTool = AIGCTool(OnlineModel(llm_name='Deepseek'), aigc_context.lang == 'en')

        result = aigcTool.reduceAIGC(aigc_context.text)

        response = {
            "errCode": 0,
            "msg": "",
            "data": {
                "result": result,
            }
        }
        return ResponseData.parse_obj(response)
    except Exception as e:
        logging.exception(e)
        errorMonitor(str(e))
        return ResponseData(errCode=1, msg="服务器错误，请稍后重试", data={})

def notifyServerFileReduceFinished(orderid, result): 
    url = SERVER + "/serverReduceFinished561"
    d = {}
    d["result"] = result
    d["orderid"] = orderid
    requests.post(url, json=d)

# @deprecated
def reduceFileAIGC(aigc_context: AIGCFileContext):
    urls = []
    try:
        aigcTool = AIGCTool(OnlineModel(llm_name='Deepseek'))
        filepath = download_file(aigc_context.fileurl)
        if filepath is None:
            errorMonitor(f"文件下载失败fileurl: {aigc_context.fileurl}，orderid: {aigc_context.orderid}")  # 新增错误监控
            return None
        file_extension = os.path.splitext(filepath)[1]  # 获取文件后缀名
        if file_extension == '.docx':
            urls.extend(aigcTool.reduceDocxAIGC(filepath))
        elif file_extension == '.txt':
            urls.extend(aigcTool.reduceTxtAIGC(filepath))
        notifyServerFileReduceFinished(aigc_context.orderid, urls)
    except Exception as e:
        logging.exception(e)
        errorMonitor(str(e))
        notifyServerFileReduceFinished(aigc_context.orderid, urls)

# @deprecated
@app.post("/amsdbjasbFileAIGC")
def genFullPaper(aigc_context: AIGCFileContext):
    try:
        if aigc_context is None:
            return ResponseData(errCode=1, msg="参数错误", data={})
        if aigc_context.fileurl is None or aigc_context.fileurl == '':
            return ResponseData(errCode=1, msg="参数错误", data={})
        if aigc_context.orderid is None or aigc_context.orderid == '':
            return ResponseData(errCode=1, msg="参数错误", data={})
        p = multiprocessing.Process(target=reduceFileAIGC, args=(aigc_context,))
        p.start()
        response = {
            "errCode": 0,
            "msg": "",
            "data": {}
        }
        return ResponseData.parse_obj(response)
    except Exception as e:
        logging.exception(e)
        errorMonitor(str(e))
        return ResponseData(errCode=1, msg="服务器错误，请稍后重试", data={})
    
def reduceFileAIGCV2(aigc_context: AIGCFileContextV2):
    urls = []
    try:
        aigcTool = AIGCTool(OnlineModel(llm_name='Deepseek'), aigc_context.lang == 'en')
        filepath = download_file(aigc_context.fileurl)
        if filepath is None:
            errorMonitor(f"文件下载失败fileurl: {aigc_context.fileurl}，orderid: {aigc_context.orderid}")  # 新增错误监控
            return None
        file_extension = os.path.splitext(filepath)[1]  # 获取文件后缀名
        if file_extension == '.docx':
            urls.extend(aigcTool.reduceDocxAIGC(filepath))
        elif file_extension == '.txt':
            urls.extend(aigcTool.reduceTxtAIGC(filepath))
        notifyServerFileReduceFinished(aigc_context.orderid, urls)
    except Exception as e:
        logging.exception(e)
        errorMonitor(str(e))
        notifyServerFileReduceFinished(aigc_context.orderid, urls)

@app.post("/amsdbjasbFileAIGCV2")
def genFullPaper(aigc_context: AIGCFileContextV2):
    try:
        if aigc_context is None:
            return ResponseData(errCode=1, msg="参数错误", data={})
        if aigc_context.fileurl is None or aigc_context.fileurl == '':
            return ResponseData(errCode=1, msg="参数错误", data={})
        if aigc_context.orderid is None or aigc_context.orderid == '':
            return ResponseData(errCode=1, msg="参数错误", data={})
        if aigc_context.lang not in ['zh', 'en']:
            return ResponseData(errCode=1, msg="参数错误", data={})
        
        p = multiprocessing.Process(target=reduceFileAIGCV2, args=(aigc_context,))
        p.start()
        response = {
            "errCode": 0,
            "msg": "",
            "data": {}
        }
        return ResponseData.parse_obj(response)
    except Exception as e:
        logging.exception(e)
        errorMonitor(str(e))
        return ResponseData(errCode=1, msg="服务器错误，请稍后重试", data={})
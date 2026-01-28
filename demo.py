from PaperWriter import PaperWriter, AbstractWriter, OpeningReportWriter, TaskBookWriter
from PPTWriter import PPTWriter
from DataProcess import LocalDataBase, ReferenceDataBase
from LargeModel import OnlineModel
from Interface import PaperInfoAll, PaperInfo
from Retriever import Retriever
from Utils import delete_folder
import Global

from langchain_community.vectorstores.chroma import Chroma
import time
import torch
from langchain.globals import set_debug

set_debug(True)

# 初始化
EmbeddingBase = LocalDataBase(Global.model_name, Global.data_path, Global.database_path, Global.device)
MyModel = OnlineModel(llm_name='GPT3.5')

def paperGenOutline(paper_info: PaperInfo):
    abstract_writer = AbstractWriter(MyModel, EmbeddingBase, paper_info, Global.data_volume, log_path=Global.log_path)
    abstract = abstract_writer.GetAbstract(min_abstract_word=500)

    if abstract[0] is None or abstract[1] is None:
       exit(0)
    torch.save(abstract, 'E1' if paper_info.isEnglish else 'C1')
    abstract_writer.abstract = torch.load('E1' if paper_info.isEnglish else 'C1')

    outlines = abstract_writer.GetOutline()
    if outlines is None:
        exit(0) 
    torch.save(outlines, 'E2' if paper_info.isEnglish else 'C2')

    del abstract_writer
    torch.cuda.empty_cache()
    return abstract, outlines

def genFullPaperInternal(paper_info: PaperInfoAll):
    retriever = Retriever(paper_info, ref_db=EmbeddingBase, retrieve_num=Global.retrieve_num, max_online_search_num=Global.max_online_search_num)
    paper_writer = PaperWriter(MyModel, retriever, paper_info, log_path=Global.log_path)

    # 完成英文摘要和全文
    output_path = Global.paper_save_path + paper_info.title + '.docx'
    full_paper = paper_writer.GetFullPaper()
    paper_writer.WriteToDocx(output_path=output_path, forced_add_catalogs=True)
    torch.save((paper_writer.paper_content, paper_writer.ref_papers), 'E3' if paper_info.isEnglish else 'C3')
    # paper_writer.paper_content, paper_writer.ref_papers = torch.load('E3' if paper_info.isEnglish else 'C3')
    # paper_writer.WriteToDocx(output_path=output_path, forced_add_catalogs=True)
    # 完成开题报告
    opening_writer = None
    if paper_info.needGenOpeningReport:
        output_path = Global.paper_save_path + paper_info.title + '_开题报告.docx'
        opening_writer = OpeningReportWriter(MyModel, paper_info, paper_writer)
        opening_writer.WriteOpeningReport(output_path)
        
    # 完成任务书
    if paper_info.needGenTaskBook:
        output_path = Global.paper_save_path + paper_info.title + '_任务书.docx'
        task_writer = TaskBookWriter(MyModel, paper_info, paper_writer, opening_writer)
        task_writer.WriteTaskBook(output_path)

    # 完成答辩ppt
    if paper_info.needGenPPT:
        output_path = Global.paper_save_path + paper_info.title + '.pptx'
        ppt_writer = PPTWriter(MyModel, paper_info, full_paper)
        ppt_writer.GetPPT(output_path=output_path)

    # 删除缓存
    retriever.url_proprietary_sentence_databse.delete_collection()
    del retriever
    del paper_writer
    delete_folder('C:\\Users\\REN\AppData\\Local\\Temp\\gen_py\\3.8\\00020905-0000-0000-C000-000000000046x0x8x7')
    torch.cuda.empty_cache()

    # return full_paper

if __name__ == '__main__':
    paper_info = PaperInfo(category='工商管理', 
                    title='科学传播网站用户持续使用行为影响因素实证研究', 
                    wordCount=10000, 
                    useThreeLevel=False,
                    # isEnglish=True,
                    needAIGC=False,
                    )                                                               
    # 完成摘要和提纲
    abstract, outlines = paperGenOutline(paper_info)
    # 接收用户修改的摘要和提纲，并检索相关性更强的内容，生成整篇文章
    abstract = torch.load('E1' if paper_info.isEnglish else 'C1')
    outlines = torch.load('E2' if paper_info.isEnglish else 'C2')
    
    paper_info = PaperInfoAll(category='工商管理', 
                              title='科学传播网站用户持续使用行为影响因素实证研究', 
                              wordCount=10000, 
                              useThreeLevel=False,
                              # isEnglish=True,
                              needGenOpeningReport=False,
                              needGenTaskBook=False,
                              needGenPPT=False,
                              abstract=abstract, 
                              outline=outlines,
                              aiPercent=5,
                              needAIGC=False,
                              # referenceFileList=['D:\PaperWriter\\reference_file_example\\1.txt', 
                              #                   'D:\PaperWriter\\reference_file_example\\1.pdf', 
                              #                  'D:\PaperWriter\\reference_file_example\\1.docx', 
                              #                   'D:\PaperWriter\\reference_file_example\\1.doc', 
                              #                   'D:\PaperWriter\\reference_file_example\\1.xls', 
                              #                   'D:\PaperWriter\\reference_file_example\\1.xlsx'],
                              )
    full_paper = genFullPaperInternal(paper_info)
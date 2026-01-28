"""
混合检索系统 - 结合 BM25 稀疏检索与 Dense Vector 语义检索
支持多粒度文档切分和语义路径元数据
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from rank_bm25 import BM25Okapi
import jieba

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS, Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.retrievers import EnsembleRetriever, ContextualCompressionRetriever
from langchain.retrievers.document_compressors import EmbeddingsFilter
from langchain_community.retrievers import BM25Retriever

import re
import threading
from collections import defaultdict


@dataclass
class RetrievalConfig:
    """检索配置类"""
    # 混合检索权重
    bm25_weight: float = 0.3  # BM25权重
    dense_weight: float = 0.7  # 向量检索权重
    
    # 多粒度切分参数
    section_chunk_size: int = 1500  # 章节级切分大小
    paragraph_chunk_size: int = 800  # 段落级切分大小
    sentence_chunk_size: int = 200   # 句子级切分大小
    chunk_overlap: int = 100         # 重叠区域
    
    # 检索参数
    top_k: int = 15                  # 返回文档数
    min_similarity: float = 0.3      # 最小相似度阈值
    use_rerank: bool = True          # 是否使用重排序
    
    # 向量库选择
    vector_store: str = "faiss"      # "faiss" or "chroma"


class MultiGranularitySplitter:
    """多粒度文档切分器"""
    
    def __init__(self, config: RetrievalConfig):
        self.config = config
        self.section_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.section_chunk_size,
            chunk_overlap=config.chunk_overlap,
            separators=["\n\n\n", "\n\n", "。\n", "。", "\n", " ", ""]
        )
        self.paragraph_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.paragraph_chunk_size,
            chunk_overlap=config.chunk_overlap,
            separators=["\n\n", "。\n", "。", "\n", " "]
        )
        self.sentence_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.sentence_chunk_size,
            chunk_overlap=20,
            separators=["。", "；", "！", "？", "\n"]
        )
    
    def split_with_hierarchy(self, document: Document) -> List[Document]:
        """
        层次化切分文档,添加语义路径元数据
        
        Returns:
            包含多粒度切片和完整元数据的文档列表
        """
        all_chunks = []
        content = document.page_content
        base_metadata = document.metadata.copy()
        
        # 1. 章节级切分
        sections = self.section_splitter.split_text(content)
        
        for section_idx, section in enumerate(sections):
            section_path = f"section_{section_idx}"
            
            # 2. 段落级切分
            paragraphs = self.paragraph_splitter.split_text(section)
            
            for para_idx, paragraph in enumerate(paragraphs):
                para_path = f"{section_path}/para_{para_idx}"
                
                # 3. 句子级切分(用于精确引用)
                sentences = self.sentence_splitter.split_text(paragraph)
                
                # 保存段落级文档(主检索单元)
                para_metadata = {
                    **base_metadata,
                    "granularity": "paragraph",
                    "semantic_path": para_path,
                    "section_idx": section_idx,
                    "para_idx": para_idx,
                    "parent_section": section[:100],  # 保存上下文
                    "char_start": content.find(paragraph),
                    "char_end": content.find(paragraph) + len(paragraph)
                }
                all_chunks.append(Document(
                    page_content=paragraph,
                    metadata=para_metadata
                ))
                
                # 可选: 保存句子级索引(用于精确匹配)
                for sent_idx, sentence in enumerate(sentences):
                    if len(sentence.strip()) < 10:  # 过滤过短句子
                        continue
                    sent_metadata = {
                        **base_metadata,
                        "granularity": "sentence",
                        "semantic_path": f"{para_path}/sent_{sent_idx}",
                        "parent_paragraph": paragraph[:100]
                    }
                    all_chunks.append(Document(
                        page_content=sentence,
                        metadata=sent_metadata
                    ))
        
        return all_chunks


class HybridRetriever:
    """
    混合检索器 - 融合 BM25 和 Dense Vector 检索
    """
    
    def __init__(
        self,
        embedding_model: HuggingFaceEmbeddings,
        config: RetrievalConfig,
        persist_directory: Optional[str] = None
    ):
        self.embedding_model = embedding_model
        self.config = config
        self.persist_directory = persist_directory
        
        # 向量数据库
        self.vector_store = None
        self.bm25_retriever = None
        
        # 多粒度切分器
        self.splitter = MultiGranularitySplitter(config)
        
        # 文档索引(用于BM25)
        self.bm25_corpus = []
        self.bm25_docs = []
        
        self.lock = threading.Lock()
    
    def build_index(self, documents: List[Document]):
        """
        构建混合索引
        
        Args:
            documents: 原始文档列表
        """
        print("🔨 开始构建混合检索索引...")
        
        # Step 1: 多粒度切分
        all_chunks = []
        for doc in documents:
            chunks = self.splitter.split_with_hierarchy(doc)
            all_chunks.extend(chunks)
        
        print(f"📊 切分完成: 共 {len(all_chunks)} 个文档块")
        
        # Step 2: 构建向量索引 (FAISS/Chroma)
        if self.config.vector_store == "faiss":
            self.vector_store = FAISS.from_documents(
                all_chunks,
                self.embedding_model
            )
            if self.persist_directory:
                self.vector_store.save_local(self.persist_directory)
        else:
            self.vector_store = Chroma.from_documents(
                all_chunks,
                self.embedding_model,
                persist_directory=self.persist_directory
            )
        
        print("✅ 向量索引构建完成")
        
        # Step 3: 构建 BM25 索引
        self._build_bm25_index(all_chunks)
        
        print("✅ BM25 索引构建完成")
    
    def _build_bm25_index(self, documents: List[Document]):
        """构建 BM25 稀疏检索索引"""
        self.bm25_docs = documents
        
        # 分词处理
        tokenized_corpus = []
        for doc in documents:
            # 中文使用 jieba 分词
            if self._is_chinese(doc.page_content):
                tokens = list(jieba.cut(doc.page_content))
            else:
                tokens = doc.page_content.lower().split()
            tokenized_corpus.append(tokens)
        
        self.bm25_corpus = tokenized_corpus
        self.bm25_model = BM25Okapi(tokenized_corpus)
    
    def _is_chinese(self, text: str) -> bool:
        """判断文本是否为中文"""
        return bool(re.search(r'[\u4e00-\u9fff]', text))
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict] = None
    ) -> List[Document]:
        """
        混合检索主函数
        
        Args:
            query: 查询文本
            top_k: 返回文档数
            filters: 元数据过滤条件 (例如: {"granularity": "paragraph"})
        
        Returns:
            排序后的文档列表
        """
        top_k = top_k or self.config.top_k
        
        # 1. BM25 稀疏检索
        bm25_docs = self._bm25_retrieve(query, top_k * 2)
        
        # 2. Dense Vector 检索
        dense_docs = self._dense_retrieve(query, top_k * 2, filters)
        
        # 3. 混合融合
        merged_docs = self._merge_results(
            bm25_docs,
            dense_docs,
            query,
            top_k
        )
        
        # 4. 可选: 重排序
        if self.config.use_rerank:
            merged_docs = self._rerank(query, merged_docs)
        
        return merged_docs[:top_k]
    
    def _bm25_retrieve(self, query: str, top_k: int) -> List[Tuple[Document, float]]:
        """BM25 检索"""
        # 查询分词
        if self._is_chinese(query):
            query_tokens = list(jieba.cut(query))
        else:
            query_tokens = query.lower().split()
        
        # 计算 BM25 分数
        scores = self.bm25_model.get_scores(query_tokens)
        
        # 获取 top_k 结果
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = scores[idx]
            if score > 0:  # 过滤零分文档
                results.append((self.bm25_docs[idx], float(score)))
        
        return results
    
    def _dense_retrieve(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict]
    ) -> List[Tuple[Document, float]]:
        """向量检索"""
        if filters:
            # 使用过滤器
            results = self.vector_store.similarity_search_with_score(
                query,
                k=top_k,
                filter=filters
            )
        else:
            results = self.vector_store.similarity_search_with_score(
                query,
                k=top_k
            )
        
        return results
    
    def _merge_results(
        self,
        bm25_results: List[Tuple[Document, float]],
        dense_results: List[Tuple[Document, float]],
        query: str,
        top_k: int
    ) -> List[Document]:
        """
        融合 BM25 和 Dense 检索结果 (Reciprocal Rank Fusion)
        """
        # 归一化分数
        def normalize_scores(results):
            if not results:
                return {}
            scores = [score for _, score in results]
            min_score, max_score = min(scores), max(scores)
            range_score = max_score - min_score if max_score > min_score else 1
            
            normalized = {}
            for doc, score in results:
                doc_id = doc.page_content[:50]  # 使用内容前50字作为ID
                normalized[doc_id] = (score - min_score) / range_score
            return normalized
        
        bm25_scores = normalize_scores(bm25_results)
        dense_scores = normalize_scores(dense_results)
        
        # 加权融合
        all_doc_ids = set(bm25_scores.keys()) | set(dense_scores.keys())
        merged_scores = {}
        
        for doc_id in all_doc_ids:
            bm25_score = bm25_scores.get(doc_id, 0)
            dense_score = dense_scores.get(doc_id, 0)
            
            # 加权平均
            merged_scores[doc_id] = (
                self.config.bm25_weight * bm25_score +
                self.config.dense_weight * dense_score
            )
        
        # 排序并获取原始文档
        sorted_ids = sorted(
            merged_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]
        
        # 构建文档映射
        doc_map = {}
        for doc, _ in bm25_results + dense_results:
            doc_id = doc.page_content[:50]
            if doc_id not in doc_map:
                doc_map[doc_id] = doc
        
        return [doc_map[doc_id] for doc_id, _ in sorted_ids if doc_id in doc_map]
    
    def _rerank(self, query: str, documents: List[Document]) -> List[Document]:
        """
        使用 Embedding 相似度重排序 (简化版)
        生产环境可替换为 Cross-Encoder 模型
        """
        query_embedding = self.embedding_model.embed_query(query)
        doc_embeddings = self.embedding_model.embed_documents(
            [doc.page_content for doc in documents]
        )
        
        # 计算余弦相似度
        scores = []
        for doc_emb in doc_embeddings:
            score = np.dot(query_embedding, doc_emb) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_emb)
            )
            scores.append(score)
        
        # 按相似度排序
        sorted_indices = np.argsort(scores)[::-1]
        return [documents[i] for i in sorted_indices]
    
    def retrieve_with_context(
        self,
        query: str,
        top_k: int = 5,
        context_window: int = 1
    ) -> List[Dict]:
        """
        检索并返回带上下文的结果
        
        Args:
            context_window: 上下文窗口大小(返回前后N个段落)
        """
        base_docs = self.retrieve(query, top_k)
        
        results = []
        for doc in base_docs:
            result = {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "context": self._get_context(doc, context_window)
            }
            results.append(result)
        
        return results
    
    def _get_context(self, doc: Document, window: int) -> Dict:
        """获取文档上下文"""
        metadata = doc.metadata
        semantic_path = metadata.get("semantic_path", "")
        
        # 解析路径获取相邻段落
        # 实际实现需要根据 semantic_path 查询数据库
        context = {
            "parent_section": metadata.get("parent_section", ""),
            "before": [],  # 前面的段落
            "after": []    # 后面的段落
        }
        
        return context


# ==================== 使用示例 ====================
from LargeModel import OnlineModel
def example_usage():
    """示例: 如何使用混合检索器"""
    
    # 1. 初始化配置
    config = RetrievalConfig(
        bm25_weight=0.3,
        dense_weight=0.7,
        top_k=10,
        vector_store="faiss"
    )
    MyModel = OnlineModel(llm_name='GPT3.5')

    # 2. 加载 Embedding 模型
    embedding_model = MyModel
    
    # 3. 创建检索器
    retriever = HybridRetriever(
        embedding_model=embedding_model,
        config=config,
        persist_directory="./vector_db"
    )
    
    # 4. 构建索引
    documents = [
        Document(
            page_content="人工智能正在改变世界...",
            metadata={"source": "paper1.pdf", "page": 1}
        ),
        # 更多文档...
    ]
    retriever.build_index(documents)
    
    # 5. 检索
    results = retriever.retrieve(
        query="深度学习在自然语言处理中的应用",
        top_k=5
    )
    
    for i, doc in enumerate(results):
        print(f"\n--- Result {i+1} ---")
        print(f"Content: {doc.page_content[:100]}...")
        print(f"Metadata: {doc.metadata}")


if __name__ == "__main__":
    example_usage()
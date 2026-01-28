import dspy
import openai
from dspy.teleprompt import BootstrapFewShot
from dspy.retrieve.chromadb_rm import ChromadbRM
from sentence_transformers import SentenceTransformer
import re
import chromadb
import torch

model = SentenceTransformer(model_name_or_path = '', device = 'cuda')
class MyEmbeddingFunction(chromadb.EmbeddingFunction):
    def __call__(self, texts: chromadb.Documents) -> chromadb.Embeddings:
        embeddings = [list(model.encode(text,normalize_embeddings=True).astype(float)) for text in texts]
        return embeddings


client = chromadb.Client()

collection = client.create_collection(name="my_collection",
                                      embedding_function=MyEmbeddingFunction())

collection.add(
    documents=["What were the two main things the author worked on before college?Writing and programming", 
               "What programming language did the author learn in college?Python"],
    metadatas=[{"source": "doc1"}, {"source": "doc2"}],
    ids=["id1", "id2"]
)

# Set OpenAI API key

# Configure LLM
lm = dspy.OpenAI(model="gpt-3.5-turbo", api_key="sk-kFwihnlBAuTgfcZc5d183312767648Ef88C58eFa2bA07b80", api_base="https://api.oaipro.com/v1/")

# Configure Retriever
rm = ChromadbRM(collection_name="my_collection", 
                client=client,
                embedding_function=MyEmbeddingFunction(),
                persist_directory="D:\PaperWriter\\RefDatabase")

# Configure DSPy to use the following language model and retrieval model by default
dspy.settings.configure(lm = lm, 
                        rm = rm)

# Small training set with question and answer pairs
trainset = [dspy.Example(question="What were the two main things the author worked on before college?", 
                         answer="Writing and programming").with_inputs('question'),]

class GenerateAnswer(dspy.Signature):
    """Answer questions with short factoid answers."""

    context = dspy.InputField(desc="may contain relevant facts")
    question = dspy.InputField()
    answer = dspy.OutputField(desc="often between 1 and 5 words")

class RAG(dspy.Module):
    def __init__(self, num_passages=1):
        super().__init__()

        self.retrieve = dspy.Retrieve(k=num_passages)
        self.generate_answer = dspy.ChainOfThought(GenerateAnswer)
    
    def forward(self, question):
        context = self.retrieve(question).passages
        prediction = self.generate_answer(context=context, question=question)
        return dspy.Prediction(context=context, answer=prediction.answer)

# Set up a basic teleprompter, which will compile our RAG program.
# teleprompter = BootstrapFewShot(metric=dspy.evaluate.answer_exact_match)

# Compile!
# compiled_rag = teleprompter.compile(RAG(), trainset=trainset)

# compiled_rag.save('00')
compiled_rag = RAG()
compiled_rag.load(path='00')
pred = compiled_rag(question = "你在大学里学了什么")
print(lm.inspect_history())
print(pred)
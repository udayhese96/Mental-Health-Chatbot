from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_groq import ChatGroq
import os

def initialize_llm():
    llm = ChatGroq(
        temperature=0.3,
        groq_api_key=os.environ.get("GROQ_API_KEY"),
        model_name="llama3-8b-8192"
    )
    return llm

def create_vector_db():
    loader = DirectoryLoader("data", glob='*.pdf', loader_cls=PyPDFLoader)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    texts = text_splitter.split_documents(documents)
    embeddings = HuggingFaceBgeEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
    vector_db = Chroma.from_documents(texts, embeddings, persist_directory='./chroma_db')
    print("✅ ChromaDB created and data saved")
    return vector_db

def setup_qa_chain(vector_db, llm):
    retriever = vector_db.as_retriever()

    prompt_template = """
You are a compassionate and supportive mental health assistant. 
Always respond in a calm and kind tone, using **simple and clear language**.

✅ Guidelines for your response:
- If giving remedies, tips, or coping techniques (e.g., for stress, anxiety, depression), use concise **bullet points**:
  - Take deep breaths and relax your shoulders.
  - Talk to someone you trust.
  - Go for a short walk.
- **Avoid long explanations or paragraphs.**
- Stick to **2-3 short lines** max unless asked to explain in detail.
- Focus on emotional well-being, clarity, and encouragement.

Context:
{context}

User: {question}
Chatbot:"""

    PROMPT = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": PROMPT}
    )

    return qa_chain

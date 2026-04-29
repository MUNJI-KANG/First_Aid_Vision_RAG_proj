import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from app.config import Settings

# pdf 파일 로드 및 나누기
def preparse_rag_database():
    pdf_path = "assets"
    documents = []

    # 폴더 안의 모든 pdf 읽기
    for file in os.listdir(pdf_path):
        if file.endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(pdf_path, file))
            documents.extend(loader.load())

    # 텍스트 나누기
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    splits = text_splitter.split_documents(documents)

    # 3. 벡터 DB 생성 및 로컬 저장
    embeddings = OpenAIEmbeddings(openai_api_key=Settings.OPENAI_API_KEY)
    vectorstack = FAISS.from_documents(splits, embeddings)

    # DB를 매번 새로 만들지 않게 로컬에 저장
    vectorstack.save_local("faiss_index")
    return vectorstack

# 관련 지식 검색 함수
def search_relevant_info(query : str):
    embeddings = OpenAIEmbeddings(openai_api_key=Settings.OPENAI_API_KEY)

    # 저장된 DB 불러오기
    if os.path.exists("faiss_index"):
        vectorstack = FAISS.load_local("faiss_index", embeddings, allow_dangerous_pickle=True)
        

        # 유사한 조치법 3개 추출
        results = vectorstack.similarity_search(query, k=3)
        return "\n".join([doc.page_content for doc in results])
    
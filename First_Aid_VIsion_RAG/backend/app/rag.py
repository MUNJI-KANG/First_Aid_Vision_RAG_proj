from functools import lru_cache
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings

PROJECT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]
ASSETS_DIR = PROJECT_DIR / "assets"
CHROMA_DIR = BACKEND_DIR / "chroma_index"
COLLECTION_NAME = "first_aid_manuals"


def _build_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        openai_api_key=settings.OPENAI_API_KEY,
        model=settings.EMBEDDING_MODEL,
        chunk_size=settings.EMBEDDING_BATCH_SIZE,
    )


def _load_documents():
    if not ASSETS_DIR.exists():
        raise FileNotFoundError(f"RAG assets folder not found: {ASSETS_DIR}")

    pdf_files = sorted(ASSETS_DIR.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDF manuals found in: {ASSETS_DIR}")

    documents = []
    for pdf_file in pdf_files:
        loader = PyPDFLoader(str(pdf_file))
        documents.extend(loader.load())

    return documents


def build_vectorstore() -> Chroma:
    documents = _load_documents()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
    )
    splits = text_splitter.split_documents(documents)
    if not splits:
        raise ValueError("No text chunks were created from the PDF manuals.")

    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=_build_embeddings(),
        persist_directory=str(CHROMA_DIR),
        collection_name=COLLECTION_NAME,
    )
    vectorstore.persist()
    return vectorstore


@lru_cache(maxsize=1)
def load_vectorstore() -> Chroma:
    if CHROMA_DIR.exists():
        return Chroma(
            persist_directory=str(CHROMA_DIR),
            embedding_function=_build_embeddings(),
            collection_name=COLLECTION_NAME,
        )
    return build_vectorstore()


def search_relevant_info(query: str) -> str:
    cleaned_query = query.strip()
    if not cleaned_query:
        raise ValueError("Search query is empty.")

    vectorstore = load_vectorstore()
    docs = vectorstore.similarity_search(cleaned_query, k=3)

    if not docs:
        return "매뉴얼에서 관련 응급처치 정보를 찾지 못했습니다."

    return "\n\n".join(doc.page_content.strip() for doc in docs if doc.page_content.strip())

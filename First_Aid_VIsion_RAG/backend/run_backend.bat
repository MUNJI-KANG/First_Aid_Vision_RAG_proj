@echo off
cd /d "F:\First_Aid_Vision_RAG\First_Aid_VIsion_RAG\backend"
"F:\First_Aid_Vision_RAG\First_Aid_VIsion_RAG\backend\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8001

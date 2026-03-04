import json
import asyncio
import redis.asyncio as redis
from langchain_text_splitters import RecursiveCharacterTextSplitter # Use this specific package
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

async def process_queue():
    r = redis.Redis(host='redis', port=6379, decode_responses=True)
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    
    print("Worker started. Listening for tasks...")
    while True:
        try:
            _, message = await r.brpop("ingestion_queue")
            data = json.loads(message)
            
            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            chunks = splitter.split_text(data['content'])
            
            vectorstore.add_texts(chunks, metadatas=[{"source": data['filename']}] * len(chunks))
            print(f"Successfully indexed: {data['filename']}")
        except Exception as e:
            print(f"Worker Error: {e}")

if __name__ == "__main__":
    asyncio.run(process_queue())
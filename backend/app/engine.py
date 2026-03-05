import asyncio
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma

# 1. Use local embeddings (Free & Fast)
embeddings = OllamaEmbeddings(
    model="nomic-embed-text", 
    base_url="http://host.docker.internal:11434"
)
# 2. Use local LLM (Free & No Quota limits)
llm = ChatOllama(
    model="llama3.2:1b", 
    base_url="http://host.docker.internal:11434"
)
vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

async def get_streaming_rag_response(query):
    # Search the local database
    docs = await asyncio.to_thread(vectorstore.similarity_search, query, k=3)
    context = "\n".join([d.page_content for d in docs])
    
    prompt = f"Context: {context}\n\nQuestion: {query}\n\nAnswer:"
    
    # Stream from your local machine
    async for chunk in llm.astream(prompt):
        yield chunk.content
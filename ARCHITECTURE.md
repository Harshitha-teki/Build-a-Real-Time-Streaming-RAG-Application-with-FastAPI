graph TD
    subgraph Client_Layer [Client Layer]
        User((User)) -->|Interact| UI[Chainlit UI]
    end

    subgraph API_Layer [API Layer - FastAPI]
        UI -->|Upload/Query| API[FastAPI Server]
        API -->|1. Save File| Disk[(Shared Volume: /app/data)]
        API -->|2. Push Task| Redis[(Redis Queue)]
    end

    subgraph Background_Layer [Worker Layer]
        Redis -->|3. Pull Task| Worker[Ingestion Worker]
        Worker -->|4. Read/Chunk| Disk
        Worker -->|5. Embed| Ollama_E[Ollama: nomic-embed-text]
        Worker -->|6. Store| Chroma[(ChromaDB)]
    end

    subgraph Inference_Layer [RAG Retrieval]
        API -->|7. Search| Chroma
        Chroma -->|8. Context| API
        API -->|9. Prompt| Ollama_G[Ollama: gemma3:4b]
        Ollama_G -->|10. Stream| UI
    end

    
    
Decoupling via Redis: Using Redis as a message broker ensures that the FastAPI server remains non-blocking. Even if a user uploads a 50-page PDF, the chat interface stays responsive while the Worker handles the heavy lifting in the background.

Shared Volume Architecture: The /app/data volume is the "bridge" that allows the App container to save files and the Worker container to read them without duplicating data.

Persistent Vector Store: ChromaDB is mounted to a local directory (./chroma_db) so that your document embeddings are not lost if the Docker containers are restarted.

## Model Choice
Model: Gemma 3:4b.

Reasoning: This model provides a strong balance between reasoning capabilities and memory efficiency, requiring approximately 4.0 GiB of available system memory. This makes it ideal for local RAG deployments on consumer hardware.
---
name: rag
description: RAG (Retrieval Augmented Generation) patterns for building AI-powered search and Q&A systems using ChromaDB and embeddings.
---

# RAG Development Patterns

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    User Query                       │
└─────────────────────────┬───────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│              Embedding Generation                   │
│         (OpenAI, Sentence Transformers)             │
└─────────────────────────┬───────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│               Vector Search (ChromaDB)              │
│            Find semantically similar docs           │
└─────────────────────────┬───────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│              Context Assembly + LLM                 │
│        Generate answer with retrieved context       │
└─────────────────────────────────────────────────────┘
```

---

## ChromaDB Integration

### Setup
```python
import chromadb
from chromadb.utils import embedding_functions

# Persistent storage
client = chromadb.PersistentClient(path="./chroma_db")

# Use default embedding function
embedding_fn = embedding_functions.DefaultEmbeddingFunction()

# Create/get collection
collection = client.get_or_create_collection(
    name="documents",
    embedding_function=embedding_fn,
    metadata={"hnsw:space": "cosine"}
)
```

### Document Ingestion
```python
from typing import List
import uuid

def ingest_documents(
    documents: List[str],
    metadatas: List[dict] = None
):
    """Add documents to the vector store."""
    ids = [str(uuid.uuid4()) for _ in documents]
    
    collection.add(
        documents=documents,
        metadatas=metadatas or [{}] * len(documents),
        ids=ids
    )
    
    return ids

# Example usage
documents = [
    "FastAPI is a modern Python web framework",
    "Next.js is a React framework for production",
    "DuckDB is an embedded analytical database"
]

metadatas = [
    {"source": "docs", "category": "backend"},
    {"source": "docs", "category": "frontend"},
    {"source": "docs", "category": "database"}
]

ingest_documents(documents, metadatas)
```

### Semantic Search
```python
def search(query: str, n_results: int = 5, filter: dict = None):
    """Search for semantically similar documents."""
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where=filter  # {"category": "backend"}
    )
    
    return [
        {
            "text": doc,
            "metadata": meta,
            "distance": dist
        }
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        )
    ]

# Example
results = search("How to build an API?", n_results=3)
```

---

## Document Processing

### Text Chunking
```python
from typing import List

def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50
) -> List[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence boundary
        if end < len(text):
            last_period = chunk.rfind('.')
            if last_period > chunk_size * 0.5:
                end = start + last_period + 1
                chunk = text[start:end]
        
        chunks.append(chunk.strip())
        start = end - overlap
    
    return chunks

# For larger documents, consider semantic chunking
def semantic_chunk(text: str) -> List[str]:
    """Chunk by paragraphs or sections."""
    paragraphs = text.split('\n\n')
    return [p.strip() for p in paragraphs if p.strip()]
```

### CSV to RAG
```python
import pandas as pd

def ingest_csv_for_rag(filepath: str, text_column: str):
    """Convert CSV data to searchable documents."""
    df = pd.read_csv(filepath)
    
    documents = []
    metadatas = []
    
    for _, row in df.iterrows():
        # Create searchable text from row
        text = row[text_column]
        
        # Add all other columns as metadata
        metadata = row.drop(text_column).to_dict()
        metadata = {k: str(v) for k, v in metadata.items()}
        
        documents.append(text)
        metadatas.append(metadata)
    
    return ingest_documents(documents, metadatas)
```

---

## RAG Pipeline

### Complete Query Pipeline
```python
from openai import OpenAI

client = OpenAI()

def rag_query(question: str, n_context: int = 5) -> str:
    """Complete RAG pipeline: retrieve + generate."""
    
    # 1. Retrieve relevant documents
    results = search(question, n_results=n_context)
    
    # 2. Build context
    context = "\n\n".join([r["text"] for r in results])
    
    # 3. Generate response with context
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": f"""Answer questions based on the following context.
                If the answer is not in the context, say so.
                
                Context:
                {context}"""
            },
            {"role": "user", "content": question}
        ]
    )
    
    return response.choices[0].message.content

# Usage
answer = rag_query("What database should I use for analytics?")
```

---

## Best Practices

### ✅ DO
- Use appropriate chunk sizes (300-500 tokens)
- Add metadata for filtering
- Use cosine similarity for text
- Handle empty results gracefully
- Cache embeddings for performance

### ❌ DON'T
- Chunk too small (loses context)
- Chunk too large (dilutes relevance)
- Ignore metadata potential
- Skip document preprocessing
- Use without evaluation

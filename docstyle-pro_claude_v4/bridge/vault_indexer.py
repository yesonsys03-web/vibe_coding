import os
from pathlib import Path
import re
import chromadb

# Singleton-like approach for the ChromaDB client
_chroma_client = None
_collection = None

def get_chroma_collection():
    global _chroma_client, _collection
    if _chroma_client is None:
        vault_dir = Path.home() / "Documents" / "DocStyle_Vault"
        chroma_path = vault_dir / ".chroma"
        chroma_path.mkdir(parents=True, exist_ok=True)
        # PersistentClient automatically saves to the specified path
        _chroma_client = chromadb.PersistentClient(path=str(chroma_path))
        # We will use the default SentenceTransformers embedding function
        _collection = _chroma_client.get_or_create_collection(
            name="docstyle_vault",
            metadata={"hnsw:space": "cosine"}
        )
    return _collection

def chunk_markdown(content: str) -> list[str]:
    """
    Split a markdown string into meaningful chunks.
    For simplicity, we split by headers (##) or double newlines.
    """
    # Naive split by paragraphs or headers
    raw_chunks = re.split(r'\n\n+', content)
    
    # Filter out empty or extremely short chunks
    chunks = [c.strip() for c in raw_chunks if len(c.strip()) > 10]
    
    # Optional: If a chunk is too long, we could further split it here. 
    # For MVP RAG, simple paragraph splitting is usually quite effective.
    return chunks

def index_document(file_path: str):
    """
    Reads a markdown file, chunks it, and updates its vectors in ChromaDB.
    """
    path_obj = Path(file_path)
    if not path_obj.exists() or path_obj.suffix != '.md':
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path} for indexing: {e}")
        return

    collection = get_chroma_collection()
    
    # 1. Delete old chunks for this file
    # Chroma allows deleting by metadata matches
    collection.delete(where={"source": file_path})

    chunks = chunk_markdown(content)
    if not chunks:
        return

    # 2. Add new chunks
    ids = [f"{path_obj.name}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"source": file_path, "filename": path_obj.name} for _ in range(len(chunks))]

    collection.add(
        documents=chunks,
        metadatas=metadatas,
        ids=ids
    )

def query_vault(query_text: str, n_results: int = 5) -> list[dict]:
    """
    Semantic search across the entire vault.
    Returns a list of dicts: {"content": str, "source": str, "filename": str, "distance": float}
    """
    collection = get_chroma_collection()
    
    # Perform semantic search
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    
    output = []
    if results and results.get("documents") and len(results["documents"]) > 0:
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0] if "distances" in results else [0.0]*len(docs)
        
        for d, m, dist in zip(docs, metas, distances):
            output.append({
                "content": d,
                "source": m.get("source", ""),
                "filename": m.get("filename", ""),
                "distance": dist
            })
            
    return output

def sync_entire_vault():
    """
    Scans the vault directory and indexes all .md files.
    """
    vault_dir = Path.home() / "Documents" / "DocStyle_Vault"
    if not vault_dir.exists():
        return
        
    for item in vault_dir.glob("*.md"):
        try:
            index_document(str(item))
        except Exception as e:
            print(f"Failed to index {item}: {e}")


"""
Pipeline RAG - Rapports d'etudes de marche (GenZ vs Adult)
Extraction PDF -> Chunking -> Embeddings -> Insertion Supabase (pgvector)

Installation :
    pip install pymupdf sentence-transformers psycopg2-binary python-dotenv

Setup Supabase (a faire une fois dans l'editeur SQL du dashboard) :
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE TABLE rag_chunks (
        id SERIAL PRIMARY KEY,
        text TEXT,
        source TEXT,
        audience TEXT,
        embedding VECTOR(384)
    );

Config :
    Cree un fichier .env a cote de ce script avec :
    SUPABASE_DB_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
    (recuperable dans Supabase -> Settings -> Database -> Connection string -> URI)
"""

import os
import glob
from pathlib import Path

import fitz  # pymupdf
import psycopg2
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

# --- Config ---
DB_URL = os.environ["SUPABASE_DB_URL"]
EMBED_MODEL = "BAAI/bge-small-en-v1.5"  # 384 dims - change si tes rapports ne sont pas en anglais
CHUNK_SIZE = 400   # mots par chunk
OVERLAP = 50       # mots de chevauchement entre chunks

# Dossiers attendus :
#   rag_sources/GenZ/*.pdf
#   rag_sources/Adults/*.pdf
REPORTS = {
    "genz": "rag_sources/GenZ/*.pdf",
    "adult": "rag_sources/Adults/*.pdf",
}


def extract_text(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return text


def chunk_text(text: str, source: str, audience: str,
                chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[dict]:
    words = text.split()
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        chunk_words = words[i:i + chunk_size]
        if len(chunk_words) < 20:  # ignore les micro-chunks en fin de doc
            continue
        chunks.append({
            "text": " ".join(chunk_words),
            "source": source,
            "audience": audience,
        })
    return chunks


def build_all_chunks() -> list[dict]:
    all_chunks = []
    for audience, pattern in REPORTS.items():
        pdf_files = glob.glob(pattern)
        if not pdf_files:
            print(f"[!] Aucun PDF trouve pour '{audience}' avec le pattern {pattern}")
            continue
        for pdf_path in pdf_files:
            source_name = Path(pdf_path).stem
            print(f"  Extraction: {source_name} ({audience})")
            text = extract_text(pdf_path)
            chunks = chunk_text(text, source_name, audience)
            all_chunks.extend(chunks)
            print(f"    -> {len(chunks)} chunks")
    return all_chunks


def embed_and_insert(chunks: list[dict]):
    print(f"\nChargement du modele d'embedding ({EMBED_MODEL})...")
    model = SentenceTransformer(EMBED_MODEL)

    print("Calcul des embeddings...")
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)

    print("Insertion dans Supabase...")
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    insert_query = """
        INSERT INTO rag_chunks (text, source, audience, embedding)
        VALUES (%s, %s, %s, %s)
    """
    for chunk, emb in zip(chunks, embeddings):
        cur.execute(insert_query, (
            chunk["text"],
            chunk["source"],
            chunk["audience"],
            emb.tolist(),
        ))

    conn.commit()
    cur.close()
    conn.close()
    print(f"Termine : {len(chunks)} chunks inseres dans rag_chunks.")


def search(query: str, top_k: int = 5, audience: str | None = None):
    """Test de retrieval rapide."""
    model = SentenceTransformer(EMBED_MODEL)
    query_emb = model.encode([query], normalize_embeddings=True)[0].tolist()

    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    if audience:
        cur.execute("""
            SELECT text, source, audience, embedding <=> %s::vector AS distance
            FROM rag_chunks
            WHERE audience = %s
            ORDER BY distance
            LIMIT %s
        """, (query_emb, audience, top_k))
    else:
        cur.execute("""
            SELECT text, source, audience, embedding <=> %s::vector AS distance
            FROM rag_chunks
            ORDER BY distance
            LIMIT %s
        """, (query_emb, top_k))

    results = cur.fetchall()
    cur.close()
    conn.close()

    for text, source, aud, dist in results:
        print(f"\n[{aud}] {source} (distance: {dist:.4f})")
        print(text[:300] + "...")

    return results


if __name__ == "__main__":
    print("=== Pipeline RAG - Rapports d'etudes de marche ===\n")
    chunks = build_all_chunks()
    print(f"\nTotal : {len(chunks)} chunks sur {sum(1 for _ in glob.glob('rag_sources/*/*.pdf'))} PDF")

    if chunks:
        embed_and_insert(chunks)

        # Test rapide
        print("\n=== Test de retrieval ===")
        search("pourquoi cibler les jeunes avec des offres sans frais", top_k=3)

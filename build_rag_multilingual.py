"""
Pipeline RAG - Rapports d'etudes de marche (GenZ vs Adult)
Version MULTILINGUE : remplace bge-small-en-v1.5 (384 dim, optimise anglais)
par paraphrase-multilingual-mpnet-base-v2 (768 dim) pour ne plus desavantager
les sources non-anglaises (ex: La-generation-Z-et-la-banque-de-detail, en francais).

Ecrit dans une NOUVELLE table (rag_chunks_multilingual) separee de l'ancienne
(rag_chunks) -- permet de comparer les deux avant de basculer l'app dessus.

Installation :
    pip install pymupdf sentence-transformers psycopg2-binary python-dotenv

Setup Supabase (a faire une fois dans l'editeur SQL du dashboard) :
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE TABLE rag_chunks_multilingual (
        id SERIAL PRIMARY KEY,
        text TEXT,
        source TEXT,
        audience TEXT,
        embedding VECTOR(768)
    );

Config :
    Meme .env que la version originale (SUPABASE_DB_URL=...)
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
EMBED_MODEL = "paraphrase-multilingual-mpnet-base-v2"  # 768 dim, multilingue (FR/EN/NL...)
TABLE_NAME = "rag_chunks_multilingual"  # separee de rag_chunks (ancienne, 384 dim)
CHUNK_SIZE = 400   # mots par chunk
OVERLAP = 50       # mots de chevauchement entre chunks

# Dossiers attendus (identiques a la version originale) :
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
            if len(text.strip()) < 100:
                print(f"    [!] Texte quasi vide ({len(text.strip())} caracteres) — "
                      f"probablement un PDF scanne sans couche de texte, ignore.")
                continue
            chunks = chunk_text(text, source_name, audience)
            all_chunks.extend(chunks)
            print(f"    -> {len(chunks)} chunks")
    return all_chunks


def embed_and_insert(chunks: list[dict]):
    print(f"\nChargement du modele d'embedding multilingue ({EMBED_MODEL})...")
    print("(premier lancement : telechargement ~1GB, plus lourd que bge-small)")
    model = SentenceTransformer(EMBED_MODEL)

    print("Calcul des embeddings...")
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)

    print(f"Insertion dans Supabase (table: {TABLE_NAME})...")
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    insert_query = f"""
        INSERT INTO {TABLE_NAME} (text, source, audience, embedding)
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
    print(f"Termine : {len(chunks)} chunks inseres dans {TABLE_NAME}.")


def search(query: str, top_k: int = 5, audience: str | None = None):
    """Test de retrieval rapide, sur la nouvelle table multilingue."""
    model = SentenceTransformer(EMBED_MODEL)
    query_emb = model.encode([query], normalize_embeddings=True)[0].tolist()

    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    if audience:
        cur.execute(f"""
            SELECT text, source, audience, embedding <=> %s::vector AS distance
            FROM {TABLE_NAME}
            WHERE audience = %s
            ORDER BY distance
            LIMIT %s
        """, (query_emb, audience, top_k))
    else:
        cur.execute(f"""
            SELECT text, source, audience, embedding <=> %s::vector AS distance
            FROM {TABLE_NAME}
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


def compare_source_diversity():
    """Verifie combien de chunks par source ont ete crees, pour confirmer
    que la source francaise n'est plus anormalement sous-representee."""
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute(f"SELECT source, COUNT(*) FROM {TABLE_NAME} GROUP BY source ORDER BY COUNT(*) DESC")
    print("\n=== Chunks par source (nouvelle table) ===")
    for source, count in cur.fetchall():
        print(f"  {source}: {count}")
    cur.close()
    conn.close()


if __name__ == "__main__":
    print("=== Pipeline RAG multilingue - Rapports d'etudes de marche ===\n")
    chunks = build_all_chunks()
    print(f"\nTotal : {len(chunks)} chunks sur {sum(1 for _ in glob.glob('rag_sources/*/*.pdf'))} PDF")

    if chunks:
        embed_and_insert(chunks)
        compare_source_diversity()

        # Test rapide : la question ou la source francaise aurait du remonter
        print("\n=== Test de retrieval (recherche en francais) ===")
        search("comment les banques doivent communiquer avec la generation Z", top_k=5)
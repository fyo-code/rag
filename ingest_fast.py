"""
High-Performance Data Ingestion Pipeline v2
With rate limiting to avoid 429 errors
"""

import os
import shutil
import time
import pandas as pd
import duckdb
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from tqdm import tqdm
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import chromadb

# Load environment
load_dotenv()

# Configuration
CSV_FILE = "reclamatii.csv"
DUCKDB_FILE = "reclamatii.duckdb"
CHROMA_DIR = "./chroma_db"
BATCH_SIZE = 100
MAX_WORKERS = 5  # Reduced to avoid rate limiting
DELAY_BETWEEN_BATCHES = 0.5  # Seconds between batch submissions


def load_and_clean_csv() -> pd.DataFrame:
    """Load CSV and apply all cleaning transformations."""
    print("📂 Loading CSV...")
    df = pd.read_csv(CSV_FILE, encoding="utf-8")
    print(f"   Loaded {len(df):,} rows")

    # 1. Date Conversion
    date_columns = ["DATA RECLAMATIE", "DATA FACTURA", "DATA COMANDA"]
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="%d.%m.%Y", errors="coerce")
            df[col] = df[col].where(df[col].notna(), None)
    print("   ✅ Dates converted")

    # 2. Numeric Cleaning
    if "Valoare Articole Reclamate" in df.columns:
        df["Valoare Articole Reclamate"] = pd.to_numeric(
            df["Valoare Articole Reclamate"], errors="coerce"
        ).fillna(0.0)

    if "Cantitate Reclamata" in df.columns:
        df["Cantitate Reclamata"] = pd.to_numeric(
            df["Cantitate Reclamata"], errors="coerce"
        ).fillna(0).astype(int)
    print("   ✅ Numerics cleaned")

    # 3. String Cleaning
    text_columns = ["OBSERVATII", "DESCRIERE", "MOTIV RECLAMATIE", "ARTICOL DENUMIRE",
                    "RAION", "MODALITATE REZOLVARE", "MAGAZIN", "FURNIZOR"]
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).replace("#null", "")
    print("   ✅ Text cleaned")

    return df


def ingest_to_duckdb(df: pd.DataFrame) -> None:
    """Fast bulk insert to DuckDB."""
    print("\n🦆 Building DuckDB...")
    
    if os.path.exists(DUCKDB_FILE):
        os.remove(DUCKDB_FILE)
    
    con = duckdb.connect(DUCKDB_FILE)
    
    con.execute("""
        CREATE TABLE complaints (
            id INTEGER,
            date_complaint DATE,
            product_name VARCHAR,
            category VARCHAR,
            issue_type VARCHAR,
            description TEXT,
            status VARCHAR,
            value DOUBLE,
            shop VARCHAR,
            supplier VARCHAR
        )
    """)
    
    insert_df = pd.DataFrame({
        "id": df["NR RECLAMATIE"],
        "date_complaint": df["DATA RECLAMATIE"],
        "product_name": df["ARTICOL DENUMIRE"],
        "category": df["RAION"],
        "issue_type": df["MOTIV RECLAMATIE"],
        "description": df["DESCRIERE"],
        "status": df["MODALITATE REZOLVARE"],
        "value": df["Valoare Articole Reclamate"],
        "shop": df["MAGAZIN"],
        "supplier": df["FURNIZOR"]
    })
    
    con.execute("INSERT INTO complaints SELECT * FROM insert_df")
    
    count = con.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
    print(f"   ✅ Inserted {count:,} rows")
    
    con.close()


def prepare_documents(df: pd.DataFrame) -> tuple:
    """Prepare all documents for embedding."""
    texts = []
    metadatas = []
    ids = []
    
    for idx, row in df.iterrows():
        text = (
            f"MOTIV: {row['MOTIV RECLAMATIE']} | "
            f"DESC: {row['DESCRIERE']} | "
            f"OBS: {row['OBSERVATII']} | "
            f"PROD: {row['ARTICOL DENUMIRE']}"
        )
        
        if text == "MOTIV:  | DESC:  | OBS:  | PROD: ":
            continue
        
        date_val = row["DATA RECLAMATIE"]
        date_str = date_val.strftime("%Y-%m-%d") if pd.notna(date_val) and hasattr(date_val, 'strftime') else ""
        
        texts.append(text)
        metadatas.append({
            "id": int(row["NR RECLAMATIE"]),
            "date": date_str,
            "category": str(row["RAION"])
        })
        ids.append(f"doc_{idx}")
    
    return texts, metadatas, ids


def embed_batch_with_retry(batch_data, embeddings, collection, max_retries=3):
    """Embed a single batch with retry logic."""
    texts, metadatas, ids, batch_num = batch_data
    
    for attempt in range(max_retries):
        try:
            # Get embeddings
            vectors = embeddings.embed_documents(texts)
            
            # Add to collection
            collection.add(
                embeddings=vectors,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            return {"success": True, "batch": batch_num, "count": len(texts)}
        
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                # Rate limited - wait and retry
                wait_time = (attempt + 1) * 2  # Exponential backoff
                time.sleep(wait_time)
                continue
            else:
                return {"success": False, "batch": batch_num, "error": error_msg[:100]}
    
    return {"success": False, "batch": batch_num, "error": "Max retries exceeded (rate limit)"}


def ingest_to_chroma_throttled(df: pd.DataFrame) -> None:
    """Throttled parallel vector embedding."""
    print("\n🔮 Building ChromaDB (Throttled Parallel)...")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("   ❌ GOOGLE_API_KEY not found!")
        return
    
    # Clear existing
    if os.path.exists(CHROMA_DIR):
        shutil.rmtree(CHROMA_DIR)
    
    # Initialize embeddings
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=api_key
    )
    
    # Initialize Chroma
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_or_create_collection(
        name="complaints",
        metadata={"hnsw:space": "cosine"}
    )
    
    # Prepare documents
    print("   Preparing documents...")
    texts, metadatas, ids = prepare_documents(df)
    print(f"   Prepared {len(texts):,} documents")
    
    # Create batches
    batches = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch_num = i // BATCH_SIZE + 1
        batches.append((
            texts[i:i + BATCH_SIZE],
            metadatas[i:i + BATCH_SIZE],
            ids[i:i + BATCH_SIZE],
            batch_num
        ))
    
    total_batches = len(batches)
    print(f"   {total_batches} batches | {MAX_WORKERS} workers | {DELAY_BETWEEN_BATCHES}s delay")
    
    # Process with throttling
    success_count = 0
    error_count = 0
    
    with tqdm(total=total_batches, desc="   Embedding", unit="batch") as pbar:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = []
            
            for batch in batches:
                future = executor.submit(
                    embed_batch_with_retry, 
                    batch, 
                    embeddings, 
                    collection
                )
                futures.append(future)
                time.sleep(DELAY_BETWEEN_BATCHES)  # Throttle submissions
            
            for future in as_completed(futures):
                result = future.result()
                if result["success"]:
                    success_count += result["count"]
                else:
                    error_count += 1
                pbar.update(1)
    
    print(f"\n   ✅ Embedded {success_count:,} documents")
    if error_count > 0:
        print(f"   ⚠️ {error_count} batches had errors")
    
    print(f"   💾 Saved to '{CHROMA_DIR}'")


def main():
    print("=" * 60)
    print("🚀 INGESTION PIPELINE v2 (Rate-Limited)")
    print("=" * 60)
    
    if not os.path.exists(CSV_FILE):
        print(f"❌ CSV not found: {CSV_FILE}")
        return
    
    df = load_and_clean_csv()
    ingest_to_duckdb(df)
    ingest_to_chroma_throttled(df)
    
    print("\n" + "=" * 60)
    print("✅ COMPLETE!")
    print("=" * 60)
    print(f"\n📊 DuckDB: {DUCKDB_FILE}")
    print(f"🔮 ChromaDB: {CHROMA_DIR}")


if __name__ == "__main__":
    main()

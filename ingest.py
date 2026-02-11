"""
Data Ingestion Pipeline for Complaints (Reclamatii)
Loads CSV -> DuckDB (analytics) + ChromaDB (vector search)
"""

import os
import pandas as pd
import duckdb
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

# Load environment
load_dotenv()

# Configuration
CSV_FILE = "reclamatii.csv"
DUCKDB_FILE = "reclamatii.duckdb"
CHROMA_DIR = "./chroma_db"
BATCH_SIZE = 100


def load_and_clean_csv() -> pd.DataFrame:
    """Load CSV and apply all cleaning transformations."""
    print("📂 Loading CSV...")
    df = pd.read_csv(CSV_FILE, encoding="utf-8")
    print(f"   Loaded {len(df):,} rows")

    # 1. Date Conversion (DD.MM.YYYY -> YYYY-MM-DD)
    date_columns = ["DATA RECLAMATIE", "DATA FACTURA", "DATA COMANDA"]
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(
                df[col], 
                format="%d.%m.%Y", 
                errors="coerce"
            )
            # Convert NaT to None for SQL NULL compatibility
            df[col] = df[col].where(df[col].notna(), None)
    print("   ✅ Date columns converted")

    # 2. Numeric Cleaning
    if "Valoare Articole Reclamate" in df.columns:
        df["Valoare Articole Reclamate"] = pd.to_numeric(
            df["Valoare Articole Reclamate"], 
            errors="coerce"
        ).fillna(0.0)

    if "Cantitate Reclamata" in df.columns:
        df["Cantitate Reclamata"] = pd.to_numeric(
            df["Cantitate Reclamata"], 
            errors="coerce"
        ).fillna(0).astype(int)
    print("   ✅ Numeric columns cleaned")

    # 3. String Cleaning - fill NaN with empty string
    text_columns = ["OBSERVATII", "DESCRIERE", "MOTIV RECLAMATIE", "ARTICOL DENUMIRE"]
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)
            # Replace #null with empty string
            df[col] = df[col].replace("#null", "")
    print("   ✅ Text columns cleaned")

    # 4. Clean other string columns
    string_columns = ["RAION", "MODALITATE REZOLVARE", "MAGAZIN", "FURNIZOR"]
    for col in string_columns:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).replace("#null", "")

    return df


def ingest_to_duckdb(df: pd.DataFrame) -> None:
    """Create DuckDB table and insert cleaned data."""
    print("\n🦆 Ingesting to DuckDB...")
    
    # Connect to DuckDB
    con = duckdb.connect(DUCKDB_FILE)
    
    # Drop and create table
    con.execute("DROP TABLE IF EXISTS complaints")
    
    con.execute("""
        CREATE TABLE complaints (
            id INTEGER,
            date_complaint DATE,
            date_invoice DATE,
            date_order DATE,
            product_name VARCHAR,
            product_code VARCHAR,
            category VARCHAR,
            issue_type VARCHAR,
            description TEXT,
            observations TEXT,
            status VARCHAR,
            value DOUBLE,
            quantity INTEGER,
            shop VARCHAR,
            supplier VARCHAR,
            customer_name VARCHAR,
            order_id VARCHAR
        )
    """)
    
    # Prepare data for insertion
    insert_df = pd.DataFrame({
        "id": df["NR RECLAMATIE"],
        "date_complaint": df["DATA RECLAMATIE"],
        "date_invoice": df["DATA FACTURA"],
        "date_order": df["DATA COMANDA"],
        "product_name": df["ARTICOL DENUMIRE"],
        "product_code": df.get("ARTICOL COD", ""),
        "category": df["RAION"],
        "issue_type": df["MOTIV RECLAMATIE"],
        "description": df["DESCRIERE"],
        "observations": df["OBSERVATII"],
        "status": df["MODALITATE REZOLVARE"],
        "value": df["Valoare Articole Reclamate"],
        "quantity": df["Cantitate Reclamata"],
        "shop": df["MAGAZIN"],
        "supplier": df["FURNIZOR"],
        "customer_name": df.get("NUME CLIENT", ""),
        "order_id": df.get("ID COMANDA", "").astype(str)
    })
    
    # Insert data
    con.execute("INSERT INTO complaints SELECT * FROM insert_df")
    
    # Verify
    count = con.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
    print(f"   ✅ Inserted {count:,} rows into 'complaints' table")
    
    # Show sample
    print("\n   Sample data:")
    sample = con.execute("""
        SELECT id, date_complaint, category, issue_type, value 
        FROM complaints 
        LIMIT 3
    """).fetchdf()
    print(sample.to_string(index=False))
    
    con.close()


def ingest_to_chroma(df: pd.DataFrame) -> None:
    """Create vector embeddings and store in ChromaDB."""
    print("\n🔮 Ingesting to ChromaDB...")
    
    # Initialize embeddings
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("   ❌ GOOGLE_API_KEY not found in .env")
        return
    
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=api_key
    )
    
    # Initialize Chroma - clear existing data
    import shutil
    if os.path.exists(CHROMA_DIR):
        shutil.rmtree(CHROMA_DIR)
        print("   Cleared existing ChromaDB data")
    
    vectorstore = Chroma(
        collection_name="complaints",
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR
    )
    
    # Prepare documents
    print("   Preparing documents...")
    texts = []
    metadatas = []
    ids = []
    
    for idx, row in df.iterrows():
        # Create searchable text content
        text = (
            f"MOTIV: {row['MOTIV RECLAMATIE']} | "
            f"DESCRIERE: {row['DESCRIERE']} | "
            f"OBSERVATII: {row['OBSERVATII']} | "
            f"PRODUS: {row['ARTICOL DENUMIRE']}"
        )
        
        # Skip empty texts
        if text.strip() == "MOTIV:  | DESCRIERE:  | OBSERVATII:  | PRODUS: ":
            continue
        
        # Format date for metadata
        date_val = row["DATA RECLAMATIE"]
        if pd.notna(date_val):
            date_str = date_val.strftime("%Y-%m-%d") if hasattr(date_val, 'strftime') else str(date_val)
        else:
            date_str = ""
        
        texts.append(text)
        metadatas.append({
            "complaint_id": int(row["NR RECLAMATIE"]),
            "date": date_str,
            "category": str(row["RAION"])
        })
        # Use row index to ensure unique IDs
        ids.append(f"row_{idx}_id_{row['NR RECLAMATIE']}")
    
    print(f"   Prepared {len(texts):,} documents for embedding")
    
    # Process in batches
    total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE
    
    for i in range(0, len(texts), BATCH_SIZE):
        batch_num = i // BATCH_SIZE + 1
        batch_texts = texts[i:i + BATCH_SIZE]
        batch_metadatas = metadatas[i:i + BATCH_SIZE]
        batch_ids = ids[i:i + BATCH_SIZE]
        
        try:
            vectorstore.add_texts(
                texts=batch_texts,
                metadatas=batch_metadatas,
                ids=batch_ids
            )
            print(f"   📦 Batch {batch_num}/{total_batches} complete ({len(batch_texts)} docs)")
        except Exception as e:
            print(f"   ⚠️ Batch {batch_num} error: {e}")
            continue
    
    print(f"   ✅ ChromaDB saved to '{CHROMA_DIR}'")


def main():
    """Run the full ingestion pipeline."""
    print("=" * 50)
    print("🚀 COMPLAINTS DATA INGESTION PIPELINE")
    print("=" * 50)
    
    # Check CSV exists
    if not os.path.exists(CSV_FILE):
        print(f"❌ CSV file not found: {CSV_FILE}")
        print("   Run setup_data.py first!")
        return
    
    # Load and clean
    df = load_and_clean_csv()
    
    # Ingest to DuckDB
    ingest_to_duckdb(df)
    
    # Ingest to ChromaDB
    ingest_to_chroma(df)
    
    print("\n" + "=" * 50)
    print("✅ INGESTION COMPLETE!")
    print("=" * 50)
    print(f"\n📊 DuckDB: {DUCKDB_FILE}")
    print(f"🔮 ChromaDB: {CHROMA_DIR}")
    print("\nNext steps:")
    print("  - Query DuckDB: duckdb.connect('reclamatii.duckdb')")
    print("  - Search vectors: Use ChromaDB similarity search")


if __name__ == "__main__":
    main()

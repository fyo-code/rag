"""
Database module - DuckDB loader and query executor
Loads reclamatii.csv into DuckDB with proper schema
"""

import os
import duckdb
import pandas as pd
from pathlib import Path

# Database file path
DB_PATH = Path(__file__).parent.parent / "reclamatii.duckdb"
CSV_PATH = Path(__file__).parent.parent / "reclamatii.csv"

# Global connection
_connection = None


def get_connection() -> duckdb.DuckDBPyConnection:
    """Get or create DuckDB connection."""
    global _connection
    if _connection is None:
        _connection = duckdb.connect(str(DB_PATH))
    return _connection


def init_database() -> bool:
    """Initialize database from CSV if needed."""
    con = get_connection()
    
    # Check if table exists
    tables = con.execute("SHOW TABLES").fetchall()
    if any("complaints" in str(t) for t in tables):
        count = con.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
        print(f"✅ Database ready: {count:,} complaints")
        return True
    
    # Load from CSV
    if not CSV_PATH.exists():
        print(f"❌ CSV not found: {CSV_PATH}")
        return False
    
    print("📂 Loading CSV into DuckDB...")
    df = pd.read_csv(CSV_PATH, encoding="utf-8")
    
    # Clean date columns
    date_cols = ["DATA RECLAMATIE", "DATA FACTURA", "DATA COMANDA"]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="%d.%m.%Y", errors="coerce")
    
    # Clean numeric columns
    if "Valoare Articole Reclamate" in df.columns:
        df["Valoare Articole Reclamate"] = pd.to_numeric(
            df["Valoare Articole Reclamate"], errors="coerce"
        ).fillna(0.0)
    
    if "Cantitate Reclamata" in df.columns:
        df["Cantitate Reclamata"] = pd.to_numeric(
            df["Cantitate Reclamata"], errors="coerce"
        ).fillna(0).astype(int)
    
    # Clean string columns
    text_cols = df.select_dtypes(include=["object"]).columns
    for col in text_cols:
        df[col] = df[col].fillna("").astype(str).replace("#null", "")
    
    # Rename columns to clean SQL names
    column_mapping = {
        "NR RECLAMATIE": "nr_reclamatie",
        "RAION": "raion",
        "PM": "pm",
        "OBSERVATII": "observatii",
        "NUME CLIENT": "nume_client",
        "NR COMANDA": "nr_comanda",
        "ID COMANDA": "id_comanda",
        "GRUPA MEDIU VANZARE": "grup_vanzare",
        "FURNIZOR": "furnizor",
        "ECHIPA LIVRARE COMANDA": "echipa_livrare",
        "DATA FACTURA": "data_factura",
        "DATA COMANDA": "data_comanda",
        "DATA RECLAMATIE": "data_reclamatie",
        "MAGAZIN": "magazin",
        "ARTICOL COD": "articol_cod",
        "ID CLIENT": "id_client",
        "ARTICOL DENUMIRE": "articol_denumire",
        "MODALITATE REZOLVARE": "modalitate_rezolvare",
        "MOTIV RECLAMATIE": "motiv_reclamatie",
        "DESCRIERE": "descriere",
        "MOD LIVRARE": "mod_livrare",
        "FURNIZOR EXT": "furnizor_ext",
        "RESPONSABIL COMANDA": "responsabil_comanda",
        "Cantitate Reclamata": "cantitate",
        "Valoare Articole Reclamate": "valoare"
    }
    df = df.rename(columns=column_mapping)
    
    # Create table
    con.execute("DROP TABLE IF EXISTS complaints")
    con.execute("CREATE TABLE complaints AS SELECT * FROM df")
    
    count = con.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
    print(f"✅ Loaded {count:,} complaints into DuckDB")
    
    return True


def execute_query(sql: str) -> tuple[list[dict], list[str], str | None]:
    """
    Execute SQL query and return results.
    Returns: (rows as list of dicts, column names, error message or None)
    """
    con = get_connection()
    try:
        result = con.execute(sql)
        columns = [desc[0] for desc in result.description]
        rows = result.fetchall()
        
        # Convert to list of dicts
        data = [dict(zip(columns, row)) for row in rows]
        
        return data, columns, None
    except Exception as e:
        return [], [], str(e)


def get_schema() -> str:
    """Get table schema description for LLM context."""
    return """
TABLE: complaints (reclamații clienți Mobexpert)

COLUMNS:
- nr_reclamatie (INTEGER): Numărul reclamației (ID unic)
- raion (VARCHAR): Categoria/zona produsului (MOBILIER GENERAL, BUCATARII, ONLINE, etc.)
- pm (VARCHAR): Product Manager responsabil
- observatii (TEXT): Observații despre defect
- nume_client (VARCHAR): Numele clientului
- nr_comanda (INTEGER): Numărul comenzii (resetat anual)
- id_comanda (VARCHAR): ID unic comandă
- grup_vanzare (VARCHAR): Canal/grupa mediu de vânzare (GRUPA MEDIU VANZARE - online, offline, sau gol). Aceasta coloană este cunoscută și ca "grupa mediu" sau "mediu vânzare"
- furnizor (VARCHAR): Furnizorul produsului
- echipa_livrare (VARCHAR): Echipa de livrare/montaj
- data_factura (DATE): Data facturii
- data_comanda (DATE): Data comenzii
- data_reclamatie (DATE): Data înregistrării reclamației
- magazin (VARCHAR): Magazinul de unde s-a cumpărat
- articol_cod (VARCHAR): Codul produsului
- id_client (INTEGER): ID unic client
- articol_denumire (VARCHAR): Denumirea completă a produsului
- modalitate_rezolvare (VARCHAR): Cum s-a rezolvat reclamația
- motiv_reclamatie (VARCHAR): Motivul reclamației
- descriere (TEXT): Descrierea detaliată a problemei
- mod_livrare (VARCHAR): Tipul livrării (MMC, CDD, CEX, CLG)
- furnizor_ext (VARCHAR): Fabrica/furnizorul extern
- responsabil_comanda (VARCHAR): Vânzătorul responsabil
- cantitate (INTEGER): Cantitatea de produse reclamate
- valoare (DOUBLE): Valoarea produselor reclamate (RON)

NOTES:
- Date format în baza de date: YYYY-MM-DD
- Pentru perioade, folosește: data_reclamatie BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD'
- Pentru an, folosește: YEAR(data_reclamatie) = YYYY
- Pentru lună, folosește: MONTH(data_reclamatie) = M
"""


def get_sample_data() -> list[dict]:
    """Get sample data for testing."""
    con = get_connection()
    result = con.execute("""
        SELECT nr_reclamatie, data_reclamatie, raion, motiv_reclamatie, valoare
        FROM complaints
        LIMIT 5
    """)
    columns = [desc[0] for desc in result.description]
    rows = result.fetchall()
    return [dict(zip(columns, row)) for row in rows]


def get_stats() -> dict:
    """Get basic statistics for dashboard."""
    con = get_connection()
    
    stats = {}
    
    # Total complaints
    stats["total"] = con.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
    
    # Total value
    stats["total_value"] = con.execute("SELECT SUM(valoare) FROM complaints").fetchone()[0]
    
    # Date range
    date_range = con.execute("""
        SELECT MIN(data_reclamatie), MAX(data_reclamatie) FROM complaints
    """).fetchone()
    stats["date_min"] = str(date_range[0]) if date_range[0] else None
    stats["date_max"] = str(date_range[1]) if date_range[1] else None
    
    # Top categories
    top_raion = con.execute("""
        SELECT raion, COUNT(*) as cnt
        FROM complaints
        GROUP BY raion
        ORDER BY cnt DESC
        LIMIT 5
    """).fetchall()
    stats["top_categories"] = [{"name": r[0], "count": r[1]} for r in top_raion]
    
    # Top reasons
    top_reasons = con.execute("""
        SELECT motiv_reclamatie, COUNT(*) as cnt
        FROM complaints
        WHERE motiv_reclamatie != ''
        GROUP BY motiv_reclamatie
        ORDER BY cnt DESC
        LIMIT 5
    """).fetchall()
    stats["top_reasons"] = [{"name": r[0], "count": r[1]} for r in top_reasons]
    
    return stats

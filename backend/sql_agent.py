"""
SQL Agent - Text-to-SQL conversion using Gemini 3 Flash Preview
Converts natural language questions to SQL queries
Smart aggregation: prefers charts/insights over raw data dumps
"""

import os
import json
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv
from database import get_schema, execute_query

load_dotenv()

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Model configuration - Using Gemini 3 Flash for speed + accuracy
MODEL = "gemini-3-flash-preview"


def get_sql_system_prompt() -> str:
    """System prompt for SQL generation - prefers aggregations over raw dumps."""
    schema = get_schema()
    return f"""Ești un expert SQL pentru DuckDB. Generează interogări SQL precise bazate pe întrebările utilizatorului.

{schema}

REGULI STRICTE:
1. Returnează DOAR interogarea SQL, fără explicații
2. Folosește NUMAI coloanele din schema de mai sus
3. Pentru date, folosește formatul 'YYYY-MM-DD'
4. Pentru anul curent, folosește YEAR(data_reclamatie) = 2024 sau 2025
5. Folosește alias-uri clare pentru coloane în rezultate
6. Pentru TOP N, folosește ORDER BY ... DESC LIMIT N
7. Tratează valorile goale ca și '' (string gol), nu NULL
8. Pentru căutări text, folosește ILIKE '%text%'

REGULI CRITICE PENTRU AGREGĂRI (FOARTE IMPORTANT):
9. NU folosi NICIODATĂ "SELECT *" pentru întrebări generale - ÎNTOTDEAUNA agregă datele
10. Când utilizatorul întreabă despre reclamații într-o perioadă (ex: "reclamații în 2024"), 
    generează o interogare de SUMARIZARE cu GROUP BY, NU o listare a tuturor rândurilor
11. Pentru întrebări despre o perioadă de timp, preferă defalcare pe LUNI:
    SELECT MONTHNAME(data_reclamatie) as luna, COUNT(*) as numar_reclamatii 
    FROM complaints WHERE YEAR(data_reclamatie) = YYYY GROUP BY luna, MONTH(data_reclamatie) ORDER BY MONTH(data_reclamatie)
12. Pentru întrebări de tipul "câte", "cât", "total", folosește COUNT(*), SUM(), AVG()
13. LIMITA maximă de rânduri returnate: 150. Folosește LIMIT 150 dacă query-ul ar putea returna mai mult
14. Dacă utilizatorul cere explicit "toate" sau "lista", returnează cu LIMIT 150 și coloane relevante (nu SELECT *)
15. Selectează DOAR coloanele relevante, niciodată SELECT *

CATEGORII DE INTEROGĂRI ȘI CE SĂ GENEREZI:

A) ÎNTREBĂRI CANTITATIVE ("câte reclamații", "reclamații în 2024", "total"):
   → GROUP BY pe cea mai relevantă dimensiune (lună, raion, PM, furnizor)
   → Exemplu: SELECT MONTHNAME(data_reclamatie) as luna, COUNT(*) as numar FROM complaints WHERE YEAR(data_reclamatie) = 2024 GROUP BY luna, MONTH(data_reclamatie) ORDER BY MONTH(data_reclamatie)

B) ÎNTREBĂRI DE TOP/CLASAMENT ("top furnizori", "PM cu cele mai multe"):
   → GROUP BY + ORDER BY DESC + LIMIT 10
   → Exemplu: SELECT pm, COUNT(*) as numar FROM complaints WHERE pm != '' GROUP BY pm ORDER BY numar DESC LIMIT 10

C) ÎNTREBĂRI DE VALOARE ("valoare reclamații", "cost"):
   → SUM(valoare) cu GROUP BY relevant
   → Exemplu: SELECT furnizor, SUM(valoare) as valoare_totala FROM complaints WHERE furnizor != '' GROUP BY furnizor ORDER BY valoare_totala DESC LIMIT 10

D) ÎNTREBĂRI SPECIFICE ("reclamația 72335", "clientul X"):
   → SELECT coloane specifice WHERE condiție exactă LIMIT 5

E) ÎNTREBĂRI DE TREND ("evoluție", "pe luni", "comparație"):
   → GROUP BY cu MONTH() sau YEAR() + ORDER BY cronologic

EXEMPLE:
Q: "Câte reclamații au fost în 2024?"
A: SELECT MONTHNAME(data_reclamatie) as luna, COUNT(*) as numar_reclamatii FROM complaints WHERE YEAR(data_reclamatie) = 2024 GROUP BY luna, MONTH(data_reclamatie) ORDER BY MONTH(data_reclamatie)

Q: "Reclamații în 2024"
A: SELECT MONTHNAME(data_reclamatie) as luna, COUNT(*) as numar_reclamatii FROM complaints WHERE YEAR(data_reclamatie) = 2024 GROUP BY luna, MONTH(data_reclamatie) ORDER BY MONTH(data_reclamatie)

Q: "Care PM are cele mai multe reclamații?"
A: SELECT pm, COUNT(*) as numar_reclamatii FROM complaints WHERE pm != '' GROUP BY pm ORDER BY numar_reclamatii DESC LIMIT 10

Q: "Top 5 furnizori după valoare reclamații"
A: SELECT furnizor, SUM(valoare) as valoare_totala, COUNT(*) as numar FROM complaints WHERE furnizor != '' GROUP BY furnizor ORDER BY valoare_totala DESC LIMIT 5

Q: "Care sunt motivele principale de reclamație?"
A: SELECT motiv_reclamatie, COUNT(*) as numar FROM complaints WHERE motiv_reclamatie != '' GROUP BY motiv_reclamatie ORDER BY numar DESC LIMIT 10

Q: "Care sunt motivele principale de reclamație?"
A: SELECT motiv_reclamatie, COUNT(*) as numar FROM complaints WHERE motiv_reclamatie != '' GROUP BY motiv_reclamatie ORDER BY numar DESC LIMIT 10

Q: "Ce NR RECLAMATIE au avut reclamațiile din Brașov pe 01.02.2022?"
A: SELECT nr_reclamatie FROM complaints WHERE magazin ILIKE '%brasov%' AND data_reclamatie = '2022-02-01'

Q: "Ce probleme a avut produsul JEF001?"
A: SELECT nr_reclamatie, magazin, observatii FROM complaints WHERE articol_cod ILIKE '%JEF001%' OR articol_denumire ILIKE '%JEF001%' LIMIT 15

Q: "Ce numar de reclamatii au avut cele 5 de la brasov"
A: SELECT nr_reclamatie FROM complaints WHERE magazin ILIKE '%brasov%' ORDER BY data_reclamatie DESC LIMIT 5

REGULĂ CRITICĂ: Fiecare interogare TREBUIE să conțină 'FROM complaints'. NU genera niciodată SELECT fără FROM.

DATE EUROPENE: Când utilizatorul scrie date în format DD.MM.YYYY (ex: 01.02.2022), convertește ÎNTOTDEAUNA la format SQL YYYY-MM-DD (ex: '2022-02-01'). 01.02.2022 = 1 Februarie 2022.

CÂND UTILIZATORUL CERE DETALII DESPRE UN PRODUS (probleme, motive, de ce) + "CATE RECLAMATII":
- EXTREM DE IMPORTANT: NU folosi COUNT() sau GROUP BY.
- Selectează `nr_reclamatie`, `magazin`, `motiv_reclamatie`, `observatii` (raw data).
- Aplicația va număra rândurile automat.
- Exemplu gresit: SELECT magazin, COUNT(*) ...
- Exemplu CORECT: SELECT nr_reclamatie, magazin, observatii FROM complaints WHERE ...
- NU selecta doar `motiv_reclamatie` (este adesea generic/nedeterminat) - `observatii` e util.

ORDINEA SORTĂRII:
- Folosește 'DESC' pentru ordine descrescătoare. NU scrie 'descriere' în ORDER BY decât dacă te referi explicit la coloana 'descriere'.
- Corect: ORDER BY numar_reclamatii DESC
- Greșit: ORDER BY numar_reclamatii descriere
"""


def get_response_system_prompt() -> str:
    """System prompt for response formatting with smart visualization selection."""
    return """Ești un asistent executiv pentru analiza reclamațiilor Mobexpert. 
Formatează rezultatele SQL într-un răspuns natural, structurat și profesionist în română.

REGULI DE FORMATARE:
1. Folosește structură clară cu:
   - **Titluri bold** pentru secțiuni importante
   - • Puncte bullet pentru liste
   - Numere formatate cu separator de mii (ex: 1.234)
   - Pentru valori monetare mari, folosește format "X.XXX.XXX RON"

2. STRUCTURĂ RĂSPUNS:
   - Începe cu un rezumat concis (1-2 propoziții) cu totalul evidențiat bold
   - Dacă sunt mai multe date, organizează-le în secțiuni
   - La final, adaugă un insight sau observație utilă

3. REGULI PENTRU VIZUALIZARE (FOARTE IMPORTANT):
   - Dacă datele conțin evoluție în timp (luni, ani) → "line_chart"
   - Dacă datele conțin categorii cu valori (top N, clasament) → "bar_chart"
   - Dacă datele conțin distribuție/proporții (sub 8 categorii) → "pie_chart"
   - Dacă datele conțin un singur număr → "none" (doar text)
   - Dacă datele sunt detalii specifice (o reclamație, un client) → "none"
   - Dacă datele conțin IDENTIFICATORI (nr_reclamatie, ID-uri) sau TEXT LIBER (observatii, descrieri) → "none"
     și INCLUDE valorile în textul răspunsului ca listă cu bullet points (OBLIGATORIU TOATE DACĂ SUNT < 60)
   - NICIODATĂ nu folosi "bar_chart" pentru date de tip identificator (nr_reclamatie, observatii)
   - NICIODATĂ nu folosi "table" pentru liste de detalii (folosește text)

4. REGULI PENTRU LISTE DE IDENTIFICATORI / DETALII:
   - Când utilizatorul cere NR RECLAMAȚIE, observații, sau alte detalii specifice:
     → visualization = "none"
     → Include TOATE valorile în textul răspunsului ca listă bullet
   - Exemplu pentru NR RECLAMATIE:
     "Cele **5 reclamații** din data de 01.02.2022 au următoarele numere:
     • 97246
     • 97247
     • 97249
     • 97251
     • 97252"
   - Exemplu pentru observații:
     "**Observațiile** pentru cele 5 reclamații:
     • 97246 - Observația text aici
     • 97247 - Observația text aici"

5. EXEMPLE DE FORMATARE:
   Pentru numere simple:
   "În anul 2024, au fost înregistrate **8.187 reclamații** în sistemul Mobexpert."
   
   Pentru liste:
   "**Top 5 Furnizori după valoare:**
   • LINEA MEX SRL - 119.417.641 RON (50.343 reclamații)
   • MURES MEX SA - 23.618.807 RON (6.496 reclamații)
   
   📊 **Insight:** Furnizorul principal generează peste 50% din valoarea totală."

6. NU include NICIODATĂ în răspuns:
   - Checklisturi de tip "* RON added? Yes"
   - Mesaje interne sau de debug
   - Comentarii despre format JSON
   - Text în engleză (răspunde doar în română)

7. NU inventa date - folosește DOAR ce primești din rezultate

FORMAT JSON RĂSPUNS:
{
    "text": "Răspunsul structurat în limba română",
    "visualization": "none" | "table" | "bar_chart" | "line_chart" | "pie_chart",
    "chart_config": { "x": "coloana_x", "y": "coloana_y", "title": "Titlu" }
}

IMPORTANT: Returnează DOAR obiectul JSON valid, fără text suplimentar."""


def generate_sql(question: str) -> tuple[str, str | None]:
    """
    Convert natural language question to SQL.
    Returns: (sql_query, error_message)
    """
    # Known valid column names for auto-correction
    VALID_COLUMNS = {
        'nr_reclamatie', 'raion', 'pm', 'observatii', 'nume_client',
        'nr_comanda', 'id_comanda', 'grup_vanzare', 'furnizor',
        'echipa_livrare', 'data_factura', 'data_comanda', 'data_reclamatie',
        'magazin', 'articol_cod', 'id_client', 'articol_denumire',
        'modalitate_rezolvare', 'motiv_reclamatie', 'descriere',
        'mod_livrare', 'furnizor_ext', 'responsabil_comanda',
        'cantitate', 'valoare'
    }
    
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=question,
            config=types.GenerateContentConfig(
                system_instruction=get_sql_system_prompt(),
                temperature=0.1,  # Low temperature for accuracy
                max_output_tokens=1000,
            )
        )
        
        sql = response.text.strip()
        
        # Clean up SQL (remove markdown code blocks if present)
        sql = re.sub(r'^```sql\s*', '', sql)
        sql = re.sub(r'^```\s*', '', sql)
        sql = re.sub(r'\s*```$', '', sql)
        sql = sql.strip()
        
        # Basic validation
        if not sql.upper().startswith(('SELECT', 'WITH')):
            return "", f"Invalid SQL generated: {sql[:100]}"
        
        # Auto-correct truncated or wrong column names
        def fix_column_name(match):
            word = match.group(0)
            if word.lower() in VALID_COLUMNS:
                return word  # Already valid
            # Try prefix matching for truncated names
            for valid in VALID_COLUMNS:
                if valid.startswith(word.lower()) and len(word) >= 4:
                    return valid
            # Try fuzzy matching for close names
            name_map = {
                'grupa_mediu_vanzare': 'grup_vanzare',
                'grupa_mediu': 'grup_vanzare',
                'mediu_vanzare': 'grup_vanzare',
                'grup_mediu': 'grup_vanzare',
                'data_reclam': 'data_reclamatie',
                'data_rec': 'data_reclamatie',
                'nr_reclam': 'nr_reclamatie',
                'motiv_reclam': 'motiv_reclamatie',
                'articol_den': 'articol_denumire',
                'mod_rezolvare': 'modalitate_rezolvare',
                'responsabil': 'responsabil_comanda',
                'echipa': 'echipa_livrare',
            }
            if word.lower() in name_map:
                return name_map[word.lower()]
            return word
        
        # Fix column names in SQL (match word-like patterns that look like column names)
        sql = re.sub(r'\b[a-z][a-z_]+[a-z]\b', fix_column_name, sql, flags=re.IGNORECASE)
        
        # CRITICAL FIX: Replace 'descriere' with 'DESC' in ORDER BY clauses if used as a keyword
        # Matches "ORDER BY ... descriere" or "ORDER BY ... descriere LIMIT"
        sql = re.sub(r'(ORDER\s+BY\s+[\w\(\)]+\s+)descriere(\s+LIMIT|\s*$)', r'\1DESC\2', sql, flags=re.IGNORECASE)
        
        # CRITICAL: Check for missing FROM clause and auto-fix
        sql_upper = sql.upper()
        if 'FROM' not in sql_upper and sql_upper.startswith('SELECT'):
            # Inject FROM complaints before WHERE/GROUP BY/ORDER BY/LIMIT or at end
            for keyword in ['WHERE', 'GROUP BY', 'ORDER BY', 'LIMIT']:
                if keyword in sql_upper:
                    idx = sql_upper.index(keyword)
                    sql = sql[:idx] + 'FROM complaints ' + sql[idx:]
                    break
            else:
                sql = sql.rstrip(';') + ' FROM complaints'
            sql_upper = sql.upper()
        
        # Safety: inject LIMIT if missing and query doesn't have aggregation
        has_aggregation = any(fn in sql_upper for fn in ['COUNT(', 'SUM(', 'AVG(', 'MIN(', 'MAX(', 'GROUP BY'])
        # FORCE MINIMUM LIMIT 150
        has_limit = 'LIMIT' in sql_upper
        limit_match = re.search(r'LIMIT\s+(\d+)', sql, re.IGNORECASE)
        if limit_match:
            current_limit = int(limit_match.group(1))
            if current_limit < 150:
                 sql = re.sub(r'LIMIT\s+\d+', 'LIMIT 150', sql, flags=re.IGNORECASE)
        
        if not has_aggregation and not has_limit:
            sql = sql.rstrip(';') + ' LIMIT 150'
        
        return sql, None
        
    except Exception as e:
        return "", f"Error generating SQL: {str(e)}"


def generate_chart_query(question: str, original_sql: str, row_count: int) -> str | None:
    """
    If the original query returned too many raw rows (>20),
    generate a smarter aggregation query for chart display.
    Returns: aggregation SQL or None
    """
    try:
        prompt = f"""Interogarea originală a returnat {row_count} rânduri brute, ceea ce este prea mult pentru afișare.

Interogarea originală SQL: {original_sql}
Întrebarea utilizatorului: {question}

Generează o interogare SQL de SUMARIZARE care:
1. Păstrează filtrul WHERE din interogarea originală
2. Agregă datele prin GROUP BY pe cea mai relevantă dimensiune:
   - Dacă e filtrare pe AN → GROUP BY pe LUNI (MONTHNAME)
   - Dacă e filtrare pe LUNĂ → GROUP BY pe ZILE
   - Dacă nu e filtrare temporală → GROUP BY pe raion sau motiv_reclamatie
3. Folosește COUNT(*) ca metrică principală
4. ORDER BY logic (cronologic pentru timp, DESC pentru categorii)
5. LIMIT 12

Returnează DOAR SQL-ul, fără explicații."""

        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=get_sql_system_prompt(),
                temperature=0.1,
                max_output_tokens=300,
            )
        )
        
        agg_sql = response.text.strip()
        agg_sql = re.sub(r'^```sql\s*', '', agg_sql)
        agg_sql = re.sub(r'^```\s*', '', agg_sql)
        agg_sql = re.sub(r'\s*```$', '', agg_sql)
        agg_sql = agg_sql.strip()
        
        if agg_sql.upper().startswith(('SELECT', 'WITH')):
            return agg_sql
        return None
        
    except Exception:
        return None


def format_response(question: str, sql: str, results: list[dict], columns: list[str],
                    total_count: int | None = None) -> dict:
    """
    Format query results into a natural language response.
    Returns: {text, visualization, data, chart_config}
    """
    try:
        # Prepare context for LLM - INCREASED CONTEXT TO 100 ROWS
        result_summary = json.dumps(results[:100], default=str, ensure_ascii=False)
        
        count_info = ""
        if total_count and total_count != len(results):
            count_info = f"\nNOTĂ: Totalul real de rânduri din baza de date pentru acest filtru este {total_count}."
        
        # Calculate distribution for context if 'magazin' column exists
        stats_text = ""
        mag_col = next((c for c in columns if 'magazin' in c.lower()), None)
        if mag_col and len(results) > 1:
            from collections import Counter
            counts = Counter(str(r[mag_col]) for r in results if r.get(mag_col))
            top_counts = counts.most_common()
            stats_list = "\n".join(f"- {k}: {v}" for k, v in top_counts)
            stats_text = f"\n\nSTATISTICI PRE-CALCULATE (FOLOSEȘTE-LE PE ACESTEA, NU NUMĂRA TU):\nDistribuție magazine:\n{stats_list}\n"
        
        prompt = f"""Întrebarea utilizatorului: {question}

SQL executat: {sql}

Rezultate ({len(results)} rânduri):
{result_summary}
{count_info}
{stats_text}
Coloane: {columns}

Generează răspunsul în formatul JSON specificat.
IMPORTANT: 
- Dacă ai primit date agregate (cu GROUP BY), alege vizualizare "bar_chart" sau "line_chart", NU "table"
- Dacă datele conțin luni/perioade, folosește "bar_chart" (x=luna/perioada, y=count/valoare)
- Dacă e un singur număr, folosește "none"
- Specifică chart_config cu "x" și "y" pentru coloanele corecte
- Menționează totalul în text dacă este disponibil

REGULĂ CRITICĂ PENTRU DETALII PRODUSE (ex: JEF001):
1. Începe cu un REZUMAT clar:
   "Au fost înregistrate **X reclamații** pentru produsul [nume/cod].
   Dintre acestea:
   • **Y** în magazinul [Magazin 1]
   • **Z** în magazinul [Magazin 2]"

2. Listează MOTIVELE SPECIFICE extrase din coloana `observatii`:
   "**Motivele detaliate:**"
   • Pentru fiecare rând, extrage partea relevantă din `observatii` (ignoră formule de politețe gen "Buna ziua", "va rog").
   • Dacă motivul este scurt (1-2 cuvinte gen "CULOARE DESCHISA") sau neclar, scrie-l și adaugă "(detalii incomplete)" în paranteză.
   • Format OBLIGATORIU: FIECARE bullet point PE RÂND NOU.
   • Exemplu:
     "**Nr. 49108** (Brașov) - pazie defecta
      **Nr. 49109** (Militari) - lovit la colt / Culoare deschisa (detalii incomplete)"
   
3. Visualization = "none" (pentru că este o listă detaliată de text)

REGULĂ CRITICĂ PENTRU LISTE DE VALORI (nr_reclamatie, observații, etc.):
- Dacă datele conțin identificatori sau text (NU numere agregate), visualization = "none"
- TREBUIE să incluzi TOATE valorile din rezultat în textul răspunsului ca listă bullet.
- NU REZUMA! Dacă sunt 29 de rânduri, scrie 29 de bullet points.
- FIECARE element pe rând nou (folosește \n)
- NU trunchia răspunsul, listează datele relevante
DOAR JSON valid, nimic altceva."""

        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=get_response_system_prompt(),
                temperature=0.3,
                max_output_tokens=4000,
            )
        )
        
        # Parse JSON response
        response_text = response.text.strip()
        
        # Clean up JSON (remove markdown code blocks if present)
        response_text = re.sub(r'^```json\s*', '', response_text, flags=re.MULTILINE)
        response_text = re.sub(r'^```\s*', '', response_text, flags=re.MULTILINE)
        response_text = re.sub(r'\s*```$', '', response_text)
        response_text = response_text.strip()
        
        parsed = None
        
        # Try to parse as JSON
        try:
            parsed = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to find JSON object in the response
            json_match = re.search(r'\{[^{}]*"text"\s*:\s*"[^"]*"[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            # If still not parsed, try to extract just the text field
            if not parsed:
                text_match = re.search(r'"text"\s*:\s*"([^"]*)"', response_text)
                if text_match:
                    parsed = {
                        "text": text_match.group(1),
                        "visualization": _guess_visualization(results, columns)
                    }
                else:
                    # Last resort
                    clean_text = re.sub(r'^\s*\{\s*"text"\s*:\s*"?', '', response_text)
                    clean_text = re.sub(r'"?\s*,?\s*"visualization".*$', '', clean_text, flags=re.DOTALL)
                    clean_text = clean_text.strip().strip('"').strip()
                    if clean_text:
                        parsed = {
                            "text": clean_text,
                            "visualization": _guess_visualization(results, columns)
                        }
                    else:
                        parsed = {
                            "text": f"Am găsit {len(results)} rezultate.",
                            "visualization": _guess_visualization(results, columns)
                        }
        
        # Ensure text field exists and is clean
        if "text" in parsed:
            parsed["text"] = parsed["text"].replace('\\"', '"')
        
        # Override visualization if LLM chose wrong
        if parsed.get("visualization") == "table" and len(results) > 15:
            parsed["visualization"] = _guess_visualization(results, columns)
        
        # Force correct visualization for identifier/detail data
        detail_cols = {'nr_reclamatie', 'observatii', 'observatie', 'detalii', 'descriere',
                       'adresa', 'telefon', 'email', 'client', 'nume_client', 'id', 'nr', 'numar', 'cod'}
        cols_lower = {col.lower() for col in columns}
        is_detail = bool(cols_lower.intersection(detail_cols))
        
        if is_detail and parsed.get("visualization") not in ("none", "table"):
            parsed["visualization"] = "none"
        
        # If visualization is "none" for detail data, ensure values are in text
        if is_detail and parsed.get("visualization") == "none" and len(results) <= 60:
            # Check if values are actually in the text
            text = parsed.get("text", "")
            values = [str(list(r.values())[0]) for r in results if r]
            missing = [v for v in values if v not in text]
            
            # If ANY value is missing from text, force full list injection
            if len(missing) > 0:
                # Find observatii/magazin columns safely
                keys = list(results[0].keys())
                obs_key = next((k for k in keys if 'observ' in k.lower()), None)
                mag_key = next((k for k in keys if 'magazin' in k.lower()), None)
                
                lines = []
                for r in results:
                    val = str(list(r.values())[0])
                    line = f"• {val}"
                    if mag_key and r.get(mag_key):
                        line += f" ({r[mag_key]})"
                    if obs_key and r.get(obs_key):
                        # Clean up text
                        obs_text = str(r[obs_key]).replace('\n', ' ').strip()
                        if len(obs_text) > 150:
                            obs_text = obs_text[:147] + "..."
                        if not obs_text:
                            obs_text = "(detalii incomplete)"
                        line += f" - {obs_text}"
                    lines.append(line)
                
                value_list = "\n".join(lines)
                # Append Clean List
                parsed["text"] += f"\n\n**Lista detaliată ({len(results)} înregistrări):**\n{value_list}"
            # Clear data so frontend doesn't try to render a chart
            parsed["data"] = []
            parsed["columns"] = []
        
        # Add data to response
        if "data" not in parsed:
            parsed["data"] = results
        if "columns" not in parsed:
            parsed["columns"] = columns
        parsed["sql"] = sql
        parsed["row_count"] = len(results)
        
        return parsed
        
    except Exception as e:
        return {
            "text": f"Eroare la formatarea răspunsului: {str(e)}",
            "visualization": "none",
            "data": results,
            "columns": columns,
            "sql": sql,
            "row_count": len(results)
        }


def _guess_visualization(results: list[dict], columns: list[str]) -> str:
    """Guess the best visualization type based on data shape."""
    if not results or len(results) == 0:
        return "none"
    if len(results) == 1 and len(columns) <= 2:
        return "none"  # Single value, just show text
    
    # Detect identifier / detail columns → never chart these
    detail_cols = {'nr_reclamatie', 'observatii', 'observatie', 'detalii', 'descriere',
                   'adresa', 'telefon', 'email', 'client', 'nume_client',
                   'id', 'nr', 'numar', 'cod'}
    cols_lower = {col.lower() for col in columns}
    
    # CRITICAL: If we have 'observatii', it's a detail query -> text list only
    if 'observatii' in cols_lower or 'observatie' in cols_lower:
        return "none"
    
    # If ALL columns are identifiers or detail text → no chart, just text
    if cols_lower.issubset(detail_cols | {'data_reclamatie', 'data', 'magazin'}):
        return "none"
    
    # If the only non-date column is an identifier → no chart
    non_date_cols = cols_lower - {'data_reclamatie', 'data'}
    if non_date_cols and non_date_cols.issubset(detail_cols):
        return "none"
    
    # If single column and it's identifiers → no chart
    if len(columns) == 1 and cols_lower.intersection(detail_cols):
        return "none"
    
    # Check for time-based columns
    time_cols = {'luna', 'month', 'an', 'year', 'data', 'zi', 'saptamana', 'trimestru'}
    has_time = any(col.lower() in time_cols for col in columns)
    
    # Check if we have numeric aggregation columns
    numeric_cols = {'numar', 'numar_reclamatii', 'total', 'count', 'valoare',
                    'valoare_totala', 'suma', 'medie', 'procent'}
    has_numeric = any(col.lower() in numeric_cols for col in columns)
    
    # Need at least one numeric column for charts to make sense
    if not has_numeric:
        # Check if second column is actually numeric in the data
        if len(columns) >= 2:
            second_col = columns[1]
            sample_val = results[0].get(second_col)
            if not isinstance(sample_val, (int, float)):
                return "table" if len(results) <= 15 else "none"
    
    if has_time and len(results) > 2:
        return "bar_chart"
    
    if len(results) <= 8 and len(columns) == 2:
        return "pie_chart" if len(results) <= 6 else "bar_chart"
    
    if len(results) <= 15:
        return "bar_chart"
    
    return "bar_chart"


def chat(question: str) -> dict:
    """
    Main chat function - process question and return formatted response.
    Smart logic: if query returns too many raw rows, auto-aggregate for chart.
    """
    # Step 1: Generate SQL
    sql, sql_error = generate_sql(question)
    if sql_error:
        return {
            "text": f"Nu am putut genera interogarea SQL: {sql_error}",
            "visualization": "none",
            "error": True
        }
    
    # Step 2: Execute SQL
    results, columns, exec_error = execute_query(sql)
    if exec_error:
        return {
            "text": f"Eroare la executarea interogării: {exec_error}",
            "visualization": "none",
            "sql": sql,
            "error": True
        }
    
    # Step 3: No results
    if not results:
        return {
            "text": "Nu am găsit rezultate pentru această interogare.",
            "visualization": "none",
            "sql": sql,
            "data": [],
            "columns": columns,
            "row_count": 0
        }
    
    # Step 4: SMART REDIRECT - If too many raw rows, auto-aggregate
    total_count = len(results)
    if total_count >= 150:
        # Get the real total count
        count_sql = _extract_count_query(sql)
        if count_sql:
            count_results, _, _ = execute_query(count_sql)
            if count_results and len(count_results) == 1:
                first_val = list(count_results[0].values())[0]
                if isinstance(first_val, (int, float)):
                    total_count = int(first_val)
        
        # Generate a smarter aggregation query
        agg_sql = generate_chart_query(question, sql, total_count)
        if agg_sql:
            agg_results, agg_columns, agg_error = execute_query(agg_sql)
            if not agg_error and agg_results:
                # Use aggregated data instead of raw dump
                return format_response(
                    question, agg_sql, agg_results, agg_columns,
                    total_count=total_count
                )
    
    # Step 5: Format response with original data
    return format_response(question, sql, results, columns, total_count=total_count)


def _extract_count_query(sql: str) -> str | None:
    """Extract a COUNT(*) version of the given SQL query."""
    try:
        # Replace SELECT ... FROM with SELECT COUNT(*) FROM
        count_sql = re.sub(
            r'SELECT\s+.*?\s+FROM',
            'SELECT COUNT(*) as total FROM',
            sql,
            count=1,
            flags=re.IGNORECASE | re.DOTALL
        )
        # Remove ORDER BY, LIMIT, GROUP BY
        count_sql = re.sub(r'\s+ORDER\s+BY\s+.*$', '', count_sql, flags=re.IGNORECASE)
        count_sql = re.sub(r'\s+LIMIT\s+\d+', '', count_sql, flags=re.IGNORECASE)
        count_sql = re.sub(r'\s+GROUP\s+BY\s+.*?(?=\s+HAVING|\s+ORDER|\s+LIMIT|$)', '', count_sql, flags=re.IGNORECASE)
        
        if count_sql.upper().startswith('SELECT'):
            return count_sql
        return None
    except Exception:
        return None


# Test function
if __name__ == "__main__":
    from database import init_database
    
    init_database()
    
    test_questions = [
        "Câte reclamații sunt în total?",
        "Reclamații în 2024",
        "Care sunt top 5 categorii cu cele mai multe reclamații?",
        "Care este valoarea totală a reclamațiilor?",
    ]
    
    for q in test_questions:
        print(f"\n❓ {q}")
        result = chat(q)
        print(f"💬 {result.get('text', 'No response')}")
        print(f"📊 Viz: {result.get('visualization')}")
        print(f"📈 Rows: {result.get('row_count')}")
        if result.get('sql'):
            print(f"📝 SQL: {result['sql']}")

# Plan: Robust Chat Logic (Smart Intent Detection)

## Context
User requests a nuanced approach to filtering:
1.  **Avoid Over-Blocking**: Do not aggressively filter valid questions (e.g., vague keywords) as "irrelevant".
2.  **Target Extreme Cases**: Only block obvious nonsense (e.g., "fastest car") or multi-part questions (e.g., "top 10 complaints AND top 10 expensive items").
3.  **Handle Failures Gracefully**: If a complex query slips through and causes a SQL error, catch it and suggest simplification.

## Goal
Implement "Smart Intent Detection" within the LLM prompt to identify `MULTI_PART` and `IRRELEVANT` queries *contextually*, while allowing all other queries to attempt SQL generation.

## Phase 1: Smart Prompt Engineering (The "Soft Filter")
**Modify `backend/sql_agent.py` System Instruction:**

- [ ] **Define Response Modes**:
    1.  **Standard SQL**: Generate SQL for valid queries.
    2.  **Multi-Part Flag**: If user asks two distinct questions (e.g., "Show X... AND show Y..."), DO NOT generate SQL. instead return `MULTI_PART`.
    3.  **Irrelevant Flag**: If user asks about completely unrelated topics (World Knowledge, Sports, Coding), return `IRRELEVANT`.
    
- [ ] **Handling the Flags in Python**:
    - If LLM returns `MULTI_PART` -> Return specific message: *"Te rog să îmi adresezi câte o singură întrebare pe rând. (Ex: 'Top 10...' și apoi 'Cele mai scumpe...')".*
    - If LLM returns `IRRELEVANT` -> Return specific message: *"Nu am informații despre acest subiect. Răspund doar la întrebări legate de reclamațiile Mobexpert."*

*Rationale: This relies on the LLM's understanding of "distinct questions" vs "complex single question", which is smarter than keywords.*

## Phase 2: Safety Net (Exception Handling)
**Handle valid-but-too-complex queries that the LLM tried (and failed) to answer.**

- [ ] **Modify `chat()` in `backend/sql_agent.py`**:
    - Wrap `duckdb.sql().df()` in `try...except`.
    - Catch `duckdb.ParserException` & `duckdb.BinderException`.
    - **User Message**: *"Am întâmpinat o eroare tehnică (interogare prea complexă). Te rog să reformulezi sau să simplifici întrebarea."*
    - Log the error for review.

## Phase 3: Verification
- [ ] **Test Multi-Part**: "Top 10 reclamații și top 10 produse scumpe" -> Should return "Te rog să adresezi câte o singură întrebare".
- [ ] **Test Irrelevant**: "Care e cea mai rapidă mașină?" -> Should return "Nu am informații...".
- [ ] **Test Edge Case (Valid but Weird)**: "Care e produsul cu nume de floare?" -> Should ATTEMPT SQL (might fail or empty result, but not blocked).
- [ ] **Test Complex Valid**: "Reclamații din Brașov în 2024 cu status deschis" -> Should generate valid SQL.

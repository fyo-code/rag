---
name: pandas
description: Pandas and data science patterns for data analysis, transformation, and visualization. Covers DataFrame operations, performance optimization, and integration with DuckDB.
---

# Pandas & Data Science Patterns

## Core DataFrame Operations

### Loading Data
```python
import pandas as pd
import duckdb

# From CSV
df = pd.read_csv("data.csv", dtype={"id": int})

# From DuckDB
con = duckdb.connect("database.duckdb")
df = con.execute("SELECT * FROM users").fetchdf()

# With chunking for large files
for chunk in pd.read_csv("large.csv", chunksize=10000):
    process(chunk)
```

### Data Cleaning
```python
# Handle missing values
df = df.dropna(subset=["important_column"])
df["col"] = df["col"].fillna(0)

# Type conversion
df["date"] = pd.to_datetime(df["date"])
df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

# Remove duplicates
df = df.drop_duplicates(subset=["id"], keep="last")
```

### Transformations
```python
# Apply functions
df["normalized"] = df["value"].apply(lambda x: x / x.max())

# Group operations
summary = df.groupby("category").agg({
    "amount": ["sum", "mean", "count"],
    "date": "max"
}).reset_index()

# Pivot tables
pivoted = df.pivot_table(
    values="amount",
    index="category",
    columns="month",
    aggfunc="sum",
    fill_value=0
)
```

---

## DuckDB Integration

### Why DuckDB?
- Fast analytical queries on local data
- Can query Pandas DataFrames directly
- Efficient for 70k+ row datasets
- SQL interface for complex queries

```python
import duckdb

# Query DataFrame with SQL
result = duckdb.query("""
    SELECT 
        category,
        SUM(amount) as total,
        COUNT(*) as count
    FROM df
    WHERE date >= '2024-01-01'
    GROUP BY category
    ORDER BY total DESC
""").fetchdf()

# Persistent database
con = duckdb.connect("analytics.duckdb")

# Create table from DataFrame
con.execute("CREATE TABLE IF NOT EXISTS sales AS SELECT * FROM df")

# Query with parameters
params = {"min_amount": 100}
result = con.execute(
    "SELECT * FROM sales WHERE amount >= $min_amount",
    params
).fetchdf()
```

---

## Performance Optimization

### Memory Efficiency
```python
# Downcast numeric types
df["int_col"] = pd.to_numeric(df["int_col"], downcast="integer")
df["float_col"] = pd.to_numeric(df["float_col"], downcast="float")

# Use categories for repeated strings
df["category"] = df["category"].astype("category")

# Check memory usage
print(df.memory_usage(deep=True))
```

### Vectorized Operations
```python
# ✅ DO: Use vectorized operations
df["result"] = df["a"] + df["b"] * df["c"]

# ❌ DON'T: Use loops
for i in range(len(df)):
    df.loc[i, "result"] = df.loc[i, "a"] + df.loc[i, "b"] * df.loc[i, "c"]

# ✅ DO: Use query for filtering
df.query("amount > 100 and category == 'A'")

# ❌ DON'T: Chain multiple boolean masks
df[(df["amount"] > 100) & (df["category"] == "A")]  # Less readable
```

---

## Analysis Patterns

### Time Series Analysis
```python
# Resample to monthly
monthly = df.set_index("date").resample("M").agg({
    "amount": "sum",
    "count": "count"
})

# Rolling calculations
df["rolling_avg"] = df["value"].rolling(window=7).mean()

# Year-over-year comparison
df["prev_year"] = df.groupby("month")["amount"].shift(12)
df["yoy_growth"] = (df["amount"] - df["prev_year"]) / df["prev_year"]
```

### Statistical Summary
```python
# Comprehensive statistics
stats = df.describe(percentiles=[.25, .5, .75, .95])

# Correlation matrix
corr = df.select_dtypes(include="number").corr()

# Value counts with percentages
counts = df["category"].value_counts(normalize=True)
```

---

## Best Practices

### ✅ DO
- Use vectorized operations instead of loops
- Use appropriate dtypes to save memory
- Use DuckDB for complex SQL queries
- Handle missing values explicitly
- Document data transformations

### ❌ DON'T
- Use `.apply()` when vectorized alternative exists
- Load entire large files into memory
- Modify DataFrames in place without assignment
- Ignore data types when loading
- Chain too many operations without intermediate checks

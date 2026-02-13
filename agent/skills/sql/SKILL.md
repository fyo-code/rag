---
name: sql
description: SQL patterns for database queries, schema design, and optimization. Covers DuckDB, PostgreSQL, and analytical queries for data processing.
---

# SQL Patterns & Best Practices

## DuckDB Specifics

### Why DuckDB for Analytics?
- Columnar storage optimized for analytical queries
- In-process database (no server needed)
- Can query Parquet, CSV, JSON directly
- Postgres-compatible SQL syntax

### Basic Queries
```sql
-- Create table from CSV
CREATE TABLE sales AS 
SELECT * FROM read_csv_auto('sales.csv');

-- Query with aggregations
SELECT 
    category,
    DATE_TRUNC('month', sale_date) as month,
    SUM(amount) as total_revenue,
    COUNT(*) as transaction_count,
    AVG(amount) as avg_order_value
FROM sales
WHERE sale_date >= '2024-01-01'
GROUP BY 1, 2
ORDER BY month, total_revenue DESC;

-- Window functions
SELECT 
    *,
    SUM(amount) OVER (
        PARTITION BY category 
        ORDER BY sale_date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as cumulative_total
FROM sales;
```

---

## Analytical Patterns

### Running Totals & Moving Averages
```sql
SELECT 
    date,
    revenue,
    SUM(revenue) OVER (ORDER BY date) as cumulative_revenue,
    AVG(revenue) OVER (
        ORDER BY date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as moving_avg_7d
FROM daily_sales;
```

### Ranking & Top-N
```sql
-- Top 10 by category
WITH ranked AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY category 
            ORDER BY amount DESC
        ) as rank
    FROM products
)
SELECT * FROM ranked WHERE rank <= 10;

-- Percentiles
SELECT 
    category,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY amount) as median,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY amount) as p95
FROM sales
GROUP BY category;
```

### Time-Based Analysis
```sql
-- Year-over-year comparison
SELECT 
    DATE_TRUNC('month', date) as month,
    SUM(revenue) as current_year,
    LAG(SUM(revenue), 12) OVER (ORDER BY DATE_TRUNC('month', date)) as prev_year,
    ROUND(
        (SUM(revenue) - LAG(SUM(revenue), 12) OVER (ORDER BY DATE_TRUNC('month', date))) 
        / NULLIF(LAG(SUM(revenue), 12) OVER (ORDER BY DATE_TRUNC('month', date)), 0) * 100,
        2
    ) as yoy_growth_pct
FROM sales
GROUP BY 1;

-- Cohort analysis
SELECT 
    first_purchase_month,
    purchase_month,
    DATEDIFF('month', first_purchase_month, purchase_month) as cohort_month,
    COUNT(DISTINCT customer_id) as customers
FROM (
    SELECT 
        customer_id,
        DATE_TRUNC('month', date) as purchase_month,
        MIN(DATE_TRUNC('month', date)) OVER (PARTITION BY customer_id) as first_purchase_month
    FROM orders
) t
GROUP BY 1, 2, 3;
```

---

## Schema Design

### Normalization vs Denormalization
```sql
-- Normalized (good for OLTP)
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name VARCHAR NOT NULL,
    email VARCHAR UNIQUE NOT NULL
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    order_date DATE NOT NULL,
    total DECIMAL(10, 2)
);

-- Denormalized (good for analytics)
CREATE TABLE order_facts AS
SELECT 
    o.id as order_id,
    o.order_date,
    o.total,
    c.name as customer_name,
    c.email as customer_email,
    p.name as product_name,
    p.category
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id;
```

### Indexes for Query Patterns
```sql
-- Index for common filters
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_orders_customer ON orders(customer_id);

-- Composite index for common query pattern
CREATE INDEX idx_orders_date_customer ON orders(order_date, customer_id);
```

---

## Performance Optimization

### Query Optimization
```sql
-- Use EXPLAIN ANALYZE
EXPLAIN ANALYZE
SELECT * FROM orders WHERE customer_id = 123;

-- ✅ DO: Select only needed columns
SELECT id, name, total FROM orders WHERE date > '2024-01-01';

-- ❌ DON'T: Select all columns
SELECT * FROM orders WHERE date > '2024-01-01';

-- ✅ DO: Use proper data types
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    event_date DATE,      -- Not VARCHAR
    amount DECIMAL(10,2)  -- Not FLOAT
);
```

---

## Best Practices

### ✅ DO
- Use CTEs for complex queries (readability)
- Use window functions for analytics
- Create indexes based on query patterns
- Use EXPLAIN before optimizing
- Use appropriate data types

### ❌ DON'T
- Use SELECT * in production
- Create indexes on every column
- Use subqueries when JOINs work
- Ignore NULL handling
- Use FLOAT for money (use DECIMAL)

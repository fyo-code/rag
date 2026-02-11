# Executive UI & Chart Design Plan

## 🎯 Goal
Create a "top-tier" executive dashboard experience by implementing high-fidelity, custom-designed charts and data visualizations. Instead of generic generated charts, we will use specific visual templates inspired by premium UI designs.

## 📋 Strategy
1.  **Template-Driven Design**: The user will provide reference images for specific chart types.
2.  **Custom Implementation**: I will build React/Tremor components that exactly match the style (colors, spacing, fonts, interactions) of these references.
3.  **Data mapping**: I will map the real SQL data to these visual templates.

## 📊 Required Chart Types (Request for References)
Please provide reference photos/screenshots for the following chart types you'd like to see:

### 1. KPI Cards (The "At a Glance" View)
*   **Purpose**: Show High-level metrics (Total Complaints, Resolution Rate, Avg Response Time).
*   **Need**: Style for big numbers, trend indicators (arrow up/down), and mini sparklines if desired.

### 2. Time-Series Trend (The "Story Over Time")
*   **Purpose**: Show complaints evolution over months/weeks.
*   **Need**: Style for line charts (smooth vs sharp curves, gradient fills under the line, point styles).

### 3. Category Breakdown (The "Drivers")
*   **Purpose**: "Top 5 Suppliers" or "Top 5 Products" with most complaints.
*   **Need**: Horizontal Bar Chart style (often looks better for long names) or Vertical Bar Chart.

### 4. Composition (The "Makeup")
*   **Purpose**: Status distribution (Open vs Resolved) or Complaint Type.
*   **Learn**: Donut chart style (thickness, legend placement, center text).

### 5. Detailed Data View
*   **Purpose**: The raw data for deep diving.
*   **Need**: Table design (header styling, row striping, status badges, hover effects).

## 🚀 Execution Plan (After References Received)
1.  [ ] User uploads reference images for selected charts.
2.  [ ] I analyze the design tokens (colors, border-radius, shadows, fonts).
3.  [ ] I update `frontend/src/app/page.tsx` (and component files) to implement these exact designs using Tailwind CSS + Tremor/Recharts.
4.  [ ] I verify the look with screenshots.

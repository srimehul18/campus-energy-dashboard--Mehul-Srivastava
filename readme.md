# Campus Energy Dashboard – K.R. Mangalam University

This project analyzes hourly smart meter electricity consumption data for multiple buildings on the K.R. Mangalam University campus. The goal is to study daily and weekly energy usage patterns and build a visual dashboard to support energy-saving decisions.

---

##  Objectives

- Load and validate multiple CSV smart-meter data files
- Aggregate energy usage into daily and weekly trends
- Create building-wise consumption summaries
- Visualize key insights in a single dashboard figure
- Practice Object-Oriented Programming (OOP) design for data handling
- Automatically generate summary reports and cleaned data files

---

##  Project Structure
capstone/

│

├── data/

│ ├── engg_block.csv

│ ├── library.csv

│ ├── admin_block.csv

│ └── hostel.csv

│
├── output/

│ ├── cleaned_energy_data.csv

│ ├── building_summary.csv

│ ├── dashboard.png

│ ├── summary.txt

│ └── energy_dashboard.log

│
├── energy_dashboard.py

└── README.md


---

## Methods & Concepts Used

| Task | Method |
|------|--------|
| Data ingestion | Pandas, validation, merge |
| Daily & weekly aggregation | `resample()`, `groupby()` |
| Visualization | Matplotlib line, bar & scatter plots |
| OOP design | Building, MeterReading & Manager classes |
| Summary reporting | File output + logs |

---

##  Outputs Generated

1. **Dashboard Figure** (`dashboard.png`)  
   - Daily consumption trend (all buildings)
   - Weekly average comparison
   - Peak hour usage (scatter)

2. **Cleaned and Combined Data** (`cleaned_energy_data.csv`)

3. **Building-wise Summary** (`building_summary.csv`)

4. **Campus-wide Summary** (`summary.txt`)

---

##  How to Run

Install dependencies:

```bash
pip install pandas numpy matplotlib
```

Then run script:

**python energy_dashboard.py**

All results will appear automatically in output/ folder.

---
## Developed By:
Mehul Srivastava

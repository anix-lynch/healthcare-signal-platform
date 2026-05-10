# Healthcare Data Analytics Platform

**Data Analytics Engineer portfolio project:** End-to-end analytics solution for hospital operations.

**Demo:** 55,500 synthetic patient records | REST API → dbt warehouse → Power BI semantic model → ML workflow

**Interview claim source of truth:** `sla` (locked bullets + claim-to-code traceability)

Single source of truth: [SPEC.md](SPEC.md).

For agents: progress in SPEC; backup map below if any.

**Repos:** Warehouse = GitLab (review here first). Showroom = GitHub (push only when shipable/presentable for headhunters).

## Scaffold backup

Originals: `_scaffold_backup_20260311/`. Schema/mapping now in SPEC or outputs/02_schema/, outputs/02_mapping/.

---

## 📊 Why This Matters for DA Role

This project demonstrates **clinical domain knowledge** + **modern data stack** — exactly what healthcare orgs in LA (Cedars-Sinai, UCLA Health, USC Keck, Kaiser Permanente) look for but rarely find:

✅ **Healthcare-shaped synthetic data** (clearly labeled)  
✅ **Hospital operations focus** (readmission reduction = reimbursement value)  
✅ **dbt + SQL warehouse** (industry standard for AE/DA)  
✅ **Power BI / TMDL semantic modeling** (clinical KPIs)  
✅ **ML integration** (predictive analytics for interventions)  
✅ **All runnable via CLI** (no GUI bloat)

---

## 🏗️ Architecture: Four-Layer Analytics Stack

```
Layer 0: Data Source
  └─ REST API → 55K patient records (FastAPI)

Layer 1: Data Lake → Warehouse  
  └─ dbt SQL transforms into star schema (dbt + Fabric SQL)

Layer 2: Semantic Model
  └─ Power BI TMDL + DAX clinical KPIs (billable hours, readmission %)

Layer 3: Insights & Predictions
  └─ XGBoost readmission risk model + MLflow experiment tracking
```

**Business framing:** simulated/projected scenarios only. No real-world savings claimed.

**Why are some input/output files empty?** The folders are the map: **inputs** = what goes in, **outputs** = what comes out (see each folder’s `*_context.md`). The actual JSON/MD files get filled when you run the pipeline. Gate: **data/raw/healthcare_dataset.csv** must exist (55K rows; see api/README for schema or sample). Then run `./scripts/populate_proof_artifacts.sh` to capture API stats, encounter snapshot, and (if dbt/ML run) proof into the output folders.

---

## 🚀 Quick Start (CLI Only)

### 1. REST API (55K patient records)

```bash
./scripts/start_api.sh
# → http://localhost:8000/docs
```

Try:
```bash
curl http://localhost:8000/api/stats  # overall volume
curl http://localhost:8000/api/encounters?condition=Diabetes&limit=10
```

See [api/README.md](api/README.md) for full docs.

### 2. Data Warehouse (dbt + Fabric SQL)

```bash
cd dbt-project

# Check Fabric auth
../scripts/fabric_doctor.sh

# Run dbt transforms
dbt run --profiles-dir . --select readmission_risk

# Test data quality
dbt test --profiles-dir .
```

### 3. ML Model (Readmission Risk)

```bash
cd ml-pipeline/src
source ../../.venv/bin/activate

# Train model on 55.5K patients
python train.py
# ✅ Accuracy: 66%+ | AUC: 0.51

# View experiments
mlflow ui  # → http://localhost:5000
```

### 4. Power BI Semantic Model (TMDL)

```bash
# Deploy to Fabric
cd ../powerbi-model
# TMDL files ready: model.tmdl, relationships.tmdl, tables/
```

---

## 📁 Project Structure

```
healthcare-analytics/
├── api/                          # FastAPI serving 55K records
│   ├── app/
│   ├── tests/
│   └── requirements.txt
├── dbt-project/                  # Star schema transforms
│   ├── dbt_project.yml
│   ├── models/                   # Fact tables: encounters, readmissions
│   ├── seeds/                    # Patient, doctor, hospital data
│   ├── tests/                    # dbt test assertions
│   ├── profiles.yml              # Fabric SQL connection
│   └── healthcare_analytics/     # dbt package
├── powerbi-model/                # TMDL semantic model
│   ├── model.tmdl                # Shared dimensions
│   ├── relationships.tmdl        # Star schema joins
│   └── tables/                   # DAX calculations
├── ml-pipeline/
│   ├── src/train.py              # XGBoost readmission model
│   ├── notebooks/                # Exploration + validation
│   └── requirements.txt
├── data/raw/                     # Sample datasets
├── scripts/
│   ├── start_api.sh              # Run API server
│   ├── fabric_doctor.sh          # CLI auth diagnostic
│   └── ...
└── docs/                         # Architecture, setup guides
```

---

## 📊 Dataset

**Source:** Healthcare Dataset (55,500 patient encounters)
- **Time Period:** 2019-2024 (5 years)
- **Patients:** 49,992 unique individuals
- **Providers:** 40,341 doctors across 39,876 hospitals
- **Conditions:** 6 major medical conditions (Diabetes, Hypertension, Cancer, Arthritis, Asthma, Obesity)
- **Location:** `data/raw/healthcare_dataset.csv`

---

## 📂 Project Structure

```
healthcare-analytics/
├── README.md                          # This file
├── data/
│   └── raw/
│       └── healthcare_dataset.csv     # 55,500 patient records (SINGLE SOURCE OF TRUTH)
│
├── api/                               # REST API (FastAPI)
│   ├── app/
│   │   └── main.py                    # API server
│   ├── requirements.txt
│   ├── README.md                      # API documentation
│   └── test_api.py                    # Test script
│
├── docs/
│   ├── KILO_INSTRUCTIONS.md           # Step-by-step build guide
│   ├── PROJECT_SPEC.md                # Original project requirements  
│   └── UNIFIED_ARCHITECTURE.md        # Complete technical specification
│
├── dbt-project/                       # PROJECT 1: Data Warehouse ✅ COMPLETE
│   ├── models/
│   │   ├── staging/                   # Staging layer (stg_healthcare)
│   │   ├── intermediate/              # Intermediate models (enrichments, readmissions)
│   │   └── marts/                     # Star schema (7 dims + 1 fact)
│   ├── tests/                         # 44 data quality tests
│   └── profiles.yml                   # dbt connection config
│
├── powerbi-model/                     # PROJECT 2: Semantic Model ✅ COMPLETE
│   ├── model.tmdl                     # Main model definition
│   ├── relationships.tmdl             # Star schema relationships
│   └── tables/                        # Table definitions with DAX measures
│
├── ml-pipeline/                       # PROJECT 3: ML Prediction ✅ COMPLETE
│   ├── src/
│   │   ├── train.py                   # XGBoost training script
│   │   └── score.py                   # Batch scoring script
│   └── requirements.txt               # ML dependencies
│
├── diagrams/                          # Architecture & ERD diagrams
└── scripts/
    └── start_api.sh                   # Start API server
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- dbt-core with Fabric adapter (for data warehouse)
- Microsoft Fabric workspace (60-day free trial, for BI/ML)
- Azure CLI (for authentication)

### Quick Start

1. **Start the Healthcare API** (Recommended first step!)
```bash
cd healthcare-da
./scripts/start_api.sh

# API runs at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

2. **Test the API**
```bash
# In another terminal
cd api
python test_api.py
```

3. **Review the documentation**
```bash
cat docs/UNIFIED_ARCHITECTURE.md  # Complete technical spec
cat docs/KILO_INSTRUCTIONS.md     # Build instructions
cat api/README.md                 # API documentation
```

4. **Set up Fabric workspace** (for dbt/TMDL/ML projects)
- Go to https://app.fabric.microsoft.com
- Create workspace: "HealthcareAnalytics"
- Run setup script: `./scripts/setup_fabric.sh` (coming soon)

5. **Build the data warehouse** (consumes API data)
```bash
cd dbt-project
dbt run
dbt test
```

---

## 📈 Key Metrics & KPIs

### Clinical Metrics
- **30-Day Readmission Rate:** Target < 15% (CMS Quality Metric)
- **Average Length of Stay (ALOS):** Benchmark 4.5 days
- **Bed Occupancy Rate:** Optimal 85-90%

### Financial Metrics
- **Total Billing:** $1.4B annually
- **Cost per Patient Day:** $1,648 average
- **Revenue per Hospital:** Varies by facility size

### ML Model Performance (current baseline)
- **AUC-ROC:** 0.51 on synthetic data — illustrative pipeline, not a production model
- **Purpose:** demonstrate XGBoost + MLflow lifecycle, not predictive lift
- **Honest framing:** a retrained model on real clinical features would be
  required before any production use; this repo proves the *engineering path*

---

## 💰 Business Framing (Illustrative Only)

Readmission risk reduction is the canonical value lever in this domain. Any
dollar figures in this repo are **illustrative scenario math**, not measured
outcomes. See `sla` for the traceability rule: every resume bullet must point
to a file, not to a projected ROI.

---

## 🛠️ Tech Stack

### API Layer
- **FastAPI:** Modern Python web framework
- **Pandas:** Data processing & manipulation
- **Uvicorn:** ASGI server
- **OpenAPI/Swagger:** Interactive API documentation

### Data Engineering
- **dbt:** Data transformation & testing
- **SQL:** Query language
- **Fabric SQL Warehouse:** Cloud data warehouse
- **Python:** Data processing

### Business Intelligence
- **TMDL:** Power BI semantic model (code-first)
- **DAX:** Business logic & calculations
- **Microsoft Fabric:** Cloud BI platform

### Machine Learning
- **XGBoost:** Gradient boosting classifier
- **MLflow:** Experiment tracking & model registry
- **Scikit-learn:** Feature engineering
- **SHAP:** Model interpretability

### DevOps
- **Git:** Version control
- **GitHub Actions:** CI/CD (planned)
- **Azure CLI:** Authentication & deployment

---

## 📚 Documentation

- **[UNIFIED_ARCHITECTURE.md](docs/UNIFIED_ARCHITECTURE.md)** - Complete technical specification
  - Star schema design
  - dbt transformation pipeline
  - DAX measures
  - ML model architecture
  - Future AI/RAG extensions

- **[PROJECT_SPEC.md](docs/PROJECT_SPEC.md)** - Original project requirements
  - Business context
  - Portfolio objectives
  - Resume bullet points

- **[KILO_INSTRUCTIONS.md](docs/KILO_INSTRUCTIONS.md)** - Step-by-step build guide
  - Phase 1: Data Warehouse
  - Phase 2: Semantic Model
  - Phase 3: ML Pipeline

---

## 🎯 Skills Demonstrated

### Data Engineering
- Dimensional modeling (star schema)
- ETL/ELT pipelines
- Data quality testing
- dbt best practices
- Cloud data warehouse

### Business Intelligence
- Code-first BI development
- Advanced DAX (calculation groups, time intelligence)
- Row-Level Security (HIPAA compliance)
- Semantic modeling

### Machine Learning
- Feature engineering
- Classification models
- Model interpretability (SHAP)
- MLOps (MLflow)
- Production deployment

### Healthcare Domain
- Clinical metrics (readmission rate, ALOS)
- HIPAA compliance
- Value-based care concepts
- Healthcare data standards

---

## 🏥 Target Job Roles

This portfolio is optimized for:

- **Healthcare Data Analyst** ($85K-$110K)
- **Clinical Analytics Specialist** ($90K-$115K)
- **Healthcare BI Developer** ($88K-$112K)
- **Analytics Engineer - Healthcare** ($95K-$120K)
- **Healthcare Data Scientist** ($105K-$130K)

---

## 📊 Current Status

**Phase 0: REST API** ✅ **COMPLETE!**
- [x] FastAPI server built
- [x] 10+ REST endpoints implemented
- [x] Filtering, pagination, search
- [x] OpenAPI documentation
- [x] Test suite created
- [x] Ready for production deployment

**Phase 1: Planning & Design** ✅
- [x] Dataset acquired & analyzed
- [x] Architecture designed
- [x] Documentation complete

**Phase 2: Data Warehouse** ✅ **COMPLETE!**
- [x] dbt project initialized
- [x] Staging models built
- [x] Dimension tables created (7 dimensions)
- [x] Fact table created (fact_patient_encounters)
- [x] Data quality tests added (44 tests)
- [x] Deployed to Microsoft Fabric Warehouse
- [x] All 11 models successfully built

**Phase 3: Semantic Model** ✅ **COMPLETE!**
- [x] TMDL structure created
- [x] DAX measures implemented (Total Revenue, Readmission Rate)
- [x] Star schema relationships defined
- [x] Deployed to Microsoft Fabric
- [x] Connected to warehouse via Direct Lake
- [x] All 5 tables loaded (fact + 4 dimensions)

**Phase 4: ML Pipeline** ✅ **COMPLETE!**
- [x] Features engineered
- [x] Model trained (XGBoost on 55,500 records)
- [x] Model evaluated (66.41% accuracy, AUC-ROC: 0.51)
- [x] MLflow experiment tracking configured
- [x] Model saved to MLflow registry

---

## 🔐 Security & Compliance

### HIPAA Compliance
- Patient names hashed (SHA-256)
- Row-Level Security in BI layer
- Audit logging enabled
- Data encryption at rest & in transit

### Data Governance
- Column-level lineage tracked
- Data quality tests automated
- PII handling documented
- Access controls implemented

---

## 🚀 Roadmap

### Current Projects (Weeks 1-8)
1. ✅ Data Warehouse (dbt + Fabric SQL)
2. ⏳ Semantic Model (TMDL + DAX)
3. ⏳ ML Prediction Engine (XGBoost + MLflow)

### Future Enhancements (Post-MVP)
- **Patient Similarity Search:** Vector embeddings for treatment recommendations
- **Clinical RAG:** LangChain + OpenAI for evidence-based decision support
- **Knowledge Graph:** Neo4j graph database for complex relationships
- **Real-Time Scoring:** Stream processing for live risk assessment
- **Multi-Modal Analytics:** Imaging data + clinical notes integration

---

## 👤 Author

**Anix Lynch**
- Location: Culver City, CA
- Email: alynch@gozeroshot.dev
- LinkedIn: [linkedin.com/in/anixlynch](https://linkedin.com/in/anixlynch)
- GitHub: [github.com/anix-lynch](https://github.com/anix-lynch)

---

## 📄 License

This project is for portfolio demonstration purposes.

Dataset: CC0-1.0 (Public Domain) - Synthetic healthcare data from Kaggle

---

## 🙏 Acknowledgments

- **Kaggle:** Healthcare dataset (prasad22/healthcare-dataset)
- **dbt Labs:** Transformation framework
- **Microsoft:** Fabric platform
- **MLflow:** Experiment tracking

---

**Built entirely via CLI/API - Zero GUI! 🔥**

## Deployment snapshot

All four components are deployed to a Microsoft Fabric workspace:
- Data Warehouse: 11 dbt models (1 table + 10 views)
- Semantic Model: connected via Direct Lake to the warehouse
- ML Pipeline: baseline XGBoost + MLflow experiment (illustrative — see AUC note)
- REST API: FastAPI serving 55,500 records via 11 endpoints

Screenshots of the live Fabric workspace, Lakehouse, FastAPI docs, and Power BI
report live in [`screenshots/`](screenshots/) and are indexed in
[`SCREENSHOTS.md`](SCREENSHOTS.md).

Authentication path for the CLI + API calls is documented in `scripts/fabric_doctor.sh`.


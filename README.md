# 💰 AI-Powered Finance & Receipt Intelligence System

An AI-powered personal finance application that automates **receipt processing, expense categorization, anomaly detection, and financial analytics**.

The system provides an end-to-end pipeline that transforms receipt images into structured financial records using **OpenCV, PaddleOCR, and Qwen2.5-VL**, followed by machine learning-based expense categorization and statistical anomaly detection.

```text
Receipt → OCR → LLM Parsing → ML Categorization → Database → Analytics
```

---

## 🚀 Key Features

- 🧾 AI-powered receipt processing
- 🔍 OCR-based text extraction using PaddleOCR
- 🖼️ Receipt image preprocessing using OpenCV
- 🤖 Structured receipt parsing using Qwen2.5-VL through Ollama
- 🏷️ Automatic expense categorization using machine learning
- 📊 Spending analytics and category breakdowns
- 📈 Monthly spending trend analysis
- 🚨 Statistical anomaly detection
- 🔐 JWT authentication and bcrypt password hashing
- 📝 Receipt and transaction management
- 🎯 Confidence scores for expense predictions
- 🔄 Regex-based fallback extraction when LLM parsing is unavailable

---

# 🧾 Receipt Intelligence Pipeline

The system converts unstructured receipt images into structured financial information.

```text
Receipt Image
      │
      ▼
OpenCV Preprocessing
      │
      │ CLAHE + Resize
      ▼
PaddleOCR
      │
      ▼
Extracted Receipt Text
      │
      ▼
Qwen2.5-VL via Ollama
      │
      ▼
Structured JSON
      │
      ├── Merchant
      ├── Date
      ├── Amount
      ├── Items
      └── Payment Method
      │
      ▼
Expense Categorization
      │
      ▼
Database Storage
      │
      ▼
Analytics & Anomaly Detection
```

---

# 🔍 OCR & Receipt Processing

## OpenCV Preprocessing

Receipt images are preprocessed before OCR using:

- CLAHE contrast enhancement
- Image resizing to 1024 × 768
- Image preprocessing for improved text extraction

## PaddleOCR

**PaddleOCR** extracts text from receipt images and provides the textual input for downstream processing.

## Qwen2.5-VL

**Qwen2.5-VL**, accessed through Ollama, is used to interpret the extracted receipt information and produce structured JSON data.

The pipeline extracts information such as:

- Merchant / store name
- Transaction date
- Total amount
- Individual receipt items
- Payment method when available

If the LLM parser is unavailable, the system falls back to **regex-based extraction**.

---

# 🤖 Expense Categorization

After receipt information is converted into transaction data, the system automatically predicts an expense category using a supervised machine learning pipeline.

## ML Pipeline

```text
Merchant Name + Receipt Items
            │
            ▼
   Text Preprocessing
            │
            ▼
      Lemmatization
            │
            ▼
      TF-IDF Vectorization
            │
            ▼
    Logistic Regression
            │
            ▼
     Expense Category
```

The classification pipeline uses **NLTK WordNet Lemmatization**, followed by **TF-IDF vectorization** and **Logistic Regression** using Scikit-learn.

---

# 📊 Machine Learning Performance

The expense categorization model was trained on **212 samples across 10 expense categories**.

## Overall Performance

| Metric | Score |
|--------|------:|
| **Precision** | **0.854** |
| **Recall** | **0.788** |
| **F1-Score** | **0.794** |

## Expense Categories

```text
Food
Travel
Entertainment
Shopping
Health
Utilities
Education
Housing
Insurance
Other
```

## Category-Level Performance

| Category | Precision | Recall | F1-Score |
|----------|----------:|-------:|---------:|
| Food | 1.000 | 0.704 | 0.826 |
| Travel | 0.909 | 0.800 | 0.851 |
| Entertainment | 0.905 | 0.864 | 0.884 |
| Shopping | 0.515 | 1.000 | 0.680 |
| Health | 0.917 | 0.550 | 0.688 |
| Utilities | 0.875 | 0.875 | 0.875 |
| Education | 0.917 | 0.688 | 0.786 |
| Housing | 1.000 | 0.562 | 0.720 |
| Insurance | 0.900 | 0.818 | 0.857 |
| Other | 0.840 | 0.840 | 0.840 |

---

# ⚡ ML Model Characteristics

- **Training samples:** 212
- **Expense categories:** 10
- **Model:** Logistic Regression
- **Feature extraction:** TF-IDF
- **Text preprocessing:** NLTK WordNet Lemmatizer
- **Prediction latency:** <10 ms per transaction
- **Output:** Predicted category and probability distribution
- **Model persistence:** Saved model and vectorizer

The trained model artifacts are stored as:

```text
backend/models/category_model.pkl
backend/models/vectorizer.pkl
```

---

# 🚨 Anomaly Detection

The application includes a statistical anomaly detection service for identifying unusual spending behavior.

## Detection Methods

### 1. Amount Outliers

Uses Z-score analysis to identify unusually high or low transaction amounts.

### 2. Category-Specific Outliers

Uses category-specific spending baselines based on:

```text
Mean + 2.5 × Standard Deviation
```

This allows spending behavior to be evaluated relative to the user's category patterns.

For example, a high-value transaction may be normal for **Housing** but unusual for **Food**.

### 3. Frequency Patterns

Detects repeated similar transactions occurring within short time periods.

### 4. Duplicate Detection

Identifies potentially duplicated transactions based on matching transaction characteristics within a short timeframe.

---

## 🚨 Anomaly Severity

Detected anomalies are classified into:

- 🔴 High
- 🟠 Medium
- 🟡 Low

Each anomaly includes:

- Anomaly type
- Human-readable reason
- Severity level
- Affected transaction details

---

# 📈 Financial Analytics

The application provides financial insights through analytics APIs and dashboard visualizations.

### Analytics include:

- Spending breakdown by category
- Spending breakdown by payment method
- Monthly spending trends
- Transaction-level analysis
- Anomaly detection
- ML model evaluation
- Optional AI-generated financial insights through Ollama

```text
Financial Transactions
          │
          ▼
   Categorized Expenses
          │
    ┌─────┼─────┐
    │     │     │
    ▼     ▼     ▼
Category Trends Anomalies
    │     │     │
    └─────┼─────┘
          ▼
   Finance Dashboard
```

---

# 🔐 Security

The backend implements authentication, authorization, and input validation for secure financial data handling.

- JWT-based authentication
- bcrypt password hashing
- Protected API endpoints
- Token-based authorization
- User-level data isolation
- Input validation
- Secure filename handling
- Receipt file-type validation
- Protected receipt access
- CORS configuration

---

# 🔌 REST API

The backend provides REST APIs for authentication, receipt processing, receipt management, analytics, ML evaluation, and anomaly detection.

## Receipt Processing & Management

```text
POST   /api/receipts/process
POST   /api/receipts/save
GET    /api/receipts/
GET    /api/receipts/<id>
PUT    /api/receipts/<id>
DELETE /api/receipts/<id>
```

## Analytics

```text
GET /api/analytics/summary
GET /api/analytics/anomalies
GET /api/analytics/model/evaluate
GET /api/analytics/model/metrics
GET /api/analytics/trends
GET /api/analytics/insights
```

## Authentication

```text
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
POST /api/auth/logout
```

---

# 🏗️ System Architecture

```text
┌───────────────────────────────────────────────┐
│                  Frontend                     │
│             HTML • CSS • JavaScript           │
└───────────────────────┬───────────────────────┘
                        │
                        │ HTTP / REST API
                        ▼
┌───────────────────────────────────────────────┐
│               Flask Backend                   │
│                                               │
│ Authentication │ Receipts │ Analytics         │
│ ML Categorization │ Anomaly Detection         │
└───────────────┬───────────────────┬───────────┘
                │                   │
                ▼                   ▼
       ┌────────────────┐   ┌────────────────────┐
       │ SQLite +       │   │ AI / ML Pipeline   │
       │ SQLAlchemy     │   │                    │
       │                │   │ OpenCV             │
       │ Users          │   │ PaddleOCR          │
       │ Receipts       │   │ Qwen2.5-VL         │
       │ ReceiptItems   │   │ TF-IDF             │
       │                │   │ LogisticRegression │
       └────────────────┘   │ Anomaly Detection  │
                            └────────────────────┘
```

---

# 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python, Flask |
| **Database** | SQLite |
| **ORM** | SQLAlchemy |
| **Authentication** | JWT, bcrypt |
| **Image Processing** | OpenCV |
| **OCR** | PaddleOCR |
| **Multimodal AI** | Qwen2.5-VL via Ollama |
| **Machine Learning** | Scikit-learn |
| **NLP** | NLTK, TF-IDF |
| **Classification** | Logistic Regression |
| **Frontend** | HTML, CSS, JavaScript |

---

# 📂 Project Structure

```text
finance-tracker/

├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── models.py
│   │   │
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── receipts.py
│   │   │   └── analytics.py
│   │   │
│   │   ├── services/
│   │   │   ├── ml_model.py
│   │   │   ├── anomaly_detector.py
│   │   │   ├── ocr_engine.py
│   │   │   ├── image_processor.py
│   │   │   ├── llm_parser.py
│   │   │   ├── pipeline.py
│   │   │   └── database.py
│   │   │
│   │   └── utils/
│   │       ├── auth_middleware.py
│   │       └── validators.py
│   │
│   ├── models/
│   │   ├── category_model.pkl
│   │   └── vectorizer.pkl
│   │
│   ├── uploads/
│   ├── run.py
│   ├── train_model.py
│   └── requirements.txt
│
├── frontend/
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── upload.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── api.js
│       ├── auth.js
│       ├── dashboard.js
│       └── upload.js
│
├── README.md
└── requirements.txt
```

---

# 🔄 End-to-End Workflow

```text
User Registration / Login
          │
          ▼
       JWT Token
          │
          ▼
     Upload Receipt
          │
          ▼
  OpenCV Preprocessing
          │
          ▼
       PaddleOCR
          │
          ▼
   Extracted OCR Text
          │
          ▼
      Qwen2.5-VL
          │
          ▼
 Structured Receipt Data
          │
          ▼
TF-IDF + Logistic Regression
          │
          ▼
Expense Category + Confidence
          │
          ▼
    SQLite Database
          │
      ┌───┴────┐
      ▼        ▼
 Analytics   Anomaly Detection
      │        │
      └───┬────┘
          ▼
    Finance Dashboard
```

---

# 🧪 Validation & Testing

The major application components have been tested, including:

- ✅ User registration
- ✅ User login
- ✅ JWT authentication
- ✅ ML model training
- ✅ Category prediction
- ✅ Confidence score generation
- ✅ Model persistence
- ✅ ML evaluation metrics
- ✅ Receipt CRUD operations
- ✅ Protected API access
- ✅ Frontend accessibility
- ✅ Input validation
- ✅ Anomaly detection

---

# ⚠️ Known Limitations

### PaddleOCR Compatibility

The tested environment encountered a **PaddleOCR OneDNN compatibility issue** related to the underlying CPU architecture.

The OCR pipeline is implemented, but this environment-specific issue may require a compatible PaddleOCR runtime or hardware configuration.

The system also includes fallback extraction when the optional Qwen2.5-VL/Ollama parsing component is unavailable.

### ML Dataset Size

The current classification model uses **212 training samples**. Increasing the training dataset would improve generalization, particularly for categories with lower precision or recall.

### Category Performance

The **Shopping** category currently has lower precision due to overlap with other spending categories.

---

# 🔮 Future Enhancements

- 📈 Time-series expense forecasting
- 🚨 Real-time anomaly notifications
- 🎯 Personalized spending recommendations
- 📄 CSV/PDF financial report export
- 🧾 Receipt OCR confidence reporting
- 📱 Mobile-responsive improvements
- 📦 Batch receipt processing
- ☁️ Cloud deployment
- 🤖 More advanced multimodal receipt understanding

---

# 🎯 Project Highlights

| Metric / Capability | Result |
|---------------------|--------|
| **ML Training Samples** | 212 |
| **Expense Categories** | 10 |
| **Precision** | **85.4%** |
| **Recall** | **78.8%** |
| **F1-Score** | **79.4%** |
| **Prediction Latency** | **<10 ms** |
| **Receipt OCR** | PaddleOCR |
| **Multimodal AI** | Qwen2.5-VL |
| **Classification** | TF-IDF + Logistic Regression |
| **Anomaly Detection** | Z-score + frequency + duplicate analysis |
| **Backend** | Flask |
| **Database** | SQLite + SQLAlchemy |

---

# ⚙️ Getting Started

## Prerequisites

- Python 3.10+
- pip
- Git
- Ollama (optional, for Qwen2.5-VL parsing)

## 1. Clone the Repository

```bash
git clone <repository-url>
cd finance-tracker
```

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## 3. Train the ML Model

```bash
cd backend
python train_model.py
```

The trained model and vectorizer are saved under:

```text
backend/models/
```

## 4. Start the Flask Backend

```bash
python run.py
```

The backend runs at:

```text
http://localhost:5000
```

## 5. Optional: Enable Qwen2.5-VL

Install and run Ollama, then make the Qwen2.5-VL model available.

```bash
ollama serve
```

When the LLM parser is unavailable, the application falls back to regex-based extraction.

## 6. Open the Application

```text
http://localhost:5000/frontend/login.html
```

---

# 📌 Project Status

**Status:** Production-ready application with a documented PaddleOCR hardware compatibility limitation.

The implemented system provides a complete workflow from **receipt image ingestion to OCR, structured extraction, machine learning categorization, database persistence, analytics, and anomaly detection**.

---

# 👩‍💻 Author

**Anusree Reddy**

Information Technology  
Chaitanya Bharathi Institute of Technology, Hyderabad

---

⭐ If you found this project interesting, consider giving the repository a star.

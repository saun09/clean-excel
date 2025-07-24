# Xelly – Excel Automation & Analysis

**Xelly** is a full-stack web application designed to simplify the cleaning, clustering, analysis, and forecasting of trade and product data stored in Excel or CSV files. It leverages machine learning techniques and time-series forecasting to deliver insights without requiring coding expertise.

**Live App:** [clean-excel.vercel.app](https://clean-excel.vercel.app)

---

## **Table of Contents**
1. [Problem Statement](#problem-statement)
2. [Proposed Solution](#proposed-solution)
3. [Key Features](#key-features)
    - [1. File Upload and Format Support](#1-file-upload-and-format-support)
    - [2. Cosine Similarity-Based Clustering](#2-cosine-similarity-based-clustering)
    - [3. Data Analysis & Filtering](#3-data-analysis--filtering)
    - [4. Forecasting](#4-forecasting)
    - [5. Company-wise Analysis Dashboard](#5-company-wise-analysis-dashboard)
4. [System Architecture](#system-architecture)
5. [Deployment and Security](#deployment-and-security)
6. [Installation (Local Development)](#installation-local-development)
7. [Tech Stack](#tech-stack)
8. [Author](#author)

---

## **Problem Statement**

Consulting firms and analysts frequently deal with messy Excel files containing raw trade data with inconsistent entries, typographical errors, and non-standardized naming conventions. Manual cleaning and clustering is tedious and error-prone, while advanced analysis and forecasting are limited in Excel.

---

## **Proposed Solution**

Xelly automates:
- Data cleaning and standardization
- Clustering similar entries using **TF-IDF + Cosine Similarity** and **Sentence Transformers**
- Trade data filtering and interactive dashboards
- Forecasting product prices or quantities using **Prophet**, **Linear Regression**, and **Polynomial Regression**

---

## **Key Features**

### **1. File Upload and Format Support**
- Upload Excel (.xlsx) or CSV (.csv) files via drag-and-drop or file picker.
- Automated data cleaning: trimming spaces, normalizing formats, currency (USD), and unit conversions (e.g., UQC → KG).
- Preview cleaned data and download standardized files.

### **2. Cosine Similarity-Based Clustering**
- Groups similar text entries like `“Petroleum coke”` and `“Petroleum coke bulk”`.
- Adjustable similarity threshold.
- Option to accept or reject suggested replacements.

### **3. Data Analysis & Filtering**
- **Trade Type Detection** (Import/Export).
- Multi-level filtering by city, supplier, HS code, value, year, etc.
- Insights include:
  - Top importer-supplier pairs
  - Market share metrics
  - Unit price trends
  - Importer-supplier heatmaps

### **4. Forecasting**
- Time-series forecasts for columns (e.g., quantity or unit price).
- Models:
  - Linear Regression
  - Polynomial Regression
  - Prophet (Meta)
- Outputs:
  - 2-year forecast (line + bar charts)
  - Model performance metrics (MAE, RMSE, R²)
  - Seasonal patterns and historical trends

### **5. Company-wise Analysis Dashboard**
- Key statistics: transaction count, unique products, time range.
- Quantity and price metrics.
- Product-specific transaction records.

---

## **System Architecture**

- **Frontend:** React (Vercel hosting).
- **Backend:** Flask API (Render hosting).
- **Core Modules:**
  - `upload_bp` – File upload, cleaning.
  - `cluster_bp` / `cosine_bp` – TF-IDF & cosine similarity clustering.
  - `filter_bp` – Trade data filtering and analysis.
  - `company_bp` – Company-level metrics.
  - `forecast_bp` – Prophet-based time series forecasting.

---

## **Deployment and Security**
- **Frontend:** Hosted on Vercel (HTTPS, TLS, CI/CD).
- **Backend:** Hosted on Render (HTTPS endpoints, environment variables for sensitive keys).
- **CORS Policies & Server Validation** for data protection.

---

## **Installation (Local Development)**

```bash
# Clone repository
git clone https://github.com/saun09/clean-excel.git

# Backend Setup
cd backend
pip install -r requirements.txt
flask run

# Frontend Setup
cd frontend
npm install
npm run dev

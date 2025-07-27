# 📄 Challenge 1A: PDF Outline Extraction

## 📌 Overview
This solution extracts a structured outline (title and headings) from PDF documents.

✅ **Features:**
- Multilingual support for headings  
- Statistical font analysis for heading detection  
- Works offline and fast (50‑page PDF in under 10 seconds)

---

## ⚙️ Approach

**Core steps:**
1. **Font statistics analysis:**  
   Gathers font sizes and determines thresholds for H1, H2, H3.  
2. **Multilingual regex patterns:**  
   Detects headings like numbered headings (`1.`, `1.1.`), chapters (`CHAPTER`, `第1章`), and formal headings.  
3. **Font style and position analysis:**  
   Bold text, top‑of‑page position, and short length give higher heading scores.  
4. **Outline optimization:**  
   Duplicate removal, sorting by page, and validation of heading structure.

---

## 📚 Libraries Used
- **[PyMuPDF (fitz)](https://pymupdf.readthedocs.io/)** – PDF parsing with detailed font and position metadata.
- **numpy** – Statistical calculations of font size thresholds.
- **unicodedata** – Normalization and cleaning of extracted text.

---

## 🚀 Build and Run Instructions

### 🏗️ Build the Docker Image
Run this in your `Challenge_1A` folder:
```bash
docker build --platform linux/amd64 -t pdf-extractor:v1 .

### ▶️ Run the Container

###
📌 On Windows PowerShell:
```bash
docker run --rm -v ${PWD}/input:/app/input -v ${PWD}/output:/app/output --network none pdf-extractor:v1

###
📌 On Windows CMD:
```bash
docker run --rm -v %cd%/input:/app/input -v %cd%/output:/app/output --network none pdf-extractor:v1

###
📌 On Linux / macOS:
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none pdf-extractor:v1

###
📦 Folder Structure
```bash
Challenge_1A/
├─ input/         # Place your input PDFs here
├─ output/        # JSON outputs will be generated here
├─ extractor_enhanced.py
├─ requirements.txt
├─ Dockerfile
└─ README.md

### Performance
✅ Processes 50‑page PDFs in under 10 seconds
✅ Works offline, CPU-only
✅ Model size: < 200 MB
✅ Handles multilingual headings and complex layouts

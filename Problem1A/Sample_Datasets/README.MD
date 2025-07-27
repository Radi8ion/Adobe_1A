# Challenge 1A: PDF Outline Extraction

## Approach
This solution uses PyMuPDF to extract structured outlines from PDFs using statistical font analysis and multilingual pattern matching.

### Key Algorithms:
1. Statistical font size analysis to determine heading thresholds
2. Multilingual regex patterns for numbered headings and chapters
3. Font style and position analysis
4. Duplicate removal and outline optimization

## Libraries Used
- **PyMuPDF**: PDF text extraction with formatting details
- **numpy**: Statistical analysis for font thresholds
- **unicodedata**: Text normalization

## How to Build and Run

### Build:
```bash
docker build --platform linux/amd64 -t pdf-extractor:v1 .
```

Run (On Windows PowerShell):
```bash
docker run --rm -v ${PWD}/input:/app/input -v ${PWD}/output:/app/output --network none pdf-extractor:v1
```

Run (On Windows CMD):
```bash
docker run --rm -v %cd%/input:/app/input -v %cd%/output:/app/output --network none pdf-extractor:v1
```

Run (On Linux / macOS):
```bash
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none pdf-extractor:v1
```

 Folder Structure
```bash
Challenge_1A/
├─ input/         # Place your input PDFs here
├─ output/        # JSON outputs will be generated here
├─ extractor_enhanced.py
├─ requirements.txt
├─ Dockerfile
└─ README.md
```

 Performance
-  Processes 50‑page PDFs in under 10 seconds
-  Works offline, CPU-only
-  Model size: < 200 MB
-  Handles multilingual headings and complex layouts




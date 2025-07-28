# Challenge 1A: PDF Outline Extraction

## Overview
This solution automatically extracts structured outlines from PDF files by analyzing font statistics, positions, and multilingual heading patterns.
It produces a clean hierarchical JSON outline ready to be consumed by subsequent stages (like Challenge 1B).

## Approach
We use PyMuPDF to read PDF text along with style metadata (font sizes, positions, bold/italic info).
Then, we apply statistical font analysis to detect headings and use multilingual regex patterns to recognize numbered sections and chapters.

### Key Algorithms:
1. Scan the /app/input directory for all .pdf files.
2. For each PDF:
- Use PyMuPDF to extract text blocks along with font size, style, and position.
3. Normalize and analyze font sizes across the document to estimate heading thresholds.
4. Detect headings using:
- Font size/style (bold, large)
- Multilingual regex patterns for numbered formats (e.g., “1.”, “1.1”, “Chapter 2”).
5. Determine heading levels (H1, H2, H3) based on statistical and structural rules.
6. Remove duplicates and refine the hierarchy for consistency.
7. Output a JSON file per PDF with structured headings (text, level, page).

## Libraries Used
- **PyMuPDF** – PDF parsing with font/position info
- **numpy** – Statistical font analysis
- **unicodedata** – Unicode normalization
- **re** – Regex-based heading detection

## Input PDFs
### **IMPORTANT**
Place all the PDFs you want to process inside the input/ folder in the root of this challenge folder.
The system will automatically scan this folder and process every PDF present.
Do not rename or change folder structure.
The generated JSON outputs will appear in the output/ folder with the same base names as the PDFs.

Example:
```bash
Challenge_1A/
├─ input/
│  ├─ sample.pdf
│  ├─ document1.pdf
│  └─ thesis.pdf
├─ output/        # output JSONs will be created here
...
```


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
docker run --rm -v %cd%/input:/app/input -v %cd%/output:/app/output --network none pdf-extractor:v1
```
## Folder Structure
```bash
Challenge_1A/
├─ input/         # Place your input PDFs here
├─ output/        # JSON outputs will be generated here
├─ extractor_enhanced.py
├─ requirements.txt
├─ Dockerfile
└─ README.md
```

## Performance
-  Processes 50‑page PDFs in under 10 seconds
-  Works offline, CPU-only
-  Model size: < 200 MB
-  Handles multilingual headings and complex layouts

## Output Format
```bash
[
  {
    "text": "Introduction",
    "level": "H1",
    "page": 1
  },
  {
    "text": "Background and Motivation",
    "level": "H2",
    "page": 2
  }
]
```


import os
import json
import time
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
import logging
from collections import Counter, defaultdict
import unicodedata
import numpy as np
import fitz

#logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFOutlineExtractor:    
    def __init__(self):
        self.heading_patterns = {
            'numbered': [
                # English, European, Arabic numerals
                r'^\d+\.?\s+[A-ZÀ-ÿĀ-žА-я一-龯ا-ي\u0600-\u06FF]',
                r'^\d+\.\d+\.?\s+[A-ZÀ-ÿĀ-žА-я一-龯ا-ي\u0600-\u06FF]',
                r'^\d+\.\d+\.\d+\.?\s+[A-ZÀ-ÿĀ-žА-я一-龯ا-ي\u0600-\u06FF]',
                # Roman numerals
                r'^[IVXLCDMivxlcdm]+\.?\s+[A-ZÀ-ÿĀ-žА-я一-龯ا-ي\u0600-\u06FF]',
                # Alphabetic numbering
                r'^[A-Za-z]\.?\s+[A-ZÀ-ÿĀ-žА-я一-龯ا-ي\u0600-\u06FF]',
            ],
            'chapter_section': [
                # Multilingual chapter/section keywords
                r'^(Chapter|CHAPTER|第\d*章|Kapitel|Chapitre|Capítulo|Глава|الفصل)\s*\d*',
                r'^(Section|SECTION|節|§|Abschnitt|Section|Sección|Раздел|القسم)\s*\d*',
                r'^(Part|PART|部|Teil|Partie|Parte|Часть|الجزء)\s*\d*',
                # Academic paper sections
                r'^(Abstract|Introduction|Methodology|Results|Discussion|Conclusion|References)',
                r'^(摘要|介绍|方法|结果|讨论|结论|参考文献)',
                r'^(Zusammenfassung|Einleitung|Methodik|Ergebnisse|Diskussion|Fazit)',
            ],
            'formal_headings': [
                # All caps headings (multilingual)
                r'^[A-ZÀ-ÿĀ-žА-я一-龯ا-ي\u0600-\u06FF]{2,}[A-ZÀ-ÿĀ-žА-я一-龯ا-ي\u0600-\u06FF\s]*$',
                # Title case with proper structure
                r'^[A-ZÀ-ÿĀ-žА-я一-龯ا-ي\u0600-\u06FF][a-zA-ZÀ-ÿĀ-žА-я一-龯ا-ي\u0600-\u06FF\s]*[A-ZÀ-ÿĀ-žА-я一-龯ا-ي\u0600-\u06FF]$',
            ]
        }
        
        # To avoid false positives
        self.stop_patterns = [
            r'^\d+$',  # Just numbers
            r'^page\s*\d+',  # Page numbers
            r'^\d+\s*/\s*\d+$',  # Page x/y
            r'^©.*',  # Copyright
            r'^www\..*|http[s]?://.*',  # URLs
            r'^\s*$',  # Empty
            r'^.*@.*\..*$',  # Email addresses
            r'^\d{1,2}:\d{2}',  # Time stamps
        ]
    
    def extract_title(self, doc: fitz.Document) -> str:
        """Extract document title using advanced heuristics."""
        # Document metadata
        metadata = doc.metadata
        if metadata.get('title') and metadata['title'].strip():
            title = metadata['title'].strip()
            if (len(title) > 3 and len(title) < 200 and 
                not any(skip in title.lower() for skip in ['untitled', 'document', 'microsoft', 'pdf'])):
                return self._clean_text(title)
        
        # First page title detection
        if len(doc) > 0:
            page = doc[0]
            text_blocks = self._extract_text_with_formatting(page)
            
            # Potential titles based on font characteristics
            title_candidates = []
            
            for block in text_blocks:
                text = block['text'].strip()
                font_size = block['font_size']
                is_bold = block['is_bold']
                position_y = block['position_y']
                
                # Title criteria: large font, bold, near top, reasonable length
                if (len(text) > 10 and len(text) < 150 and
                    font_size >= 14 and  # Reasonably large
                    position_y < 200 and  # Near top of page
                    not self._is_stop_pattern(text) and
                    not re.match(r'^\d+\.', text)):  # Not a numbered heading
                    
                    score = font_size
                    if is_bold:
                        score += 5
                    if position_y < 100:
                        score += 3
                    
                    title_candidates.append((text, score))
            
            if title_candidates:
                # Highest scoring candidate
                title_candidates.sort(key=lambda x: x[1], reverse=True)
                return self._clean_text(title_candidates[0][0])
        
        return "Untitled"
    
    def _extract_text_with_formatting(self, page: fitz.Page) -> List[Dict]:
        """Extract text with detailed formatting information."""
        blocks = page.get_text("dict")["blocks"]
        text_blocks = []
        
        for block in blocks:
            if "lines" in block:
                bbox = block["bbox"]
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text:
                            text_blocks.append({
                                'text': text,
                                'font_size': span['size'],
                                'font_name': span.get('font', ''),
                                'is_bold': bool(span['flags'] & 2**4),
                                'is_italic': bool(span['flags'] & 2**6),
                                'position_x': span['bbox'][0],
                                'position_y': span['bbox'][1],
                                'bbox': span['bbox']
                            })
        
        return text_blocks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        text = unicodedata.normalize('NFKC', text)
        text = ' '.join(text.split())
        text = re.sub(r'[^\w\s\-.,;:()[\]{}\'\"]+', ' ', text)
        return text.strip()
    
    def _is_stop_pattern(self, text: str) -> bool:
        """Check if text matches stop patterns."""
        for pattern in self.stop_patterns:
            if re.match(pattern, text, re.IGNORECASE | re.MULTILINE):
                return True
        return False
    
    def calculate_font_statistics(self, doc: fitz.Document) -> Dict[str, Any]:
        """Calculate comprehensive font statistics using statistical analysis."""
        font_sizes = []
        font_names = []
        is_bold_list = []
        
        sample_pages = min(10, len(doc))
        for page_num in range(sample_pages):
            page = doc[page_num]
            text_blocks = self._extract_text_with_formatting(page)
            
            for block in text_blocks:
                if len(block['text']) > 2:  # Filter out single characters
                    font_sizes.append(block['font_size'])
                    font_names.append(block['font_name'])
                    is_bold_list.append(block['is_bold'])
        
        if not font_sizes:
            return {
                "body_size": 12.0,
                "heading_thresholds": [14.0, 16.0, 18.0],
                "font_names": [],
                "bold_ratio": 0.0
            }
        
        # Statistical analysis
        font_sizes = np.array(font_sizes)
        body_size = np.median(font_sizes)
        q75 = np.percentile(font_sizes, 75)
        q90 = np.percentile(font_sizes, 90)
        q95 = np.percentile(font_sizes, 95)
        
        # Define heading thresholds based on distribution
        h3_threshold = max(body_size + 1, q75)
        h2_threshold = max(body_size + 2, q90)
        h1_threshold = max(body_size + 3, q95)
        
        return {
            "body_size": float(body_size),
            "heading_thresholds": [float(h3_threshold), float(h2_threshold), float(h1_threshold)],
            "font_names": list(set(font_names)),
            "bold_ratio": sum(is_bold_list) / len(is_bold_list) if is_bold_list else 0.0,
            "size_stats": {
                "mean": float(np.mean(font_sizes)),
                "std": float(np.std(font_sizes)),
                "min": float(np.min(font_sizes)),
                "max": float(np.max(font_sizes))
            }
        }
    
    def detect_heading_level(self, text_block: Dict, font_stats: Dict, page_context: Dict) -> Optional[str]:
        """Advanced heading detection using multiple algorithms."""
        text = text_block['text']
        font_size = text_block['font_size']
        is_bold = text_block['is_bold']
        position_y = text_block['position_y']
        
        clean_text = self._clean_text(text)
        
        # Skip invalid text
        if (len(clean_text) < 2 or len(clean_text) > 500 or 
            self._is_stop_pattern(clean_text)):
            return None
        
        heading_score = 0
        level_indicators = {"h1": 0, "h2": 0, "h3": 0}
        
        # 1. Font Size Analysis (very important bruh)
        body_size = font_stats["body_size"]
        h3_thresh, h2_thresh, h1_thresh = font_stats["heading_thresholds"]
        
        size_ratio = font_size / body_size
        
        if font_size >= h1_thresh:
            level_indicators["h1"] += 3
            heading_score += 3
        elif font_size >= h2_thresh:
            level_indicators["h2"] += 2
            heading_score += 2
        elif font_size >= h3_thresh:
            level_indicators["h3"] += 1
            heading_score += 1
        
        # 2. Font Style Analysis (also important bruh)
        if is_bold:
            heading_score += 1.5
            # Bold text may be higher-level headings
            if font_size >= body_size:
                level_indicators["h1"] += 0.5
        
        # 3. Pattern Matching (for multilingual)
        pattern_score, pattern_level = self._analyze_text_patterns(clean_text)
        heading_score += pattern_score
        if pattern_level:
            level_indicators[pattern_level] += pattern_score
        
        # 4. Positional Analysis
        if position_y < page_context.get('height', 800) * 0.15:  # Top 15% of page
            heading_score += 0.5
            level_indicators["h1"] += 0.3
        
        # 5. Length Analysis
        word_count = len(clean_text.split())
        if 2 <= word_count <= 10:  # Ideal heading length
            heading_score += 0.5
        elif word_count > 20:  # Too long for typical heading
            heading_score -= 1
        
        # 6. Structural Analysis
        if clean_text.endswith(':'):
            heading_score += 0.3
            level_indicators["h3"] += 0.5
        
        # Decision Logic
        if heading_score < 1.5:
            return None
        
        # Determine level based on combined indicators
        max_level = max(level_indicators.items(), key=lambda x: x[1])
        
        if max_level[1] >= 2.5:
            return max_level[0].upper()
        elif heading_score >= 2.5:
            return "H1"
        elif heading_score >= 2.0:
            return "H2"
        else:
            return "H3"
    
    def _analyze_text_patterns(self, text: str) -> Tuple[float, Optional[str]]:
        """Analyze text patterns for heading detection."""
        score = 0
        suggested_level = None
        
        # Check numbered patterns
        for pattern in self.heading_patterns['numbered']:
            if re.match(pattern, text, re.IGNORECASE):
                score += 2
                # Determine level based on numbering depth
                if '.' in text[:10]:
                    depth = text[:10].count('.')
                    if depth == 1:
                        suggested_level = "h1"
                    elif depth == 2:
                        suggested_level = "h2"
                    else:
                        suggested_level = "h3"
                else:
                    suggested_level = "h1"
                break
        
        # Check chapter/section patterns
        if score == 0:  # Only if not already matched
            for pattern in self.heading_patterns['chapter_section']:
                if re.match(pattern, text, re.IGNORECASE):
                    score += 2.5
                    suggested_level = "h1"
                    break
        
        # Check formal heading patterns
        if score == 0:
            for pattern in self.heading_patterns['formal_headings']:
                if re.match(pattern, text):
                    if text.isupper():
                        score += 1.5
                        suggested_level = "h1"
                    else:
                        score += 1
                        suggested_level = "h2"
                    break
        
        # Additional heuristics
        if text[0].isupper() and len(text.split()) <= 6:
            score += 0.3
        
        return score, suggested_level
    
    def extract_outline(self, pdf_path: str) -> Dict[str, Any]:
        """Extract comprehensive outline using advanced algorithms."""
        start_time = time.time()
        
        try:
            doc = fitz.open(pdf_path)
            title = self.extract_title(doc)
            font_stats = self.calculate_font_statistics(doc)
            outline = []
            seen_headings: Set[str] = set()
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_context = {
                    'height': page.rect.height,
                    'width': page.rect.width,
                    'number': page_num + 1
                }
                
                text_blocks = self._extract_text_with_formatting(page)
                
                for block in text_blocks:
                    level = self.detect_heading_level(block, font_stats, page_context)
                    
                    if level:
                        text = block['text']
                        heading_key = f"{level}:{text}:{page_num + 1}"
                        
                        if heading_key not in seen_headings:
                            outline.append({
                                "level": level,
                                "text": text,
                                "page": page_num + 1
                            })
                            seen_headings.add(heading_key)
            
            doc.close()
            
            # Post-process & optimize outline
            outline = self._optimize_outline(outline)
            
            result = {
                "title": title,
                "outline": outline
            }

            result = self._validate_schema_compliance(result)
            processing_time = time.time() - start_time
            logger.info(f"Processed {pdf_path} in {processing_time:.2f}s, found {len(outline)} headings")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {e}")
            return {
                "title": "Untitled",
                "outline": []
            }
    
    def _optimize_outline(self, outline: List[Dict]) -> List[Dict]:
        """Optimize outline structure and remove redundancies."""
        if not outline:
            return outline
        
        # Remove duplicates while preserving order
        seen = set()
        unique_outline = []
        
        for item in outline:
            key = (item["level"], item["text"].lower(), item["page"])
            if key not in seen:
                seen.add(key)
                unique_outline.append(item)
        
        # Sort by page number, then by original order
        unique_outline.sort(key=lambda x: (x["page"], outline.index(x) if x in outline else 0))
        
        # Remove overly generic headings that appear too frequently
        text_counts = Counter(item["text"].lower() for item in unique_outline)
        filtered_outline = [
            item for item in unique_outline 
            if text_counts[item["text"].lower()] < len(unique_outline) * 0.1  # Less than 10% frequency
        ]
        
        return filtered_outline
        
    def _validate_schema_compliance(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure output strictly complies with the JSON schema."""
        # Ensure title is always a string
        if not isinstance(result.get("title"), str):
            result["title"] = "Untitled"
        
        # Ensure outline is always an array
        if not isinstance(result.get("outline"), list):
            result["outline"] = []
        
        # Validate each outline item
        validated_outline = []
        for item in result.get("outline", []):
            if isinstance(item, dict):
                # Ensure all required fields exist and have correct types
                validated_item = {
                    "level": str(item.get("level", "H3")),
                    "text": str(item.get("text", "")),
                    "page": int(item.get("page", 1))
                }
                # Only include items with non-empty text
                if validated_item["text"].strip():
                    validated_outline.append(validated_item)
        
        result["outline"] = validated_outline
        return result


def process_pdfs():
    """Main processing function for Challenge 1A."""
    logger.info("Starting PDF processing")
    
    # Get input and output directories
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")

    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize extractor
    extractor = PDFOutlineExtractor()
    
    # Get all PDF files
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning("No PDF files found in input directory")
        # Create empty output.json
        output_file = output_dir / "output.json"
        with open(output_file, "w", encoding='utf-8') as f:
            json.dump({"title": "Untitled", "outline": []}, f, indent=2, ensure_ascii=False)
        return
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    total_start_time = time.time()
    
    # Process single PDF case (output direct JSON)
    if len(pdf_files) == 1:
        pdf_file = pdf_files[0]
        try:
            result = extractor.extract_outline(str(pdf_file))
            
            # Create output file named after input PDF
            output_file = output_dir / f"{pdf_file.stem}.json"
            with open(output_file, "w", encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Processed {pdf_file.name}")
                
        except Exception as e:
            logger.error(f"Failed to process {pdf_file.name}: {e}")
            # Create error output
            output_file = output_dir / f"{pdf_file.stem}.json"
            with open(output_file, "w", encoding='utf-8') as f:
                json.dump({"title": "Untitled", "outline": []}, f, indent=2, ensure_ascii=False)

    
    # Process multiple PDFs case (output nested JSON)
    else:
        all_results = {}
        
        for pdf_file in pdf_files:
            try:
                result = extractor.extract_outline(str(pdf_file))
                file_key = pdf_file.stem
                all_results[file_key] = result
                
                logger.info(f"Processed {pdf_file.name}")
                
            except Exception as e:
                logger.error(f"Failed to process {pdf_file.name}: {e}")
                all_results[pdf_file.stem] = {
                    "title": "Untitled",
                    "outline": []
                }
        
        # Create output.json file
        output_file = output_dir / "output.json"
        with open(output_file, "w", encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    total_time = time.time() - total_start_time
    logger.info(f"Completed processing {len(pdf_files)} files in {total_time:.2f}s")
    logger.info(f"Output saved to {output_dir / 'output.json'}")

if __name__ == "__main__":
    process_pdfs()
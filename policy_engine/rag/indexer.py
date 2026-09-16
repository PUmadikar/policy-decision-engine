import re
import fitz
from typing import List
from dataclasses import dataclass

@dataclass
class PolicyChunk:
    chunk_id: str
    page: int
    section: str
    sub_section: str
    text: str

class PolicyIndexer:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    def load_and_chunk(self) -> List[PolicyChunk]:
        doc = fitz.open(self.pdf_path)
        chunks: List[PolicyChunk] = []
        
        current_section = "GENERAL PROSPECTUS"
        current_subsection = "INTRO"
        
        # Section detection regexes
        section_patterns = [
            (r'^\s*DEFINITIONS\b', "DEFINITIONS"),
            (r'^\s*SCOPE OF COVER\b', "SCOPE OF COVER"),
            (r'^\s*WHAT\s+WE\s+COVER\b', "SCOPE OF COVER - WHAT WE COVER"),
            (r'^\s*WHAT\s+WE\s+EXCLUDE\b', "EXCLUSIONS - WHAT WE EXCLUDE"),
            (r'^\s*EXTENSIONS\b', "EXTENSIONS"),
            (r'^\s*CONDITIONS\b', "GENERAL CONDITIONS"),
            (r'^\s*PORTABILITY\b', "PORTABILITY"),
            (r'^\s*CLAIMS\s+PROCEDURE\b', "CLAIMS PROCEDURE"),
        ]

        for page_idx in range(len(doc)):
            page_num = page_idx + 1
            page = doc[page_idx]
            text = page.get_text("text")
            lines = text.split("\n")
            
            paragraph_buffer = []
            
            for line in lines:
                clean_line = line.strip()
                if not clean_line:
                    continue

                # Check if header
                matched_sec = None
                for pat, sec_name in section_patterns:
                    if re.search(pat, clean_line, re.IGNORECASE):
                        matched_sec = sec_name
                        break

                if matched_sec:
                    # Flush current paragraph buffer before switching section
                    if paragraph_buffer:
                        p_text = " ".join(paragraph_buffer)
                        if len(p_text) > 30:
                            cid = f"P{page_num}_C{len(chunks)+1}"
                            chunks.append(PolicyChunk(
                                chunk_id=cid,
                                page=page_num,
                                section=current_section,
                                sub_section=current_subsection,
                                text=p_text
                            ))
                        paragraph_buffer = []
                    current_section = matched_sec
                    current_subsection = clean_line
                    continue

                # Sub-section / clause detection
                if re.match(r'^\d+\.\s+[A-Z]', clean_line) or re.match(r'^[A-Z][a-z]+:', clean_line):
                    if paragraph_buffer:
                        p_text = " ".join(paragraph_buffer)
                        if len(p_text) > 30:
                            cid = f"P{page_num}_C{len(chunks)+1}"
                            chunks.append(PolicyChunk(
                                chunk_id=cid,
                                page=page_num,
                                section=current_section,
                                sub_section=current_subsection,
                                text=p_text
                            ))
                        paragraph_buffer = []
                    current_subsection = clean_line[:50]

                paragraph_buffer.append(clean_line)
                
                # Chunk size cutoff around 400-500 words
                if len(" ".join(paragraph_buffer)) > 800:
                    p_text = " ".join(paragraph_buffer)
                    cid = f"P{page_num}_C{len(chunks)+1}"
                    chunks.append(PolicyChunk(
                        chunk_id=cid,
                        page=page_num,
                        section=current_section,
                        sub_section=current_subsection,
                        text=p_text
                    ))
                    paragraph_buffer = []

            if paragraph_buffer:
                p_text = " ".join(paragraph_buffer)
                if len(p_text) > 30:
                    cid = f"P{page_num}_C{len(chunks)+1}"
                    chunks.append(PolicyChunk(
                        chunk_id=cid,
                        page=page_num,
                        section=current_section,
                        sub_section=current_subsection,
                        text=p_text
                    ))
                paragraph_buffer = []

        return chunks

if __name__ == "__main__":
    from policy_engine.config import settings
    indexer = PolicyIndexer(settings.POLICY_PDF_PATH)
    chunks = indexer.load_and_chunk()
    print(f"Extracted {len(chunks)} non-naive chunks.")
    for c in chunks[:5]:
        print(f"[{c.chunk_id}] Page {c.page} | Section: {c.section} | Subsection: {c.sub_section}\n{c.text[:150]}...\n")

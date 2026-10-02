"""
PDF loader and parser for GDG-USAR Student Handbook.
Extracts pages, detects section headings (including merged heading quirks),
and attaches rich section and page metadata to documents.
"""

import re
from pathlib import Path
from typing import List, Optional
import pypdf
from langchain_core.documents import Document

from src.config import DEFAULT_PDF_PATH


def normalize_merged_headings(text: str) -> str:
    """
    Handles PDF extraction quirk where a section heading is merged directly
    into the previous paragraph (e.g., '...event announcement.4. Project Submissions').
    Inserts line breaks so section headings start on their own line.
    """
    # Fix instances where heading is merged after punctuation: e.g. "announcement.4. Project Submissions"
    # Group 1: punctuation character
    # Group 2: section number and start of title
    cleaned = re.sub(
        r"([.!?])\s*(\d+\.\s+[A-Z])",
        r"\1\n\n\2",
        text
    )
    
    # Also handle instances where heading occurs without punctuation right before it
    # e.g. "words4. Project Submissions"
    cleaned = re.sub(
        r"([a-z])(\d+\.\s+[A-Z])",
        r"\1\n\n\2",
        cleaned
    )
    
    # Ensure any line that looks like a section heading has newlines around it
    cleaned = re.sub(
        r"\n?(\d+\.\s+[A-Z][^\n\r]+?)(?=\n|$)",
        r"\n\1\n",
        cleaned
    )
    
    return cleaned


def load_and_parse_handbook(
    pdf_path: Optional[Path] = None,
    print_detected_sections: bool = True
) -> List[Document]:
    """
    Loads the PDF handbook and splits it into section documents with accurate
    section_number, section_title, page, and source metadata.

    Args:
        pdf_path: Path to the handbook PDF. Defaults to DEFAULT_PDF_PATH.
        print_detected_sections: Whether to print detected sections for verification.

    Returns:
        List of LangChain Document objects.
    """
    path = Path(pdf_path) if pdf_path else DEFAULT_PDF_PATH
    if not path.exists():
        raise FileNotFoundError(f"Source PDF file not found at: {path}")

    reader = pypdf.PdfReader(str(path))
    section_header_regex = re.compile(r"^\s*(\d+)\.\s+([A-Z][^\n\r]+)", re.MULTILINE)

    documents: List[Document] = []
    detected_sections_log = []

    current_section_num = 0
    current_section_title = "About This Document"

    for page_idx, page in enumerate(reader.pages):
        page_num = page_idx + 1
        raw_text = page.extract_text() or ""
        normalized_text = normalize_merged_headings(raw_text)

        matches = list(section_header_regex.finditer(normalized_text))

        if not matches:
            # Whole page or continuation belongs to current section
            cleaned_page = normalized_text.strip()
            if cleaned_page:
                documents.append(
                    Document(
                        page_content=cleaned_page,
                        metadata={
                            "source": str(path),
                            "page": page_num,
                            "section_number": current_section_num,
                            "section_title": current_section_title,
                        },
                    )
                )
        else:
            # Check for preamble text before the first section match on this page
            first_match = matches[0]
            if first_match.start() > 0:
                preamble_content = normalized_text[: first_match.start()].strip()
                if preamble_content:
                    documents.append(
                        Document(
                            page_content=preamble_content,
                            metadata={
                                "source": str(path),
                                "page": page_num,
                                "section_number": current_section_num,
                                "section_title": current_section_title,
                            },
                        )
                    )
                    detected_sections_log.append(
                        (current_section_num, current_section_title, page_num)
                    )

            # Process each section header match
            for i, match in enumerate(matches):
                sec_num = int(match.group(1))
                sec_title = match.group(2).strip()
                current_section_num = sec_num
                current_section_title = sec_title

                start_idx = match.end()
                end_idx = matches[i + 1].start() if i + 1 < len(matches) else len(normalized_text)

                body = normalized_text[start_idx:end_idx].strip()
                # Clean trailing document footer markers if present
                body = re.sub(r"End of sample document\s*$", "", body).strip()

                full_section_text = f"{sec_num}. {sec_title}\n{body}" if body else f"{sec_num}. {sec_title}"

                documents.append(
                    Document(
                        page_content=full_section_text,
                        metadata={
                            "source": str(path),
                            "page": page_num,
                            "section_number": sec_num,
                            "section_title": sec_title,
                        },
                    )
                )
                detected_sections_log.append((sec_num, sec_title, page_num))

    if print_detected_sections:
        print("\n" + "=" * 60)
        print("DETECTED SECTIONS IN GDG-USAR STUDENT HANDBOOK:")
        print("=" * 60)
        seen = set()
        for s_num, s_title, p_num in detected_sections_log:
            key = (s_num, s_title)
            if key not in seen:
                seen.add(key)
                print(f"  * Section {s_num}: {s_title} (Page {p_num})")
        print("=" * 60 + "\n")

    return documents


if __name__ == "__main__":
    docs = load_and_parse_handbook()
    print(f"Total documents extracted: {len(docs)}")
    for d in docs:
        print(f"Section {d.metadata['section_number']}: {d.metadata['section_title']} (Page {d.metadata['page']}) - Length: {len(d.page_content)}")

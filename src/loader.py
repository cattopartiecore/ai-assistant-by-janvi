"""
Document loader and parser for GDG-USAR Knowledge Base.
Supports multi-document loading (.pdf, .txt, .md) from data/ directory.
Tags each document chunk with:
- source_file (e.g., 'GDG_USAR_AI_Document_Assistant_Source_TASK3.pdf')
- doc_title (e.g., 'GDG-USAR Student Handbook')
- section (e.g., 'Section 1: Student Support Desk')
- section_number (int or str)
- section_title (str)
- page (int)
- doc_type ('handbook' for primary official handbook, 'extra' for other docs)
"""

import re
from pathlib import Path
from typing import List, Optional, Dict, Any
import pypdf
from langchain_core.documents import Document

from src.config import DATA_DIR, DEFAULT_PDF_PATH


def normalize_merged_headings(text: str) -> str:
    """
    Handles PDF extraction quirk where a section heading is merged directly
    into the previous paragraph (e.g., '...event announcement.4. Project Submissions').
    Inserts line breaks so section headings start on their own line.
    """
    cleaned = re.sub(r"([.!?])\s*(\d+\.\s+[A-Z])", r"\1\n\n\2", text)
    cleaned = re.sub(r"([a-z])(\d+\.\s+[A-Z])", r"\1\n\n\2", cleaned)
    cleaned = re.sub(r"\n?(\d+\.\s+[A-Z][^\n\r]+?)(?=\n|$)", r"\n\1\n", cleaned)
    return cleaned


def parse_handbook_pdf(pdf_path: Path, print_detected_sections: bool = False) -> List[Document]:
    """
    Loads the official Task 3 handbook PDF and splits it into section documents with accurate
    section_number, section_title, page, and rich metadata.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"Source PDF file not found at: {pdf_path}")

    reader = pypdf.PdfReader(str(pdf_path))
    section_header_regex = re.compile(r"^\s*(\d+)\.\s+([A-Z][^\n\r]+)", re.MULTILINE)

    documents: List[Document] = []
    detected_sections_log = []

    current_section_num = 0
    current_section_title = "About This Document"
    file_name = pdf_path.name
    doc_title = "GDG-USAR Student Handbook"

    for page_idx, page in enumerate(reader.pages):
        page_num = page_idx + 1
        raw_text = page.extract_text() or ""
        normalized_text = normalize_merged_headings(raw_text)

        matches = list(section_header_regex.finditer(normalized_text))

        if not matches:
            cleaned_page = normalized_text.strip()
            if cleaned_page:
                sec_label = f"Section {current_section_num}: {current_section_title}"
                documents.append(
                    Document(
                        page_content=cleaned_page,
                        metadata={
                            "source": str(pdf_path),
                            "source_file": file_name,
                            "doc_title": doc_title,
                            "doc_type": "handbook",
                            "page": page_num,
                            "section": sec_label,
                            "section_number": current_section_num,
                            "section_title": current_section_title,
                        },
                    )
                )
        else:
            first_match = matches[0]
            if first_match.start() > 0:
                preamble_content = normalized_text[: first_match.start()].strip()
                if preamble_content:
                    sec_label = f"Section {current_section_num}: {current_section_title}"
                    documents.append(
                        Document(
                            page_content=preamble_content,
                            metadata={
                                "source": str(pdf_path),
                                "source_file": file_name,
                                "doc_title": doc_title,
                                "doc_type": "handbook",
                                "page": page_num,
                                "section": sec_label,
                                "section_number": current_section_num,
                                "section_title": current_section_title,
                            },
                        )
                    )
                    detected_sections_log.append(
                        (current_section_num, current_section_title, page_num)
                    )

            for i, match in enumerate(matches):
                sec_num = int(match.group(1))
                sec_title = match.group(2).strip()
                current_section_num = sec_num
                current_section_title = sec_title

                start_idx = match.end()
                end_idx = matches[i + 1].start() if i + 1 < len(matches) else len(normalized_text)

                body = normalized_text[start_idx:end_idx].strip()
                body = re.sub(r"End of sample document\s*$", "", body).strip()

                full_section_text = f"{sec_num}. {sec_title}\n{body}" if body else f"{sec_num}. {sec_title}"
                sec_label = f"Section {sec_num}: {sec_title}"

                documents.append(
                    Document(
                        page_content=full_section_text,
                        metadata={
                            "source": str(pdf_path),
                            "source_file": file_name,
                            "doc_title": doc_title,
                            "doc_type": "handbook",
                            "page": page_num,
                            "section": sec_label,
                            "section_number": sec_num,
                            "section_title": sec_title,
                        },
                    )
                )
                detected_sections_log.append((sec_num, sec_title, page_num))

    if print_detected_sections:
        print("\n" + "=" * 60)
        print("DETECTED SECTIONS (Official Handbook):")
        print("=" * 60)
        seen = set()
        for s_num, s_title, p_num in detected_sections_log:
            if s_num not in seen:
                print(f"  Section {s_num:2d}: {s_title} (Page {p_num})")
                seen.add(s_num)
        print("=" * 60 + "\n")

    return documents


def parse_generic_pdf(pdf_path: Path) -> List[Document]:
    """
    Parses any supplemental PDF document, extracting sections and pages.
    """
    reader = pypdf.PdfReader(str(pdf_path))
    file_name = pdf_path.name
    doc_title = file_name.replace(".pdf", "").replace("_", " ").title()

    documents: List[Document] = []
    section_regex = re.compile(r"^\s*(\d+)\.\s+([A-Z][^\n\r]+)", re.MULTILINE)

    for page_idx, page in enumerate(reader.pages):
        page_num = page_idx + 1
        raw_text = page.extract_text() or ""
        text_clean = normalize_merged_headings(raw_text)

        matches = list(section_regex.finditer(text_clean))
        if not matches:
            if text_clean.strip():
                documents.append(
                    Document(
                        page_content=text_clean.strip(),
                        metadata={
                            "source": str(pdf_path),
                            "source_file": file_name,
                            "doc_title": doc_title,
                            "doc_type": "extra",
                            "page": page_num,
                            "section": f"{doc_title} (p. {page_num})",
                            "section_number": 1,
                            "section_title": doc_title,
                        },
                    )
                )
        else:
            for i, match in enumerate(matches):
                sec_num = int(match.group(1))
                sec_title = match.group(2).strip()
                start_idx = match.start()
                end_idx = matches[i + 1].start() if i + 1 < len(matches) else len(text_clean)
                sec_content = text_clean[start_idx:end_idx].strip()
                sec_label = f"Section {sec_num}: {sec_title}"

                documents.append(
                    Document(
                        page_content=sec_content,
                        metadata={
                            "source": str(pdf_path),
                            "source_file": file_name,
                            "doc_title": doc_title,
                            "doc_type": "extra",
                            "page": page_num,
                            "section": sec_label,
                            "section_number": sec_num,
                            "section_title": sec_title,
                        },
                    )
                )

    return documents


def parse_markdown_or_text(file_path: Path) -> List[Document]:
    """
    Parses .md or .txt files, identifying section headers or numbered blocks.
    """
    file_name = file_path.name
    doc_title = file_path.stem.replace("_", " ").title()

    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = file_path.read_text(encoding="latin-1")

    documents: List[Document] = []
    
    # Check if markdown headers (## or #) or numbered headers (1. ...) exist
    if file_path.suffix.lower() == ".md":
        header_regex = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
        matches = list(header_regex.finditer(content))
        if matches:
            # Extract title from first H1 if present
            first_match = matches[0]
            if first_match.group(1) == "#":
                doc_title = first_match.group(2).strip()

            for i, match in enumerate(matches):
                level = len(match.group(1))
                sec_title = match.group(2).strip()
                start_idx = match.start()
                end_idx = matches[i + 1].start() if i + 1 < len(matches) else len(content)
                sec_body = content[start_idx:end_idx].strip()
                sec_num = i + 1
                sec_label = f"Section {sec_num}: {sec_title}"

                documents.append(
                    Document(
                        page_content=sec_body,
                        metadata={
                            "source": str(file_path),
                            "source_file": file_name,
                            "doc_title": doc_title,
                            "doc_type": "extra",
                            "page": 1,
                            "section": sec_label,
                            "section_number": sec_num,
                            "section_title": sec_title,
                        },
                    )
                )
            return documents

    # Handle plain text or fallback markdown: look for numbered sections "1. Header"
    text_section_regex = re.compile(r"^\s*(\d+)\.\s+([A-Z][^\n\r]+)", re.MULTILINE)
    matches = list(text_section_regex.finditer(content))

    if matches:
        first_line = content.splitlines()[0].strip()
        if first_line and not re.match(r"^\d+\.", first_line):
            doc_title = first_line

        for i, match in enumerate(matches):
            sec_num = int(match.group(1))
            sec_title = match.group(2).strip()
            start_idx = match.start()
            end_idx = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            sec_body = content[start_idx:end_idx].strip()
            sec_label = f"Section {sec_num}: {sec_title}"

            documents.append(
                Document(
                    page_content=sec_body,
                    metadata={
                        "source": str(file_path),
                        "source_file": file_name,
                        "doc_title": doc_title,
                        "doc_type": "extra",
                        "page": 1,
                        "section": sec_label,
                        "section_number": sec_num,
                        "section_title": sec_title,
                    },
                )
            )
    else:
        # Single document if no numbered headers
        documents.append(
            Document(
                page_content=content.strip(),
                metadata={
                    "source": str(file_path),
                    "source_file": file_name,
                    "doc_title": doc_title,
                    "doc_type": "extra",
                    "page": 1,
                    "section": f"{doc_title} (General)",
                    "section_number": 1,
                    "section_title": doc_title,
                },
            )
        )

    return documents


def load_all_documents(
    data_dir: Optional[Path] = None,
    print_detected_sections: bool = False
) -> List[Document]:
    """
    Loads every supported file (.pdf, .txt, .md) in the data directory.
    Tags each with source_file, doc_title, section, page, and doc_type ('handbook' or 'extra').
    """
    target_dir = Path(data_dir) if data_dir else DATA_DIR
    if not target_dir.exists():
        raise FileNotFoundError(f"Data directory does not exist: {target_dir}")

    all_docs: List[Document] = []
    supported_files = sorted(
        [p for p in target_dir.iterdir() if p.is_file() and p.suffix.lower() in [".pdf", ".txt", ".md"]],
        key=lambda p: (0 if "task3" in p.name.lower() or "handbook" in p.name.lower() else 1, p.name)
    )

    for file_path in supported_files:
        is_official_handbook = file_path.name == DEFAULT_PDF_PATH.name or "task3" in file_path.name.lower()
        if file_path.suffix.lower() == ".pdf":
            if is_official_handbook:
                docs = parse_handbook_pdf(file_path, print_detected_sections=print_detected_sections)
            else:
                docs = parse_generic_pdf(file_path)
        else:
            docs = parse_markdown_or_text(file_path)

        all_docs.extend(docs)

    return all_docs


def load_and_parse_handbook(
    pdf_path: Optional[Path] = None,
    print_detected_sections: bool = True
) -> List[Document]:
    """
    Backwards-compatible loader for the official Task 3 handbook PDF.
    """
    path = Path(pdf_path) if pdf_path else DEFAULT_PDF_PATH
    return parse_handbook_pdf(path, print_detected_sections=print_detected_sections)


if __name__ == "__main__":
    docs = load_all_documents(print_detected_sections=True)
    print(f"Total documents parsed across all data files: {len(docs)}")
    for d in docs:
        print(f"  [{d.metadata['doc_type'].upper():8s}] {d.metadata['source_file']} | {d.metadata.get('section')} | p.{d.metadata.get('page')}")

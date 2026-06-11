'''import re
from pathlib import Path
from urllib.parse import unquote
from PyPDF2 import PdfReader

# ==========================================
# PATHS
# ==========================================

PDF_ROOT = Path("Laws")
OUTPUT_ROOT = Path("laws_ext")

OUTPUT_ROOT.mkdir(
    parents=True,
    exist_ok=True
)

# ==========================================
# PDF EXTRACTION
# ==========================================

def extract_pdf(pdf_path):

    reader = PdfReader(str(pdf_path))

    pages = []

    for page in reader.pages:

        try:

            text = page.extract_text()

            if text:
                pages.append(text)

        except Exception as e:

            print(e)

    return "\n".join(pages)


# ==========================================
# BASIC CLEAN
# ==========================================

def clean_text(text):

    text = unquote(text)

    text = text.replace("\f", "\n")
    text = text.replace("\x00", "")

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text


# ==========================================
# REMOVE PAGE HEADERS
# ==========================================

def remove_headers(text):

    text = re.sub(
        r'^\s*\d+\s*:\s*.*?Act.*?$',
        '',
        text,
        flags=re.MULTILINE
    )

    text = re.sub(
        r'^\s*\[.*?Act.*?\]\s*$',
        '',
        text,
        flags=re.MULTILINE
    )

    return text


# ==========================================
# REMOVE AMENDMENT LIST
# ==========================================

def remove_amendment_section(text):

    start = re.search(
        r'LIST OF AMENDMENT ACTS',
        text,
        flags=re.IGNORECASE
    )

    if not start:
        return text

    act_start = re.search(
        r'BOMBAY ACT|MAHARASHTRA ACT|UTTAR PRADESH ACT|AN\s+ACT',
        text[start.end():],
        flags=re.IGNORECASE
    )

    if act_start:

        begin = start.start()

        end = start.end() + act_start.start()

        text = (
            text[:begin] +
            text[end:]
        )

    return text


# ==========================================
# REMOVE FOOTNOTES
# ==========================================

def remove_footnotes(text):

    lines = []

    for line in text.splitlines():

        line = line.strip()

        if re.match(
            r'^\d+\.\s*(Amended|Subs\.|Ins\.|Section)',
            line,
            flags=re.IGNORECASE
        ):
            continue

        if re.match(
            r'^Section\s+\d+',
            line,
            flags=re.IGNORECASE
        ):
            continue

        lines.append(line)

    return "\n".join(lines)


# ==========================================
# KEEP ONLY ACT CONTENT
# ==========================================

def keep_act_only(text):

    patterns = [

        r'1\.\s*Short title',

        r'Short title.*?1\.',

        r'AN\s+ACT',

        r'An Act'
    ]

    starts = []

    for p in patterns:

        m = re.search(
            p,
            text,
            flags=re.IGNORECASE | re.DOTALL
        )

        if m:
            starts.append(m.start())

    if starts:

        text = text[min(starts):]

    return text


# ==========================================
# FINAL CLEANUP
# ==========================================

def final_cleanup(text):

    text = re.sub(
        r'\n\s*\d+\s*\n',
        '\n',
        text
    )

    text = re.sub(
        r'\n{3,}',
        '\n\n',
        text
    )

    return text.strip()


# ==========================================
# PROCESS FILES
# ==========================================

for pdf_path in PDF_ROOT.rglob("*.pdf"):

    try:

        print(f"\nProcessing: {pdf_path}")

        text = extract_pdf(pdf_path)

        text = clean_text(text)

        text = remove_headers(text)

        text = remove_amendment_section(text)

        text = remove_footnotes(text)

        text = keep_act_only(text)

        text = final_cleanup(text)

        relative = pdf_path.relative_to(
            PDF_ROOT
        )

        txt_path = (
            OUTPUT_ROOT /
            relative.with_suffix(".txt")
        )

        txt_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            txt_path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(text)

        print(f"Saved: {txt_path}")

    except Exception as e:

        print(
            f"Error in {pdf_path.name}: {e}"
        )

print("\n================================")
print("Extraction Completed")
print("================================")'''





import re
from pathlib import Path
from urllib.parse import unquote
from PyPDF2 import PdfReader

# ==========================================
# PATHS
# ==========================================

PDF_ROOT = Path("Laws")
OUTPUT_ROOT = Path("laws_ext")

OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

# ==========================================
# PDF EXTRACTION
# ==========================================

def extract_pdf(pdf_path):
    reader = PdfReader(str(pdf_path))
    pages = []

    for page in reader.pages:
        try:
            text = page.extract_text()
            if text:
                pages.append(text)
        except Exception as e:
            print(f"Page error: {e}")

    return "\n".join(pages)


# ==========================================
# TEXT CLEANING (CORE FIXED VERSION)
# ==========================================

def clean_text(text):

    text = unquote(text)

    # Remove null bytes
    text = text.replace("\x00", " ")

    # Fix PDF line breaks
    text = re.sub(r'-\n', '', text)

    # Fix broken words
    text = re.sub(r'(?<=[a-zA-Z])\s(?=[a-zA-Z])', ' ', text)

    # Remove page headers
    text = re.sub(
        r'^\s*\d+\s*:\s*[A-Za-z.\s]+\]\s+.*$',
        '',
        text,
        flags=re.MULTILINE
    )

    text = re.sub(
        r'^\s*\[.*?Act.*?\]\s*$',
        '',
        text,
        flags=re.MULTILINE | re.IGNORECASE
    )

    text = re.sub(
        r'^\s*BOMBAY ACT.*$',
        '',
        text,
        flags=re.MULTILINE | re.IGNORECASE
    )

    text = re.sub(
        r'^\s*MAHARASHTRA ACT.*$',
        '',
        text,
        flags=re.MULTILINE | re.IGNORECASE
    )

    text = re.sub(
        r'^\s*ACT NO\..*$',
        '',
        text,
        flags=re.MULTILINE | re.IGNORECASE
    )

    # Remove footnote markers like:
    # 5[The Maharashtra...
    # 10[and where...
    text = re.sub(
        r'(\d+)\[',
        '[',
        text
    )

    # Remove amendment stars
    text = re.sub(
        r'\b\d+\*+\s*(\*+\s*)*',
        '',
        text
    )

    # Remove standalone page numbers
    text = re.sub(
        r'^\s*\d+\s*$',
        '',
        text,
        flags=re.MULTILINE
    )

    # Remove URLs
    text = re.sub(
        r'https?://\S+',
        ' ',
        text
    )

    # Normalize spaces
    text = re.sub(
        r'[ \t]+',
        ' ',
        text
    )

    # Normalize blank lines
    text = re.sub(
        r'\n{3,}',
        '\n\n',
        text
    )

    return text.strip()

# ==========================================
# REMOVE PAGE HEADERS / FOOTERS
# ==========================================

def remove_headers(text):

    text = re.sub(
        r'^\s*\d+\s*:\s*.*?Act.*?$',
        '',
        text,
        flags=re.MULTILINE
    )

    text = re.sub(
        r'^\s*\[.*?Act.*?\]\s*$',
        '',
        text,
        flags=re.MULTILINE | re.IGNORECASE
    )

    text = re.sub(
        r'^\s*\d+\s*:\s*[A-Za-z.\s]+\]\s+.*$',
        '',
        text,
        flags=re.MULTILINE
    )

    text = re.sub(
        r'^\s*BOMBAY ACT.*$',
        '',
        text,
        flags=re.MULTILINE | re.IGNORECASE
    )

    text = re.sub(
        r'^\s*MAHARASHTRA ACT.*$',
        '',
        text,
        flags=re.MULTILINE | re.IGNORECASE
    )

    text = re.sub(
        r'^\s*ACT NO\..*$',
        '',
        text,
        flags=re.MULTILINE | re.IGNORECASE
    )

    text = re.sub(
        r'^\s*\d+\s*$',
        '',
        text,
        flags=re.MULTILINE
    )

    return text

# ==========================================
# REMOVE AMENDMENT SECTION
# ==========================================

def remove_amendment_section(text):
    start = re.search(r'LIST OF AMENDMENT ACTS', text, flags=re.IGNORECASE)

    if not start:
        return text

    remaining = text[start.end():]

    act_start = re.search(
        r'(BOMBAY ACT|MAHARASHTRA ACT|UTTAR PRADESH ACT|AN\s+ACT)',
        remaining,
        flags=re.IGNORECASE
    )

    if act_start:
        text = text[:start.start()] + remaining[act_start.start():]

    return text


# ==========================================
# REMOVE FOOTNOTES / ANNOTATIONS
# ==========================================

def remove_footnotes(text):
    lines = []

    for line in text.splitlines():
        line = line.strip()

        line = re.sub(r'^\d+\s+', '', line)

       # line = re.sub(r'^\d+\.\s*', '', line)

        if re.search(r'(Amended by|Subs\.|Ins\.|w\.e\.f\.|Statement of Objects)', line, re.IGNORECASE):
            continue

        if re.search(
            r'(For Statement of Objects|Amended by|Subs\.|Ins\.|deleted by|w\.e\.f\.)',
            line,
            re.IGNORECASE
        ):
            continue

        if re.search(
            r'(Bombay Government Gazette|Maharashtra Adaptation of Laws)',
            line,
            re.IGNORECASE
        ):
            continue

        # Skip amendment notes
        if re.match(r'^\d+\.\s*(Amended|Subs\.|Ins\.|Section)', line, re.IGNORECASE):
            continue

        # Skip section-only noise
        if re.match(r'^Section\s+\d+', line, re.IGNORECASE):
            continue

        # Remove "* * *" style noise
        if re.match(r'^\*+\s*$', line):
            continue

        # Remove stray footnote markers like 1* 2*
        if re.match(r'^\d+\s*\*+', line):
            continue

        lines.append(line)

    return "\n".join(lines)


# ==========================================
# KEEP ONLY MAIN ACT CONTENT
# ==========================================

def keep_act_only(text):

    patterns = [

        r'THE\s+ADMINISTRATIVE\s+TRIBUNALS\s+ACT',

        r'AN\s+ACT',

        r'An\s+Act'
    ]

    starts = []

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:
            starts.append(match.start())

    if starts:
        return text[min(starts):]

    return text

# ==========================================
# FINAL CLEANUP
# ==========================================

def final_cleanup(text):
    # Remove isolated numbers
    text = re.sub(r'\n\s*\d+\s*\n', '\n', text)

    # Normalize spaces again
    text = re.sub(r'[ \t]+', ' ', text)

    # Normalize newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


# ==========================================
# PROCESS FILES
# ==========================================

for pdf_path in PDF_ROOT.rglob("*.pdf"):
    try:
        print(f"\nProcessing: {pdf_path}")

        text = extract_pdf(pdf_path)

        text = clean_text(text)
        text = remove_headers(text)
        text = remove_amendment_section(text)
        text = remove_footnotes(text)
        text = keep_act_only(text)
        text = final_cleanup(text)

        relative = pdf_path.relative_to(PDF_ROOT)

        txt_path = OUTPUT_ROOT / relative.with_suffix(".txt")
        txt_path.parent.mkdir(parents=True, exist_ok=True)

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"Saved: {txt_path}")

    except Exception as e:
        print(f"Error in {pdf_path.name}: {e}")


print("\n================================")
print("Extraction Completed (FIXED VERSION)")
print("================================")

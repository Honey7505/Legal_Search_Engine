'''from pathlib import Path
import json
import re

# ==========================================
# Paths
# ==========================================

input_dir = "laws_ext"
output_file = "law_chunks.json"

all_chunks = []
chunk_id = 0


# ==========================================
# Extract Offence Name
# ==========================================

def extract_offence(title):

    offence = re.split(
        r'—|––|–|-',
        title,
        maxsplit=1
    )[0]

    return offence.strip(" .-")


# ==========================================
# Extract Penalty
# ==========================================

def extract_penalty(text):

    text = re.sub(
        r'\s+',
        ' ',
        text
    )

    matches = re.findall(
        r'shall be punished with\s+(.*?)(?:\.|;)',
        text,
        flags=re.IGNORECASE
    )

    if not matches:
        return "Not Found"

    penalties = []

    for p in matches:

        p = re.sub(
            r'imprisonment of either description for a term which may extend to',
            'Up to',
            p,
            flags=re.IGNORECASE
        )

        p = re.sub(
            r'imprisonment for a term which may extend to',
            'Up to',
            p,
            flags=re.IGNORECASE
        )

        p = re.sub(
            r'imprisonment which may extend to',
            'Up to',
            p,
            flags=re.IGNORECASE
        )

        p = p.replace(
            'and shall also be liable to fine',
            '+ Fine'
        )

        penalties.append(
            p.strip()
        )

    return " | ".join(penalties)


# ==========================================
# Process Files
# ==========================================

for file in Path(input_dir).rglob("*.txt"):

    print(
        f"\nProcessing: {file.name}"
    )

    text = file.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    act_name = (
        file.stem
        .replace("_", " ")
        .strip()
    )

    # --------------------------------------
    # Find Sections
    # --------------------------------------

    matches = list(
        re.finditer(
            r'^\s*(\d+[A-Z]?)\.\s+',
            text,
            flags=re.MULTILINE
        )
    )

    print(
        f"Found {len(matches)} sections"
    )

    # --------------------------------------
    # Split Sections
    # --------------------------------------

    for i in range(len(matches)):

        start = matches[i].start()

        if i < len(matches) - 1:
            end = matches[i + 1].start()
        else:
            end = len(text)

        section_text = text[
            start:end
        ].strip()

        if len(section_text) < 100:
            continue

        section_no = matches[i].group(1)

        # ----------------------------------
        # First Line
        # ----------------------------------

        first_line = (
            section_text
            .split("\n")[0]
            .strip()
        )

        title_match = re.match(
            r'\d+[A-Z]?\.\s*(.*)',
            first_line
        )

        if title_match:
            title = (
                title_match
                .group(1)
                .strip()
            )
        else:
            title = "Unknown"

        # ----------------------------------
        # Extract Offence
        # ----------------------------------

        offence = extract_offence(
            title
        )

        # ----------------------------------
        # Extract Penalty
        # ----------------------------------

        penalty = extract_penalty(
            section_text
        )

        # ----------------------------------
        # Search Text
        # ----------------------------------

        search_text = (
            f"{act_name} "
            f"Section {section_no} "
            f"{offence} "
            f"{penalty} "
            f"{section_text}"
        )

        # ----------------------------------
        # Save Chunk
        # ----------------------------------

        all_chunks.append({

            "chunk_id":
                chunk_id,

            "act_name":
                act_name,

            "section":
                section_no,

            "title":
                title,

            "offence":
                offence,

            "penalty":
                penalty,

            "chunk_text":
                section_text,

            "search_text":
                search_text

        })

        chunk_id += 1


# ==========================================
# Save JSON
# ==========================================

with open(
    output_file,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        all_chunks,
        f,
        ensure_ascii=False,
        indent=2
    )

print(
    f"\nTotal Sections: {len(all_chunks)}"
)

print(
    f"Saved to {output_file}"
)'''




'''from pathlib import Path
import json
import re

# =========================
# CONFIG
# =========================

INPUT_DIR = Path("laws_ext")
OUTPUT_FILE = "law_chunks.json"

all_chunks = []
chunk_id = 0


# =========================
# FRONT MATTER REMOVAL
# =========================

def remove_front_matter(text):
    keywords = [
        "ARRANGEMENT OF SECTIONS",
        "TABLE OF CONTENTS",
        "CONTENTS",
        "LIST OF AMENDMENT ACTS"
    ]

    upper_text = text.upper()

    for keyword in keywords:
        pos = upper_text.find(keyword)
        if pos != -1:
            text = text[pos:]

            matches = list(re.finditer(
                 r'^\s*\d+[A-Z]?\.\s+[A-Za-z\(]',
                text,
                flags=re.MULTILINE
            ))

            if len(matches) >= 2:
                text = text[matches[1].start():]

            break

    return text


# =========================
# CLEAN TITLE (IMPORTANT FIX)
# =========================

def clean_title(title):
    title = re.sub(r'\s+', ' ', title)
    title = re.sub(r'—.*', '', title)   # remove dash parts
    title = re.sub(r'\(.*?\)', '', title)  # remove brackets
    title = re.sub(r'\d+', '', title)   # remove stray numbers
    title = title.strip(" .:-")

    # normalize spacing
    title = " ".join(title.split())

    # cap length (VERY IMPORTANT)
    if len(title) > 80:
        title = title[:80].rsplit(" ", 1)[0]

    return title.strip().title()


# =========================
# OFFENCE EXTRACTION
# =========================

def extract_offence(title):
    title = title.lower()

    if "tax" in title:
        return "Tax Provision"
    if "definitions" in title:
        return "Statutory Definitions"
    if "penalty" in title:
        return "Penalty Provision"
    if "appeal" in title:
        return "Appeal Provision"
    if "return" in title:
        return "Compliance Requirement"

    return "General Provision"


# =========================
# PENALTY EXTRACTION
# =========================

def extract_penalty(text):
    text = re.sub(r'\s+', ' ', text)

    matches = re.findall(
        r'shall be punished with\s+(.*?)(?:\.|;)',
        text,
        flags=re.IGNORECASE
    )

    if not matches:
        return "Not Found"

    cleaned = []

    for p in matches:
        p = re.sub(r'imprisonment.*?to', 'Up to', p, flags=re.IGNORECASE)
        p = re.sub(r'and shall also be liable to fine', '+ Fine', p, flags=re.IGNORECASE)
        cleaned.append(p.strip())

    return " | ".join(cleaned)


# =========================
# LAW METADATA
# =========================

def get_law_metadata(file_path):
    parts = [p.lower() for p in file_path.parts]

    law_type = "Unknown"
    jurisdiction = "India"

    if "central_laws" in parts:
        law_type = "Central Law"
    elif "states" in parts:
        law_type = "State Law"
        try:
            idx = parts.index("states")
            jurisdiction = file_path.parts[idx + 1]
        except:
            pass

    return law_type, jurisdiction


# =========================
# VALID SECTION FILTER
# =========================

def is_valid_section(title, text):
    if len(text) < 80:
        return False

    bad = [
        "table of contents",
        "list of amendment acts",
        "index",
        "preface",
        "short title",
        "extent",
        "commencement"
    ]

    t = title.lower()
    return not any(b in t for b in bad)


# =========================
# CLEAN TEXT
# =========================

def clean_section_text(text):
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(
        r'\b\d+\s+(?=For Statement|These words|Clause|Sub-section)',
        '',
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r'For Statement of Objects.*?(?=Section|\Z)',
        '',
        text,
        flags=re.IGNORECASE | re.DOTALL
    )
    return text.strip()


# =========================
# CHAPTER EXTRACTION
# =========================

def extract_chapters(text):

    chapter_pattern = re.compile(
        r'CHAPTER\s+([IVXLC\d]+)\s*\n+([A-Z][A-Z\s,&\-]+)',
        re.IGNORECASE
    )

    chapters = []

    for m in chapter_pattern.finditer(text):

        chapters.append({
            "start": m.start(),
            "chapter_no": m.group(1).strip(),
            "chapter_title": m.group(2).strip().title()
        })

    return chapters

# =========================
# SECTION SPLIT PATTERN FIX
# =========================

SECTION_PATTERN = re.compile(
    r'^\s*(\d+[A-Z]?)\.\s+[A-Za-z\(]',
    re.MULTILINE
)


# =========================
# PROCESS FILES
# =========================

for file in INPUT_DIR.rglob("*.txt"):
    print(f"\nProcessing: {file}")

    try:
        text = file.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print(e)
        continue

    text = remove_front_matter(text)

    # act_name = file.stem.replace("_", " ").strip().title()

    act_name = re.sub(r'_\d{4}$', '', file.stem, flags = re.IGNORECASE)
    act_name = act_name.replace("_", " ").title

    law_type, jurisdiction = get_law_metadata(file)

    matches = list(SECTION_PATTERN.finditer(text))

    print(f"Found {len(matches)} sections")

    for i in range(len(matches)):
        start = matches[i].start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        section_text = clean_section_text(text[start:end])

        section_no = matches[i].group(1)

        # first_line = section_text.split(".")[0]
        title_match = re.match(r'^\s*\d+[A-Z]?\.\s*(.+?)(?:—|-|\.|\n)', section_text)

        if title_match:
            title = clean_title(title_match.group(1))

        else:
            title = ""

        if not title:
            title = f"Section {section_no}"

        if not is_valid_section(title, section_text):
            continue

        offence = extract_offence(title)
        penalty = extract_penalty(section_text)

        search_text = f"""
Act: {act_name}
Law Type: {law_type}
Jurisdiction: {jurisdiction}
Section: {section_no}
Title: {title}
Offence: {offence}
Penalty: {penalty}
Content: {section_text[:1200]}
""".strip()

        all_chunks.append({
            "chunk_id": chunk_id,
            "act_name": act_name,
            "law_type": law_type,
            "jurisdiction": jurisdiction,
            "section": section_no,
            "title": title,
            "offence": offence,
            "penalty": penalty,
            "chunk_text": section_text,
            "search_text": search_text
        })

        chunk_id += 1


# =========================
# SAVE
# =========================

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(all_chunks, f, ensure_ascii=False, indent=2)

print("\n================================")
print(f"Total Sections: {len(all_chunks)}")
print(f"Saved to {OUTPUT_FILE}")
print("================================")'''




from pathlib import Path
import json
import re

# =========================
# CONFIG
# =========================

INPUT_DIR = Path("laws_ext")
OUTPUT_FILE = "law_chunks.json"

all_chunks = []
unique_sections = set()
chunk_id = 0
curr_chap = ""
curr_chap_name = ""

# =========================
# FRONT MATTER REMOVAL
# =========================

def remove_front_matter(text):

    keywords = [
        "ARRANGEMENT OF SECTIONS",
        "TABLE OF CONTENTS",
        "CONTENTS",
        "LIST OF AMENDMENT ACTS"
    ]

    upper = text.upper()

    for keyword in keywords:

        pos = upper.find(keyword)

        if pos != -1:

            text = text[pos:]

            matches = list(
                re.finditer(
                    r'^\s*\d+[A-Z]?\.\s+',
                    text,
                    flags=re.MULTILINE
                )
            )

            if len(matches) >= 2:
                text = text[matches[1].start():]

            break

    return text


# =========================
# CLEAN TITLE
# =========================

def clean_title(title):

    title = re.sub(r'\s+', ' ', title)

    title = re.sub(r'—.*', '', title)

    title = re.sub(r'\(.*?\)', '', title)

    title = re.sub(r'\[\d+\]', '', title)

    title = title.strip(" .:-")

    title = re.sub(r'\d+\[', '', title)
    title = re.sub(r'\]', '', title)
    title = re.sub(r'\[', '', title)

    return title.strip()


# =========================
# CHAPTER EXTRACTION
# =========================

def extract_chapters(text):

    chapters = []

    pattern = re.finditer(
        r'CHAPTER\s+([IVXLC]+)\s*\n(.*)',
        text,
        flags=re.IGNORECASE
    )

    for match in pattern:

        chapters.append(
            (
                match.start(),
                f"CHAPTER {match.group(1)}",
                match.group(2).strip()
            )
        )

    return chapters


# =========================
# FIND CURRENT CHAPTER
# =========================

def get_current_chapter(position, chapters):

    current_chapter = ""

    current_heading = ""

    for pos, chap, heading in chapters:

        if pos <= position:
            current_chapter = chap
            current_heading = heading
        else:
            break

    return current_chapter, current_heading


# =========================
# OFFENCE TYPE
# =========================

def extract_offence(title):

    t = title.lower()

    # Property Crimes
    if "identity theft" in t:
        return "Identity Theft"

    elif "theft" in t:
        return "Theft"

    elif "robbery" in t:
        return "Robbery"

    elif "extortion" in t:
        return "Extortion"

    elif "criminal breach of trust" in t:
        return "Criminal Breach of Trust"

    elif "misappropriation" in t:
        return "Criminal Misappropriation"

    elif "receiving stolen property" in t:
        return "Receiving Stolen Property"

    # Fraud Crimes
    elif "cheating" in t:
        return "Cheating"

    elif "fraud" in t:
        return "Fraud"

    elif "forgery" in t:
        return "Forgery"

    elif "counterfeit" in t:
        return "Counterfeiting"

    elif "falsification" in t:
        return "Document Falsification"

    # Cyber Crimes
    elif "computer" in t:
        return "Cyber Crime"

    elif "electronic" in t:
        return "Cyber Crime"

    elif "hacking" in t:
        return "Hacking"

    elif "unauthorised access" in t:
        return "Unauthorized Access"

    elif "data theft" in t:
        return "Data Theft"

    # Crimes Against Human Body
    elif "murder" in t:
        return "Murder"

    elif "culpable homicide" in t:
        return "Culpable Homicide"

    elif "death by negligence" in t:
        return "Death by Negligence"

    elif "hurt" in t:
        return "Causing Hurt"

    elif "grievous hurt" in t:
        return "Grievous Hurt"

    elif "assault" in t:
        return "Assault"

    elif "criminal force" in t:
        return "Criminal Force"

    elif "wrongful restraint" in t:
        return "Wrongful Restraint"

    elif "wrongful confinement" in t:
        return "Wrongful Confinement"

    # Kidnapping / Trafficking
    elif "kidnapping" in t:
        return "Kidnapping"

    elif "abduction" in t:
        return "Abduction"

    elif "human trafficking" in t:
        return "Human Trafficking"

    elif "trafficking" in t:
        return "Trafficking"

    # Sexual Offences
    elif "rape" in t:
        return "Rape"

    elif "sexual harassment" in t:
        return "Sexual Harassment"

    elif "outraging modesty" in t:
        return "Outraging Modesty"

    elif "voyeurism" in t:
        return "Voyeurism"

    elif "stalking" in t:
        return "Stalking"

    elif "obscenity" in t:
        return "Obscenity"

    # Public Order
    elif "riot" in t:
        return "Rioting"

    elif "unlawful assembly" in t:
        return "Unlawful Assembly"

    elif "affray" in t:
        return "Affray"

    elif "public nuisance" in t:
        return "Public Nuisance"

    # Government / State
    elif "sedition" in t:
        return "Sedition"

    elif "terrorism" in t:
        return "Terrorism"

    elif "waging war" in t:
        return "Waging War Against State"

    elif "treason" in t:
        return "Treason"

    # Corruption
    elif "bribe" in t:
        return "Bribery"

    elif "corruption" in t:
        return "Corruption"

    elif "public servant" in t:
        return "Public Servant Misconduct"

    # Drugs
    elif "narcotic" in t:
        return "Narcotics Offence"

    elif "psychotropic" in t:
        return "Drug Offence"

    # Motor Vehicle
    elif "drunken driving" in t:
        return "Drunken Driving"

    elif "dangerous driving" in t:
        return "Dangerous Driving"

    elif "driving licence" in t:
        return "Driving Licence Violation"

    elif "motor vehicle" in t:
        return "Motor Vehicle Violation"

    # Tax / Finance
    elif "tax evasion" in t:
        return "Tax Evasion"

    elif "gst" in t:
        return "GST Violation"

    elif "income tax" in t:
        return "Income Tax Violation"

    # Regulatory
    elif "penalty" in t:
        return "Penalty Provision"

    elif "appeal" in t:
        return "Appeal Provision"

    elif "licence" in t:
        return "Licensing Requirement"

    elif "registration" in t:
        return "Registration Requirement"

    elif "return" in t:
        return "Compliance Requirement"

    elif "inspection" in t:
        return "Inspection Provision"

    elif "search and seizure" in t:
        return "Search and Seizure"

    # Definitions
    elif "definition" in t:
        return "Statutory Definitions"

    elif "interpretation" in t:
        return "Interpretation Clause"

    elif "short title" in t:
        return "General Provision"

    elif "commencement" in t:
        return "General Provision"

    # Default
    return "General Provision"

# =========================
# PENALTY EXTRACTION
# =========================

def extract_penalty(text):

    text = re.sub(r'\s+', ' ', text)

    matches = re.findall(
        r'shall be punished with\s+(.*?)(?:\.|;|\n)',
        text,
        flags=re.IGNORECASE
    )

    if not matches:
        return "Not Found"

    return " | ".join(matches[:3])


# =========================
# LAW METADATA
# =========================

'''def get_law_metadata(file_path):

    parts = [p.lower() for p in file_path.parts]

    law_type = "Unknown"
    jurisdiction = "India"

    if "central_laws" in parts:

        law_type = "Central Law"

    elif "states" in parts:

        law_type = "State Law"

        try:

            idx = parts.index("states")

            jurisdiction = file_path.parts[idx + 1]

            jurisdiction = (
                jurisdiction
                .replace("_Laws", "")
                .replace("_", " ")
            )

        except:
            pass

    return law_type, jurisdiction'''

def get_law_metadata(file_path):

    parts = [p.lower() for p in file_path.parts]

    law_type = "Unknown"
    jurisdiction = "India"

    # Central Laws
    if "central_laws" in parts:

        law_type = "Central Law"

    # State Laws
    elif "states" in parts:

        law_type = "State Law"

        try:
            idx = parts.index("states")

            jurisdiction = (
                file_path.parts[idx + 1]
                .replace("_Laws", "")
                .replace("_", " ")
            )

        except:
            pass

    # Union Territories
    elif "union_territories" in parts:

        law_type = "Union Territory Law"

        try:
            idx = parts.index("union_territories")

            jurisdiction = (
                file_path.parts[idx + 1]
                .replace("_Laws", "")
                .replace("_", " ")
            )

        except:
            pass

    return law_type, jurisdiction

# =========================
# CLEAN SECTION TEXT
# =========================

def clean_section_text(text):

    # remove footnote markers

    text = re.sub(r'\[\d+\]', '', text)

    text = re.sub(r'\b\d+\*\s*', '', text)

    text = re.sub(r'\*+', '', text)

    # remove amendment notes

    text = re.sub(
        r'For Statement of Objects.*',
        '',
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r'These words were substituted.*',
        '',
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r'Clause.*?deleted.*',
        '',
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(r'\s+', ' ', text)
    text = text.replace("Submiss ion", "Submission")
    text = text.replace("Commiss ioner", "Commissioner")
    text = text.replace("Administrat ive", "Administrative")
    text = text.replace("id entity", "identity")
    text = text.replace("bel ieve", "believe")
    text = text.replace("l iable", "liable")
    text = text.replace("ex tend", "extend")
    text = text.replace("ceas es", "ceases")

    return text.strip()


# =========================
# VALID SECTION
# =========================

def is_valid_section(title, text):

    if len(text) < 100:
        return False

    bad_titles = [
    "contents",
    "table of contents",
    "list of amendment acts",
    "index",
    "sub",
    "sub-section",
    "sub rule",
    "sub-rule"
    ]

    title = title.lower()

    return not any(x in title for x in bad_titles)


# =========================
# SECTION SPLIT
# =========================

SECTION_PATTERN = re.compile(
    r'^\s*(\d+[A-Z]?)\.\s+',
    flags=re.MULTILINE
)

CHAPTER_PATTERN = re.compile(
    r'CHAPTER\s+([IVXLC\d]+)\s*\n\s*(.+)',
    re.IGNORECASE
)

# =========================
# PROCESS FILES
# =========================

for file in INPUT_DIR.rglob("*.txt"):

    print(f"\nProcessing: {file}")

    try:

        text = file.read_text(
            encoding="utf-8",
            errors="ignore"
        )

    except Exception as e:

        print(e)
        continue

    text = remove_front_matter(text)

    chapters = extract_chapters(text)

    act_name = file.stem.replace("_", " ").strip().title()
    
    pdf_path = str(file).replace("laws_ext", "Laws").replace(".txt", ".pdf")

    law_type, jurisdiction = get_law_metadata(file)

    chap_matches = list(CHAPTER_PATTERN.finditer(text))    

    matches = list(
        SECTION_PATTERN.finditer(text)
    )

    print(f"Found {len(matches)} sections")

    for i in range(len(matches)):

        section_pos = matches[i].start()

        for chapter_match in chap_matches:
            if chapter_match.start() < section_pos:
                current_chapter = chapter_match.group(1)
                current_chapter_name = chapter_match.group(2).strip()
            else:
                break

        start = matches[i].start()

        end = (
            matches[i + 1].start()
            if i + 1 < len(matches)
            else len(text)
        )

        section_text = clean_section_text(
            text[start:end]
        )

        section_no = matches[i].group(1)

        title = ""

        first_part = section_text[:500]

        title_match = re.search(
            r'^\s*\d+[A-Z]?\.\s*(.+?)(?:\.\s*[–—-]|[–—-])',
            first_part,
            flags=re.DOTALL
        )

        if title_match:
            title = clean_title(
                title_match.group(1)
             )

        # Fallback extraction
        if not title:
            fallback = re.search(
                r'^\s*\d+[A-Z]?\.\s*([^\n]{3,200})',
                first_part
            )

            if fallback:
                title = clean_title(
                    fallback.group(1)
                )

        chapter_no, chapter_name = get_current_chapter(
            start,
            chapters
        )

        if not is_valid_section(
            title,
            section_text
        ):
            continue

        offence = extract_offence(
            title + " " + title + " "+ section_text[:1000]
        )

        penalty = extract_penalty(
            section_text
        )

        chapter_no, chapter_name = get_current_chapter(
            start,
            chapters
        )

        if not chapter_no:
            chapter_no = "CHAPTER I"

        if not chapter_name:
            chapter_name = "GENERAL PROVISIONS"
            search_text = f"""
Act: {act_name}
Law Type: {law_type}
Jurisdiction: {jurisdiction}
Chapter: {chapter_no}
Chapter Name: {chapter_name}
Section: {section_no}
Title: {title}
Offence: {offence}
Penalty: {penalty}
Content: {section_text[:1500]}
""".strip()

        normalized_title = re.sub(
            r'[^a-z0-9 ]',
            '',
            title.lower()
        )
        
        unique_key = (
            act_name.lower().strip(),
            section_no.strip(),
            title.lower().strip()
        )

        if unique_key in unique_sections:
            continue

        unique_sections.add(unique_key)
        all_chunks.append({
            "chunk_id": chunk_id,
            "act_name": act_name,
            "law_type": law_type,
            "jurisdiction": jurisdiction,
            "chapter": chapter_no,
            "chapter_name": chapter_name,
            "section": section_no,
            "title": title,
            "offence": offence,
            "penalty": penalty,
            "pdf_path": pdf_path,
            "chunk_text": section_text,
            "search_text": search_text
        })

        chunk_id += 1

# =========================
# SAVE
# =========================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        all_chunks,
        f,
        ensure_ascii=False,
        indent=2
    )

print("\n================================")
print(f"Total Sections: {len(all_chunks)}")
print(f"Saved to {OUTPUT_FILE}")
print("================================")


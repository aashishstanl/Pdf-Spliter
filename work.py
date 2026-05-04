import argparse
import sys
import time
import os
import re
import zipfile
from datetime import datetime
from pathlib import Path

import pytesseract
from pdf2image import convert_from_path
from PIL import ImageFilter, ImageOps
from PyPDF2 import PdfReader, PdfWriter

try:
    import config
except ImportError:
    config = None


# ============================================================================
# CONFIGURATION
# ============================================================================

OUTPUT_BASE_DIR = getattr(config, "OUTPUT_BASE_DIR", "pdf_splits")
DPI = getattr(config, "DPI", 300)
DEBUG = getattr(config, "DEBUG", True)
MAX_PDF_SIZE_MB = getattr(config, "MAX_PDF_SIZE_MB", 5)
TESSERACT_PATH = getattr(config, "TESSERACT_PATH", None)
POPPLER_PATH = getattr(config, "POPPLER_PATH", None)
USE_FIFTH_LINE_FALLBACK = getattr(config, "USE_FIFTH_LINE_FALLBACK", False)
OCR_ROTATIONS = getattr(config, "OCR_ROTATIONS", (0, 90, 180, 270))
BEING_STAMP_LINE = getattr(config, "BEING_STAMP_LINE", 5)
START_NO_REGION = getattr(config, "START_NO_REGION", (0.0, 0.0, 0.30, 1.0))
BEING_STAMP_REGION = getattr(config, "BEING_STAMP_REGION", (0.0, 0.0, 0.40, 1.0))
OCR_SCALE = getattr(config, "OCR_SCALE", 3)
OCR_PSM_MODES = getattr(config, "OCR_PSM_MODES", (6, 11, 13))
OCR_PREPROCESS_VARIANTS = getattr(config, "OCR_PREPROCESS_VARIANTS", ("contrast",))
AUTO_ACCEPT_SECONDS = getattr(config, "AUTO_ACCEPT_SECONDS", 0.8)
EDIT_COMMAND = "__EDIT__"

if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# Regex patterns for detection
NO_LINE_PATTERN = re.compile(r"\bN\s*[o0]\.?\s*[:#-]?\s*(\d{1,5})\b", re.IGNORECASE)
BEING_PATTERN = re.compile(r"\bBeing\s+No\.?\s*[:#-]?\s*(\d+)\b", re.IGNORECASE)
BLUE_STAMP_PATTERN = re.compile(r"\b(\d+)\b")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def log(message):
    """Debug logging."""
    if DEBUG:
        print(f"[LOG] {message}")


def normalize_pdf_path(pdf_path):
    """Normalize common file URL input into a filesystem path."""
    pdf_path = str(pdf_path).strip().strip('"')
    if pdf_path.startswith("file:///"):
        pdf_path = pdf_path.replace("file:///", "", 1)
    return os.path.normpath(pdf_path)


def tesseract_config(psm):
    """Build a Tesseract config for marker OCR."""
    return f"--oem 3 --psm {psm}"


def extract_text_from_image(img, psm):
    """Extract text from image using OCR."""
    return pytesseract.image_to_string(img, config=tesseract_config(psm))


def preprocess_marker_crop(img):
    """Create OCR-friendly versions of a small marker crop."""
    grayscale = ImageOps.grayscale(img)
    if OCR_SCALE > 1:
        grayscale = grayscale.resize(
            (grayscale.width * OCR_SCALE, grayscale.height * OCR_SCALE),
        )

    variants = {
        "gray": grayscale,
        "contrast": ImageOps.autocontrast(grayscale),
    }
    variants["sharp"] = variants["contrast"].filter(ImageFilter.SHARPEN)
    variants["threshold"] = variants["sharp"].point(lambda pixel: 255 if pixel > 165 else 0)

    return tuple(
        (name, variants[name])
        for name in OCR_PREPROCESS_VARIANTS
        if name in variants
    )


def crop_relative(img, region):
    """Crop an image using relative left, top, right, bottom coordinates."""
    width, height = img.size
    left, top, right, bottom = region
    return img.crop((
        int(width * left),
        int(height * top),
        int(width * right),
        int(height * bottom),
    ))


def extract_text_variants(img, region, label):
    """Extract OCR text from a cropped marker region across rotations."""
    crop = crop_relative(img, region)
    variants = []
    seen_angles = set()

    for angle in OCR_ROTATIONS:
        if angle in seen_angles:
            continue
        seen_angles.add(angle)

        rotated = crop if angle == 0 else crop.rotate(-angle, expand=True)
        for preprocess_name, prepared in preprocess_marker_crop(rotated):
            for psm in OCR_PSM_MODES:
                try:
                    text = extract_text_from_image(prepared, psm)
                except Exception as e:
                    log(f"Warning: OCR failed for {label} at {angle} degrees/{preprocess_name}/psm {psm}: {e}")
                    continue
                variants.append((angle, preprocess_name, psm, text))

    return variants


def detect_page_markers(img, allow_fallback):
    """Detect markers only from configured left-side crops, never the table/body."""
    no_marker = None
    being_marker = None
    fallback_marker = None

    start_variants = extract_text_variants(img, START_NO_REGION, "left handwritten No. region")
    for angle, preprocess_name, psm, text in start_variants:
        log(f"Left handwritten No. OCR at {angle} degrees/{preprocess_name}/psm {psm} (first 200 chars): {text[:200]}")

        if no_marker is None:
            no_marker = find_no_marker(text)
            if no_marker:
                log(f"Found No.{no_marker} in left handwritten region at {angle} degrees/{preprocess_name}/psm {psm}")

        if allow_fallback and fallback_marker is None:
            fallback_marker = extract_fifth_line_number(text)
            if fallback_marker:
                log(f"Fallback start number extracted from left region 5th line at {angle} degrees/{preprocess_name}/psm {psm}: {fallback_marker}")

        if no_marker:
            break

    being_variants = extract_text_variants(img, BEING_STAMP_REGION, "left Being No. stamp region")
    for angle, preprocess_name, psm, text in being_variants:
        log(f"Left stamp OCR at {angle} degrees/{preprocess_name}/psm {psm} (first 200 chars): {text[:200]}")

        being_marker = find_being_marker(text)
        if being_marker:
            log(f"Found Being No.{being_marker} in left stamp region at {angle} degrees/{preprocess_name}/psm {psm}")
            break

    return no_marker, being_marker, fallback_marker


def find_no_marker(text):
    """Find a left-side handwritten 'No. X' marker without matching 'Being No. X'."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        if "being" in line.lower():
            continue
        match = NO_LINE_PATTERN.search(line)
        if match:
            return match.group(1)
    return None


def find_being_marker(text):
    """Find the ending Being No. marker, using the stamp's configured line."""
    match = BEING_PATTERN.search(text)
    if match:
        return match.group(1)
    return extract_line_number(text, BEING_STAMP_LINE)


def extract_line_number(text, line_number):
    """Extract the first number from a 1-based OCR line number."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    line_index = line_number - 1
    if len(lines) > line_index:
        match = BLUE_STAMP_PATTERN.search(lines[line_index])
        if match:
            return match.group(1)
    return None


def extract_fifth_line_number(text):
    """Extract a fallback start number from the fifth OCR line."""
    return extract_line_number(text, 5)


def correct_image_rotation(img):
    """Correct image orientation for OCR detection when Tesseract can infer it."""
    try:
        osd = pytesseract.image_to_osd(img, output_type=pytesseract.Output.DICT)
        angle = int(osd.get("rotate", 0))
        if angle:
            log(f"Rotating OCR image by {angle} degrees for detection")
            return img.rotate(-angle, expand=True)
    except Exception as e:
        log(f"Warning: Could not correct rotation: {e}")
    return img


def extract_pages_to_pdf(reader, start_page, end_page, output_path, rotation_degrees=0):
    """Extract pages from PDF and save to a new file."""
    writer = PdfWriter()
    for i in range(start_page, end_page + 1):
        page = reader.pages[i]
        if rotation_degrees:
            page = page.rotate(rotation_degrees)
        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)

    log(f"Created PDF: {output_path}")


def validate_group(group_name, start_page, end_page, total_pages):
    """Validate one group before writing it."""
    if group_name is None:
        raise ValueError("Group has no file number")
    if start_page is None or end_page is None:
        raise ValueError(f"Invalid group {group_name}: missing page range")
    if start_page < 0 or end_page < start_page:
        raise ValueError(f"Invalid group {group_name}: start={start_page}, end={end_page}")
    if end_page >= total_pages:
        raise ValueError(f"Invalid group {group_name}: end={end_page}, total_pages={total_pages}")
    return True


# ============================================================================
# MAIN PROCESSING LOGIC
# ============================================================================

def analyze_pdf(pdf_path):
    """
    Analyze PDF and detect groups according to rules:

    1. Start: top-of-page "No. X" marker
    2. End: matching "Being No. X" marker
    3. End: only a matching "Being No. X" ends the active group
    4. Optional fallback: use the fifth OCR line number only when no group is active

    Returns: (groups, reader, total_pages)
    """
    pdf_path = normalize_pdf_path(pdf_path)
    log(f"Converting PDF to images: {pdf_path}")
    images = convert_from_path(pdf_path, dpi=DPI, poppler_path=POPPLER_PATH)
    reader = PdfReader(pdf_path)

    groups = []
    current_no = None
    start_page = None

    for page_idx, img in enumerate(images):
        log(f"\n--- Page {page_idx + 1} ---")

        no_marker, being_marker, fallback_marker = detect_page_markers(
            img,
            allow_fallback=USE_FIFTH_LINE_FALLBACK and current_no is None,
        )
        start_marker = no_marker or fallback_marker

        log(f"No marker: {no_marker}, Being marker: {being_marker}, Start marker: {start_marker}")

        if start_marker:
            if current_no is None:
                current_no = start_marker
                start_page = page_idx
                log(f"START: File No.{current_no} at page {page_idx + 1}")
            elif current_no != start_marker:
                log(f"Ignoring No.{start_marker}; waiting for matching Being No.{current_no}")

        if being_marker:
            if current_no == being_marker:
                log(f"END: Being No.{being_marker} found at page {page_idx + 1}")
                groups.append((current_no, start_page, page_idx))
                current_no = None
                start_page = None
            elif current_no is None:
                log(f"WARNING: Being No.{being_marker} without matching start")
            else:
                log(f"WARNING: Being No.{being_marker} does not match active No.{current_no}")

    if current_no is not None:
        log(f"WARNING: Incomplete group No.{current_no}; closing at final page")
        groups.append((current_no, start_page, len(images) - 1))

    return groups, reader, len(images)


def create_output_session_dir():
    """Create a timestamped output session directory."""
    output_dir = Path(OUTPUT_BASE_DIR)
    output_dir.mkdir(exist_ok=True)

    session_dir = output_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    session_dir.mkdir(exist_ok=True)
    return session_dir


def create_output_pdf(file_no, start_page, end_page, reader, total_pages, session_dir, rotation_degrees=0):
    """Create one PDF file for a validated page group."""
    validate_group(file_no, start_page, end_page, total_pages)

    pdf_filename = f"{file_no}.pdf"
    output_path = session_dir / pdf_filename
    extract_pages_to_pdf(reader, start_page, end_page, str(output_path), rotation_degrees)

    file_size = os.path.getsize(output_path) / (1024 * 1024)
    if file_size > MAX_PDF_SIZE_MB:
        log(f"WARNING: {pdf_filename} is {file_size:.2f}MB (limit: {MAX_PDF_SIZE_MB}MB)")

    log(f"OK: Created {pdf_filename} | pages {start_page + 1}-{end_page + 1}")
    return output_path


def create_output_pdfs(groups, reader, total_pages, rotation_degrees=0):
    """Create individual PDF files for each group."""
    session_dir = create_output_session_dir()

    pdf_files = []

    for file_no, start_page, end_page in groups:
        try:
            output_path = create_output_pdf(
                file_no,
                start_page,
                end_page,
                reader,
                total_pages,
                session_dir,
                rotation_degrees,
            )
            pdf_files.append(output_path)

        except Exception as e:
            log(f"ERROR: Could not create PDF for group {file_no}: {e}")

    if len(pdf_files) != len(groups):
        raise ValueError(f"Created {len(pdf_files)} PDFs for {len(groups)} detected groups")

    return pdf_files, session_dir


def create_zip_bundle(pdf_files, session_dir):
    """Bundle all PDFs into a ZIP file."""
    zip_filename = session_dir / "pdf_split_output.zip"

    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for pdf_file in pdf_files:
            zipf.write(pdf_file, arcname=pdf_file.name)
            log(f"Added to ZIP: {pdf_file.name}")

    zip_size = os.path.getsize(zip_filename) / (1024 * 1024)
    log(f"\nOK: ZIP created: {zip_filename} ({zip_size:.2f}MB)")

    return zip_filename


def validate_groups(groups, total_pages):
    """Validate that groups are present, sorted, valid, and non-overlapping."""
    log("\n" + "=" * 60)
    log("VALIDATION REPORT")
    log("=" * 60)

    if not groups:
        log("ERROR: No groups were detected")
        return False

    if groups != sorted(groups, key=lambda item: item[1]):
        log("ERROR: Groups are not sorted by start page")
        return False

    seen_names = set()
    for i, (file_no, start, end) in enumerate(groups, 1):
        try:
            validate_group(file_no, start, end, total_pages)
        except ValueError as e:
            log(f"ERROR: {e}")
            return False

        if file_no in seen_names:
            log(f"ERROR: Duplicate output filename would be created: {file_no}.pdf")
            return False
        seen_names.add(file_no)

        log(f"Group {i}: No.{file_no} | Pages {start + 1}-{end + 1} ({end - start + 1} pages)")

    for i in range(len(groups) - 1):
        if groups[i][2] >= groups[i + 1][1]:
            log(f"ERROR: Overlap detected between group {i + 1} and {i + 2}")
            return False

    log("OK: No overlaps found")
    return True


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def process_pdf_file(pdf_path):
    """
    Process one PDF file and return a result dictionary.

    Args:
        pdf_path (str): Path to input PDF file
    """
    print("\n" + "=" * 60)
    print("PDF SPLIT FRAMEWORK v1.0")
    print("=" * 60)

    pdf_path = normalize_pdf_path(pdf_path)
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    try:
        log(f"\nSTEP 1: Analyzing PDF: {pdf_path}")
        groups, reader, total_pages = analyze_pdf(pdf_path)

        log("\nSTEP 2: Validating groups")
        if not validate_groups(groups, total_pages):
            raise ValueError("Validation failed")

        log("\nSTEP 3: Creating output PDFs")
        pdf_files, session_dir = create_output_pdfs(groups, reader, total_pages)

        log("\nSTEP 4: Bundling to ZIP")
        zip_file = create_zip_bundle(pdf_files, session_dir)

        print("\n" + "=" * 60)
        print("PROCESSING COMPLETE")
        print("=" * 60)
        print(f"Output Directory: {session_dir}")
        print("Output Files: Named by detected No. markers")
        print(f"Total Files Created: {len(pdf_files)}")
        print(f"ZIP File: {zip_file}")
        print(f"Total Groups Detected: {len(groups)}")
        print("=" * 60 + "\n")

        return {
            "status": "success",
            "groups": groups,
            "pdf_files": [str(f) for f in pdf_files],
            "output_dir": str(session_dir),
            "zip_file": str(zip_file),
            "total_groups": len(groups),
        }

    except Exception as e:
        print(f"\nERROR: {e}")
        return {
            "status": "error",
            "message": str(e),
        }


def process_pdf_file_manual(pdf_path, file_no, page_count, rotation_degrees=0):
    """
    Create one output PDF from the first N pages without OCR.

    Args:
        pdf_path (str): Path to input PDF file
        file_no (str): Output file number/name, e.g. "107"
        page_count (int): Number of pages to include from the start
    """
    print("\n" + "=" * 60)
    print("PDF SPLIT FRAMEWORK v1.0 - MANUAL MODE")
    print("=" * 60)

    pdf_path = normalize_pdf_path(pdf_path)
    file_no = str(file_no).strip()
    page_count = int(page_count)

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if not file_no:
        raise ValueError("File number cannot be empty")
    if page_count < 1:
        raise ValueError("Page count must be at least 1")

    try:
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
        if page_count > total_pages:
            raise ValueError(f"Page count {page_count} exceeds PDF pages {total_pages}")

        groups = [(file_no, 0, page_count - 1)]

        log("\nSTEP 1: Manual grouping")
        log(f"Group: No.{file_no} | Pages 1-{page_count} of {total_pages}")

        log("\nSTEP 2: Creating output PDF")
        pdf_files, session_dir = create_output_pdfs(groups, reader, total_pages, rotation_degrees)

        log("\nSTEP 3: Bundling to ZIP")
        zip_file = create_zip_bundle(pdf_files, session_dir)

        print("\n" + "=" * 60)
        print("MANUAL PROCESSING COMPLETE")
        print("=" * 60)
        print(f"Output Directory: {session_dir}")
        print(f"Output File: {file_no}.pdf")
        print(f"Pages Included: 1-{page_count}")
        print(f"Output Rotation: {rotation_degrees} degrees clockwise")
        print(f"ZIP File: {zip_file}")
        print("=" * 60 + "\n")

        return {
            "status": "success",
            "groups": groups,
            "pdf_files": [str(f) for f in pdf_files],
            "output_dir": str(session_dir),
            "zip_file": str(zip_file),
            "total_groups": 1,
        }

    except Exception as e:
        print(f"\nERROR: {e}")
        return {
            "status": "error",
            "message": str(e),
        }


def ask_non_empty(prompt):
    """Prompt until the user enters a non-empty value."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Please enter a value.")


def ask_digits_auto(prompt, allow_edit=False):
    """
    Read digits and auto-submit after a short pause.

    Enter still submits immediately. Backspace edits the current value.
    When allow_edit=True, typing E returns to the previous prompt.
    Falls back to normal input when single-key console input is unavailable.
    """
    if os.name != "nt" or not sys.stdin.isatty():
        value = ask_non_empty(prompt)
        if allow_edit and value.lower() == "e":
            return EDIT_COMMAND
        return value

    import msvcrt

    while True:
        print(prompt, end="", flush=True)
        digits = []
        last_key_time = None

        while True:
            if msvcrt.kbhit():
                char = msvcrt.getwch()

                if char in ("\r", "\n"):
                    print()
                    if digits:
                        return "".join(digits)
                    print("Please enter a number.")
                    break

                if allow_edit and char.lower() == "e":
                    print("E")
                    return EDIT_COMMAND

                if char == "\x08":
                    if digits:
                        digits.pop()
                        print("\b \b", end="", flush=True)
                    last_key_time = time.monotonic() if digits else None
                    continue

                if char.isdigit():
                    digits.append(char)
                    print(char, end="", flush=True)
                    last_key_time = time.monotonic()
                    continue

            if digits and last_key_time and time.monotonic() - last_key_time >= AUTO_ACCEPT_SECONDS:
                print()
                return "".join(digits)

            time.sleep(0.02)


def ask_page_count(prompt, remaining_pages, allow_edit=False):
    """Prompt until the user enters a valid page count."""
    while True:
        value = ask_digits_auto(prompt, allow_edit=allow_edit)
        if value == EDIT_COMMAND:
            return EDIT_COMMAND

        try:
            page_count = int(value)
        except ValueError:
            print("Please enter a whole number.")
            continue

        if page_count < 1:
            print("Page count must be at least 1.")
            continue
        if page_count > remaining_pages:
            print(f"Only {remaining_pages} page(s) remain. Enter {remaining_pages} or less.")
            continue
        return page_count


def ask_rotation(default_rotation=0):
    """Ask for a rotation value unless one was already supplied."""
    allowed = {0, 90, 180, 270}
    while True:
        value = input(
            f"Rotate output pages clockwise? [0/90/180/270, default {default_rotation}]: "
        ).strip()
        if not value:
            return default_rotation
        try:
            rotation = int(value)
        except ValueError:
            print("Please enter 0, 90, 180, or 270.")
            continue
        if rotation not in allowed:
            print("Please enter 0, 90, 180, or 270.")
            continue
        return rotation


def process_pdf_file_interactive(pdf_path, rotation_degrees=0):
    """
    Interactively split a PDF by asking for each output number and page count.

    The first answer names the output PDF. The second answer says how many
    pages from the current position belong to that PDF.
    """
    print("\n" + "=" * 60)
    print("PDF SPLIT FRAMEWORK v1.0 - INTERACTIVE MANUAL MODE")
    print("=" * 60)

    pdf_path = normalize_pdf_path(pdf_path)
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    try:
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
        current_page = 0
        groups = []
        pdf_files = []
        seen_names = set()
        session_dir = create_output_session_dir()

        print(f"\nInput PDF: {pdf_path}")
        print(f"Total pages in input PDF: {total_pages}")
        print(f"Output directory: {session_dir}")
        rotation_degrees = ask_rotation(rotation_degrees)
        print(f"Output rotation: {rotation_degrees} degrees clockwise")
        print("Enter one output file at a time. The script stops when all pages are assigned.\n")

        while current_page < total_pages:
            remaining_pages = total_pages - current_page
            human_start = current_page + 1

            print("-" * 60)
            print(f"Next unassigned page: {human_start}")
            print(f"Pages remaining: {remaining_pages}")

            file_no = ask_digits_auto("What is the No. on this first page? ")
            page_count = ask_page_count(
                f"How many total pages are in No.{file_no}? ",
                remaining_pages,
                allow_edit=True,
            )
            if page_count == EDIT_COMMAND:
                print("Editing No. for this file.\n")
                continue

            start_page = current_page
            end_page = current_page + page_count - 1

            if file_no in seen_names:
                print(f"ERROR: {file_no}.pdf already exists in this session. Enter a different No.")
                continue

            output_path = create_output_pdf(
                file_no,
                start_page,
                end_page,
                reader,
                total_pages,
                session_dir,
                rotation_degrees,
            )

            groups.append((file_no, start_page, end_page))
            pdf_files.append(output_path)
            seen_names.add(file_no)
            current_page = end_page + 1

            print(f"Created {output_path}")
            print(f"Added {file_no}.pdf from pages {start_page + 1}-{end_page + 1}\n")

        log("\nSTEP 1: Validating manual groups")
        if not validate_groups(groups, total_pages):
            raise ValueError("Validation failed")

        log("\nSTEP 2: Bundling to ZIP")
        zip_file = create_zip_bundle(pdf_files, session_dir)

        print("\n" + "=" * 60)
        print("INTERACTIVE PROCESSING COMPLETE")
        print("=" * 60)
        print(f"Output Directory: {session_dir}")
        print(f"Total Files Created: {len(pdf_files)}")
        print(f"ZIP File: {zip_file}")
        print("=" * 60 + "\n")

        return {
            "status": "success",
            "groups": groups,
            "pdf_files": [str(f) for f in pdf_files],
            "output_dir": str(session_dir),
            "zip_file": str(zip_file),
            "total_groups": len(groups),
        }

    except Exception as e:
        print(f"\nERROR: {e}")
        return {
            "status": "error",
            "message": str(e),
        }


def main():
    parser = argparse.ArgumentParser(description="Split a PDF interactively by file number and page count")
    parser.add_argument("pdf", help="Path to the input PDF")
    parser.add_argument("file_no", nargs="?", help="One-shot manual mode: output file number")
    parser.add_argument("page_count", nargs="?", type=int, help="One-shot manual mode: pages to include from start")
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Use OCR marker detection instead of interactive manual mode.",
    )
    parser.add_argument(
        "--rotate",
        type=int,
        choices=[0, 90, 180, 270],
        default=0,
        help="Rotate output pages clockwise by this many degrees.",
    )
    args = parser.parse_args()

    if args.auto:
        result = process_pdf_file(args.pdf)
    elif args.file_no and args.page_count:
        result = process_pdf_file_manual(args.pdf, args.file_no, args.page_count, args.rotate)
    else:
        result = process_pdf_file_interactive(args.pdf, args.rotate)
    print(f"\nResult: {result}")
    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())

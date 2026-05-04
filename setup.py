"""
Setup-and-run entry point for the PDF Split Framework.

Usage:
    python setup.py "C:/path/to/file.pdf"
    python setup.py "C:/path/to/file.pdf" 107 12
    python setup.py "C:/path/to/file.pdf" --auto
"""

import argparse
import sys
from pathlib import Path

from verify_setup import (
    check_config,
    check_dependencies,
    check_output_directory,
    check_poppler,
    check_python_version,
    check_tesseract,
    print_installation_guide,
)


def normalize_input_path(pdf_path):
    """Normalize a quoted path or file URL into a filesystem path."""
    path = str(pdf_path).strip().strip('"')
    if path.startswith("file:///"):
        path = path.replace("file:///", "", 1)
    return Path(path)


def run_required_setup_checks(manual_mode=False):
    """Run only the required setup checks before processing the PDF."""
    print("\n" + "=" * 60)
    print("PDF SPLIT FRAMEWORK - SETUP CHECKS")
    print("=" * 60)

    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Configuration", check_config),
        ("Output Directory", check_output_directory),
    ]
    if not manual_mode:
        checks.insert(2, ("Tesseract OCR", check_tesseract))
        checks.insert(3, ("Poppler", check_poppler))

    results = []
    for name, check_func in checks:
        try:
            results.append((name, check_func()))
        except Exception as exc:
            print(f"FAIL Error during {name} check: {exc}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("SETUP SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{status}: {name}")
        all_passed = all_passed and passed

    if not all_passed:
        print_installation_guide()

    return all_passed


def parse_args():
    parser = argparse.ArgumentParser(
        description="Verify setup, then split one PDF interactively by page counts.",
    )
    parser.add_argument("pdf", help='Path to the PDF, e.g. "C:/files/input.pdf"')
    parser.add_argument("file_no", nargs="?", help='One-shot mode: output number, e.g. "107"')
    parser.add_argument("page_count", nargs="?", type=int, help="One-shot mode: number of pages to include from the start")
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
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Skip setup checks and process the PDF immediately.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    pdf_path = normalize_input_path(args.pdf)
    manual_mode = not args.auto

    if not pdf_path.exists():
        print(f"\nERROR: PDF not found: {pdf_path}")
        return 1

    if pdf_path.suffix.lower() != ".pdf":
        print(f"\nERROR: Input must be a PDF file: {pdf_path}")
        return 1

    if (args.file_no is None) != (args.page_count is None):
        print("\nERROR: One-shot mode requires both file_no and page_count.")
        print('Example: python setup.py "C:/path/to/file.pdf" 107 12')
        return 1

    if not args.skip_checks and not run_required_setup_checks(manual_mode=manual_mode):
        return 1

    from work import process_pdf_file, process_pdf_file_interactive, process_pdf_file_manual

    if args.auto:
        result = process_pdf_file(str(pdf_path))
    elif args.file_no and args.page_count:
        result = process_pdf_file_manual(str(pdf_path), args.file_no, args.page_count, args.rotate)
    else:
        result = process_pdf_file_interactive(str(pdf_path), args.rotate)
    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    sys.exit(main())

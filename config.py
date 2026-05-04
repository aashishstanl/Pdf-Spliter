# PDF Split Framework - Configuration

# Output Configuration
OUTPUT_BASE_DIR = "pdf_splits"

# OCR Configuration
DPI = 300  # Higher DPI = better accuracy but slower (default: 300)
OCR_ROTATIONS = (0, 90)  # Fast mode: check normal and sideways-left marker crops
BEING_STAMP_LINE = 5  # The ending Being No. is always on the 5th line of the stamp
START_NO_REGION = (0.0, 0.0, 0.30, 1.0)  # Left strip only for the handwritten first-page No.
BEING_STAMP_REGION = (0.0, 0.0, 0.40, 1.0)  # Left strip only for the Being No. stamp
OCR_SCALE = 2  # Enlarge marker crops before OCR
OCR_PSM_MODES = (6,)  # Fast mode: one Tesseract reading mode per crop
OCR_PREPROCESS_VARIANTS = ("contrast",)  # Fast mode: use one image cleanup variant

# Debug Mode
DEBUG = True  # Set to False to suppress logging

# Detection Patterns
NO_PATTERN_REGEX = r'^\s*No\.?\s*[:#-]?\s*(\d+)\b'  # Top-line start marker
BEING_PATTERN_REGEX = r'\bBeing\s+No\.?\s*[:#-]?\s*(\d+)\b'  # End marker

# File Constraints
MAX_PDF_SIZE_MB = 5  # Maximum PDF file size
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
  # Set if tesseract not in PATH (e.g., r"C:\Program Files\Tesseract-OCR\tesseract.exe")
POPPLER_PATH = r"C:\poppler-26.02.0\Library\bin"  # Set to Poppler bin path if not in PATH (e.g., r"C:\poppler\Library\bin")

# Processing
CONTINUE_ON_ERROR = True  # Continue processing remaining PDFs on error
USE_FIFTH_LINE_FALLBACK = False  # Keep False to avoid blue-stamp numbers being treated as new files
AUTO_ACCEPT_SECONDS = 0.8  # Auto-submit typed numbers after this many seconds without another key

"""
Setup Verification Script

Checks all dependencies and configurations before processing PDFs.
"""

import sys
import subprocess
from pathlib import Path

try:
    import config
except ImportError:
    config = None

def check_python_version():
    """Check Python version"""
    print("\n[1] Python Version Check")
    print("-" * 50)
    version = sys.version_info
    min_version = (3, 8)
    
    if version >= min_version:
        print(f"OK Python {version.major}.{version.minor} (Required: 3.8+)")
        return True
    else:
        print(f"FAIL Python {version.major}.{version.minor} (Required: 3.8+)")
        return False

def check_dependencies():
    """Check Python package dependencies"""
    print("\n[2] Python Dependencies Check")
    print("-" * 50)
    
    required_packages = {
        'PyPDF2': 'PDF manipulation',
        'pdf2image': 'PDF to image conversion',
        'pytesseract': 'OCR text extraction',
        'PIL': 'Image processing'
    }
    
    all_installed = True
    for package, description in required_packages.items():
        try:
            __import__(package)
            print(f"OK {package}: {description}")
        except ImportError:
            print(f"FAIL {package}: {description} [MISSING]")
            all_installed = False
    
    return all_installed

def check_tesseract():
    """Check Tesseract OCR installation"""
    print("\n[3] Tesseract OCR Check")
    print("-" * 50)
    
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"OK Tesseract installed: {version_line}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Check Windows installation path
    windows_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if Path(windows_path).exists():
        print(f"OK Tesseract found at: {windows_path}")
        return True
    
    config_path = getattr(config, "TESSERACT_PATH", None)
    if config_path and Path(config_path).exists():
        print(f"OK Tesseract configured at: {config_path}")
        return True

    print("FAIL Tesseract not found in PATH")
    print("  Install from: https://github.com/UB-Mannheim/tesseract/wiki")
    return False

def check_poppler():
    """Check Poppler installation required by pdf2image."""
    print("\n[4] Poppler Check")
    print("-" * 50)

    try:
        result = subprocess.run(["pdfinfo", "-v"],
                              capture_output=True, text=True, timeout=5)
        if result.returncode in (0, 1):
            output = (result.stdout or result.stderr).split("\n")[0]
            print(f"OK Poppler available: {output}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    config_path = getattr(config, "POPPLER_PATH", None)
    if config_path and Path(config_path, "pdfinfo.exe").exists():
        print(f"OK Poppler configured at: {config_path}")
        return True

    print("FAIL Poppler pdfinfo not found in PATH")
    print("  Install Poppler and set POPPLER_PATH in config.py if needed")
    return False

def check_config():
    """Check configuration file"""
    print("\n[5] Configuration Check")
    print("-" * 50)
    
    if Path("config.py").exists():
        print("OK config.py found")
        return True
    else:
        print("FAIL config.py not found")
        return False

def check_output_directory():
    """Check output directory setup"""
    print("\n[6] Output Directory Setup")
    print("-" * 50)
    
    output_dir = Path("pdf_splits")
    try:
        output_dir.mkdir(exist_ok=True)
        print(f"OK Output directory ready: {output_dir.absolute()}")
        return True
    except Exception as e:
        print(f"FAIL Cannot create output directory: {e}")
        return False

def check_sample_pdf():
    """Check for sample PDF (optional)"""
    print("\n[7] Sample PDF Check (Optional)")
    print("-" * 50)
    
    pdf_files = list(Path(".").glob("*.pdf"))
    if pdf_files:
        print(f"OK Found {len(pdf_files)} PDF file(s) in current directory:")
        for pdf in pdf_files[:5]:
            size_mb = pdf.stat().st_size / (1024 * 1024)
            print(f"  - {pdf.name} ({size_mb:.2f} MB)")
        return True
    else:
        print("- No sample PDFs found (Optional - required for testing)")
        return False

def print_installation_guide():
    """Print installation instructions"""
    print("\n" + "="*50)
    print("INSTALLATION GUIDE")
    print("="*50)
    
    print("\n1. Install Python Packages:")
    print("   pip install -r requirements.txt")
    
    print("\n2. Install Tesseract OCR:")
    print("   Windows: Download from")
    print("   https://github.com/UB-Mannheim/tesseract/wiki")
    print()
    print("   Linux (Ubuntu/Debian):")
    print("   sudo apt-get install tesseract-ocr")
    print()
    print("   macOS:")
    print("   brew install tesseract")

    print("\n3. Install Poppler:")
    print("   Windows: Install Poppler and add its bin folder to PATH")
    print("   or set POPPLER_PATH in config.py")
    
    print("\n4. Verify Installation:")
    print("   python verify_setup.py")
    
    print("\n5. Process PDF:")
    print("   python setup.py \"path/to/input.pdf\"")
    print("   or")
    print("   python batch_process.py --input 'path/to/pdf'")

def main():
    """Run all checks"""
    
    print("\n" + "="*50)
    print("PDF SPLIT FRAMEWORK - SETUP VERIFICATION")
    print("="*50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Tesseract OCR", check_tesseract),
        ("Poppler", check_poppler),
        ("Configuration", check_config),
        ("Output Directory", check_output_directory),
        ("Sample PDF", check_sample_pdf),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"FAIL Error during {name} check: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*50)
    print("VERIFICATION SUMMARY")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {name}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    # Recommendation
    print("\n" + "="*50)
    if passed == total:
        print("ALL CHECKS PASSED - Ready to process PDFs!")
        print(f"\nUsage:")
        print("  python setup.py \"your_file.pdf\"")
    else:
        print("SOME CHECKS FAILED - Installation required")
        print_installation_guide()
    
    print("="*50 + "\n")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

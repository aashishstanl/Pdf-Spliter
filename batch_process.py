"""
Batch Processing Utility for PDF Split Framework

Usage:
    python batch_process.py --input "C:/pdf_folder" --output "results"
    python batch_process.py --input "file.pdf"  # Single file
"""

import argparse
import json
from pathlib import Path
from work import process_pdf_file
from datetime import datetime

def batch_process(input_path, output_report=None):
    """
    Process one or more PDF files
    
    Args:
        input_path (str): Path to PDF file or directory
        output_report (str): Optional path to save JSON report
    
    Returns:
        dict: Processing report
    """
    
    input_path = Path(input_path)
    report = {
        'timestamp': datetime.now().isoformat(),
        'input': str(input_path),
        'files_processed': 0,
        'files_successful': 0,
        'files_failed': 0,
        'results': []
    }
    
    print("\n" + "="*70)
    print("PDF BATCH PROCESSOR v1.0")
    print("="*70 + "\n")
    
    # Determine if single file or directory
    if input_path.is_file() and input_path.suffix.lower() == '.pdf':
        files = [input_path]
    elif input_path.is_dir():
        files = list(input_path.glob("*.pdf"))
        if not files:
            print(f"No PDF files found in: {input_path}")
            return report
    else:
        print(f"Invalid input: {input_path} (must be PDF file or directory)")
        return report
    
    print(f"Found {len(files)} PDF file(s) to process\n")
    
    # Process each file
    for idx, pdf_file in enumerate(files, 1):
        print(f"[{idx}/{len(files)}] Processing: {pdf_file.name}")
        print("-" * 70)
        
        try:
            result = process_pdf_file(str(pdf_file))
            
            report['files_processed'] += 1
            
            file_result = {
                'filename': pdf_file.name,
                'status': result['status'],
                'timestamp': datetime.now().isoformat()
            }
            
            if result['status'] == 'success':
                report['files_successful'] += 1
                file_result.update({
                    'total_groups': result['total_groups'],
                    'output_dir': result['output_dir'],
                    'zip_file': result['zip_file'],
                    'pdfs_created': len(result['pdf_files'])
                })
                print(f"✓ SUCCESS: Created {result['total_groups']} PDF files")
                print(f"  Output: {result['output_dir']}")
            else:
                report['files_failed'] += 1
                file_result['error'] = result.get('message', 'Unknown error')
                print(f"✗ FAILED: {result.get('message', 'Unknown error')}")
            
            report['results'].append(file_result)
            
        except Exception as e:
            report['files_processed'] += 1
            report['files_failed'] += 1
            print(f"✗ ERROR: {str(e)}")
            report['results'].append({
                'filename': pdf_file.name,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        
        print()
    
    # Print summary
    print("="*70)
    print("BATCH PROCESSING SUMMARY")
    print("="*70)
    print(f"Total Files Processed: {report['files_processed']}")
    print(f"Successful: {report['files_successful']}")
    print(f"Failed: {report['files_failed']}")
    print("="*70 + "\n")
    
    # Save report if specified
    if output_report:
        output_report = Path(output_report)
        output_report.parent.mkdir(parents=True, exist_ok=True)
        with open(output_report, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to: {output_report}\n")
    
    return report

def main():
    """Command-line interface"""
    
    parser = argparse.ArgumentParser(
        description='Batch process PDF files with the PDF Split Framework',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python batch_process.py --input "C:/pdfs/document.pdf"
  python batch_process.py --input "C:/pdfs/" --output "report.json"
  python batch_process.py -i "C:/pdfs" -o "C:/results/report.json"
        """
    )
    
    parser.add_argument(
        '-i', '--input',
        required=True,
        help='Path to PDF file or directory containing PDFs'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Optional path to save processing report as JSON'
    )
    
    args = parser.parse_args()
    
    # Run batch processing
    batch_process(args.input, args.output)

if __name__ == "__main__":
    main()

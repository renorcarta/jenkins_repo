#!/usr/bin/env python3

import os
import re
import json
import sys
from PyPDF2 import PdfReader

def extract_technical_debt(pdf_path):
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found at: {pdf_path}")
        sys.exit(1)

    reader = PdfReader(pdf_path)
    text = ""

    for page in reader.pages:
        text += page.extract_text() + "\n"

    # Regex pattern to match the "Total" line, capturing the last percentage
    match = re.search(r"Total\s+\d+\s+\d+\s+\d+%?\s+(\d+)%", text)

    if not match:
        print("❌ Could not find Total Technical Debt percentage in the PDF.")
        sys.exit(1)

    current_sprint_debt = int(match.group(1))

    result = {
        "source": os.path.basename(pdf_path),
        "total_technical_debt_percent": current_sprint_debt
    }

    return result

import argparse

def main():
    parser = argparse.ArgumentParser(description="Extract technical debt from PDF")
    parser.add_argument('--pdf_path', required=True, help='Path to PDF file')
    parser.add_argument('--output', required=True, help='Output JSON file path')
    args = parser.parse_args()

    result = extract_technical_debt(args.pdf_path)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    print(f"✅ PDF technical debt extracted: {result['total_technical_debt_percent']}%")
    print(f"📄 Output written to: {args.output}")

if __name__ == "__main__":
    main()

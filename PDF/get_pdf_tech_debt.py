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

def main():
    pdf_path = "../PDF/CAS_CMIT_CLFC_SourceCodeReview.pdf"
    output_path = "Artifacts/pdf-tech-debt.json"

    result = extract_technical_debt(pdf_path)

    # Ensure output folder exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"✅ PDF technical debt extracted: {result['total_technical_debt_percent']}%")
    print(f"📄 Output written to: {output_path}")

if __name__ == "__main__":
    main()

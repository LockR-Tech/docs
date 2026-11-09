"""Join the registration form v2.0 and BM03 into the file to submit: SWP490_FA26SE002_R2_Registration.pdf.

Run after exporting both PDFs: uv run --no-project --with pymupdf python merge_registration.py
"""
import os

import fitz

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
PARTS = ['FA26SE002_Registration_v2.0.pdf', 'SWP490_FA26SE002_R2_RecordOfChanges.pdf']
OUT = os.path.join(OUT_DIR, 'SWP490_FA26SE002_R2_Registration.pdf')

merged = fitz.open()
for part in PARTS:
    with fitz.open(os.path.join(OUT_DIR, part)) as doc:
        merged.insert_pdf(doc)
merged.save(OUT)
print('saved', OUT, '| pages', merged.page_count)

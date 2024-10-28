# pdf_utils.py
import PyPDF2
import streamlit as st
import logging
import re
from anthropic_utils import summarize_text

def extract_text_from_pdf(pdf_file):
    """Extract raw text from a PDF file."""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {str(e)}", exc_info=True)
        return ""

def is_pdf_parsable(pdf_file):
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        return len(pdf_reader.pages) > 0
    except Exception as e:
        logging.error(f"Error reading PDF: {str(e)}", exc_info=True)
        st.error(f"Error reading PDF: {str(e)}")
        return False

def extract_invoice_details(pdf_file):
    """Extract specific invoice details from the PDF using Claude API."""
    try:
        # Extract raw text from the PDF
        text = extract_text_from_pdf(pdf_file)
        
        if not text:
            return {"error": "No text found in PDF.", "sections": [], "present_fields": []}

        # Use Claude API to summarize and extract structured information
        sections = summarize_text(text)
        
        # Initialize details dictionary with required keys
        details = {
            "sections": sections,
            "raw_text": text,
            "present_fields": []
        }
        
        # Analyze which fields are present
        if sections and isinstance(sections, list):
            content = sections[0].get("content", "")
            field_markers = {
                "Recipient": ["Recipient Name", "Shipping Address"],
                "Invoice": ["Invoice Number", "Date"],
                "Line Items": ["Line Items"],
                "Tax": ["Tax Information"],
                "Total": ["Total Amount"]
            }
            
            for marker, fields in field_markers.items():
                if marker in content:
                    details["present_fields"].extend(fields)
        
        return details

    except Exception as e:
        logging.error(f"Error extracting details from PDF: {str(e)}", exc_info=True)
        return {
            "error": f"Unable to extract details: {str(e)}",
            "sections": [],
            "present_fields": []
        }

def extract_field(pattern, text):
    """Helper function to extract a field using regex."""
    match = re.search(pattern, text)
    return match.group(1) if match else None

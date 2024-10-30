# app.py
import streamlit as st
import logging
import sys
import os
import requests
import io
import urllib.parse
from pdf_utils import extract_text_from_pdf, is_pdf_parsable, extract_invoice_details
from anthropic_utils import summarize_text, set_api_key, query_document, client

# Configure logging but don't display it
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def convert_github_url_to_raw(url):
    """Convert GitHub blob URL to raw content URL"""
    if "github.com" in url and "/blob/" in url:
        return url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
    return url

def is_valid_pdf_url(url):
    """Validate if the URL points to a PDF file"""
    try:
        # Convert GitHub URL if necessary
        url = convert_github_url_to_raw(url)
        
        # Check if URL is properly formatted
        parsed = urllib.parse.urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            return False
        
        # Check if URL ends with .pdf or has PDF content type
        response = requests.head(url, allow_redirects=True, timeout=5)
        content_type = response.headers.get('content-type', '').lower()
        return (url.lower().endswith('.pdf') or 
                'application/pdf' in content_type or 
                'binary/octet-stream' in content_type)
    except:
        return False

def download_pdf_from_url(url):
    """Download PDF from URL with improved error handling"""
    try:
        # Convert GitHub URL if necessary
        url = convert_github_url_to_raw(url)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, stream=True, timeout=10)
        response.raise_for_status()
        
        # Verify content type
        content_type = response.headers.get('content-type', '').lower()
        if 'application/pdf' not in content_type and not url.lower().endswith('.pdf'):
            raise ValueError("URL does not point to a valid PDF file")
        
        # Read the content into BytesIO
        pdf_content = io.BytesIO()
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                pdf_content.write(chunk)
        
        pdf_content.seek(0)
        return pdf_content
    except requests.exceptions.RequestException as e:
        st.error(f"Error downloading PDF: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return None

def display_dashboard(details):
    """Display the extracted details in a professional dashboard."""
    st.markdown("""
        <style>
        .dashboard-container {
            padding: 20px;
            border-radius: 10px;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .status-green {
            color: #28a745;
            font-size: 20px;
        }
        .status-red {
            color: #dc3545;
            font-size: 20px;
        }
        .section-header {
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #2c3e50;
        }
        .info-card {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        .field-missing {
            color: #dc3545;
            font-style: italic;
        }
        </style>
    """, unsafe_allow_html=True)

    if "error" in details:
        st.error(details["error"])
        return

    # Create columns for the dashboard
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📄 Invoice Analysis")
        if "sections" in details and details["sections"]:
            for section in details["sections"]:
                with st.expander(section.get("title", "Analysis"), expanded=True):
                    st.markdown(f"""
                    <div class="info-card">
                        <p>{section.get("content", "No content available")}</p>
                    </div>
                    """, unsafe_allow_html=True)

    with col2:
        st.markdown("### 📊 Field Validation")
        required_fields = [
            "Recipient Name",
            "Shipping Address",
            "Invoice Number",
            "Date",
            "Line Items",
            "Tax Information"
        ]
        
        present_fields = details.get("present_fields", [])
        
        for field in required_fields:
            is_present = field in present_fields
            status = "✅" if is_present else "❌"
            color = "status-green" if is_present else "status-red"
            message = field if is_present else f"{field} (Missing)"
            st.markdown(f"""
            <div class="info-card">
                <span class="{color}">{status}</span> {message}
            </div>
            """, unsafe_allow_html=True)

    # Add chat interface
    st.markdown("### 💬 Ask Questions About This Invoice")
    user_question = st.text_input("Ask a question about the invoice:")
    if user_question:
        if "raw_text" in details:
            answer = query_document(user_question, details["raw_text"])
            st.markdown(f"""
            <div class="info-card">
                <p><strong>Q:</strong> {user_question}</p>
                <p><strong>A:</strong> {answer}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Unable to process questions without document context.")

def main():
    # Read API key from secrets correctly
    api_key = st.secrets["ANTHROPIC_API_KEY"]  # Use the key name, not the value
    set_api_key(api_key)
    
    st.set_page_config(page_title="Invoice Analyzer", layout="wide")
    
    # Add custom CSS
    st.markdown("""
        <style>
        .upload-section {
            text-align: center;
            padding: 40px;
            background-color: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .main-title {
            color: #2c3e50;
            font-size: 42px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .subtitle {
            color: #7f8c8d;
            font-size: 20px;
            margin-bottom: 30px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="upload-section">
            <h1 class="main-title">📄 Invoice Analysis - Quick Mockup for Didero</h1>
            <p class="subtitle">Upload your invoice for instant analysis and insights</p>
        </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file is not None:
        with st.spinner('Analyzing your invoice...'):
            details = extract_invoice_details(uploaded_file)
            display_dashboard(details)

if __name__ == "__main__":
    main()

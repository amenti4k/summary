# anthropic_utils.py
import os
import anthropic
import logging
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_random_exponential

client = None

def set_api_key(api_key: str) -> None:
    """Initialize the Anthropic client with the provided API key."""
    global client
    client = anthropic.Anthropic(api_key=api_key)

def chunk_text(text: str, chunk_size: int = 1000) -> List[str]:
    """Split text into chunks with overlap."""
    chunks = []
    overlap = 200
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    
    return chunks

def query_document(question: str, context: str) -> str:
    """Query the document using Claude's context window."""
    if not client:
        raise ValueError("API client not initialized")
    
    try:
        # Split context into manageable chunks
        chunks = chunk_text(context)
        relevant_context = "\n".join(chunks[:3])  # Use first 3 chunks for context
        
        prompt = f"""You are an AI assistant analyzing an invoice document. Use the following invoice content to answer the question.
        Only use information present in the invoice content. If information is not available, say so.
        
        Invoice Content:
        {relevant_context}

        Question: {question}

        Provide a clear, direct answer based only on the information in the invoice."""

        response = client.messages.create(
            model="claude-2.1",  # Changed from claude-3-sonnet-20240229-v1:0
            max_tokens=1000,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()

    except Exception as e:
        logging.error(f"Error in query: {str(e)}", exc_info=True)
        return f"Error processing question: {str(e)}"

@retry(
    wait=wait_random_exponential(min=1, max=60),
    stop=stop_after_attempt(3)
)
def summarize_text(text: str) -> List[Dict[str, str]]:
    if not client:
        raise ValueError("API client not initialized")
    
    try:
        logging.info("Analyzing invoice with Claude")
        prompt = f"""Analyze this invoice and extract information in these sections:

1. Recipient Information (Name, Address, Contact)
2. Invoice Details (Number, Date, PO Box, Due Date)
3. Line Items (Quantity, Description, Unit Price, Total)
4. Financial Summary (Subtotal, Tax, Total)
5. Additional Details (Signature, Notes)

Format each section clearly and include all found information.

Invoice text:
{text}"""

        response = client.messages.create(
            model="claude-2.1",  # Changed from claude-3-sonnet-20240229-v1:0
            max_tokens=4000,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}]
        )

        if response and hasattr(response.content[0], 'text'):
            analysis = response.content[0].text
            sections = [
                {"title": "Invoice Analysis", "content": analysis}
            ]
            return sections
        else:
            return [{"title": "Error", "content": "Unable to parse response"}]

    except Exception as e:
        logging.error(f"Error analyzing invoice: {str(e)}", exc_info=True)
        return [{"title": "Error", "content": f"Error: {str(e)}"}]

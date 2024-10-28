# tests.py
import unittest
from unittest.mock import patch, MagicMock
from pdf_utils import extract_text_from_pdf
from anthropic_utils import summarize_text  # Updated import
import os

class TestPDFSummarization(unittest.TestCase):

    def test_extract_text_from_pdf(self):
        # Ensure you have a sample.pdf in your project directory for testing
        with open("sample.pdf", "rb") as pdf_file:
            text = extract_text_from_pdf(pdf_file)
            self.assertIsNotNone(text)
            self.assertGreater(len(text), 0, "Failed to extract text from PDF")

    @patch('anthropic.Client.completions.create')  # Updated patch path
    def test_summarize_text(self, mock_create):
        # Create a mock response object
        mock_response = MagicMock()
        mock_response.__getitem__.return_value = MagicMock()
        mock_response.get.return_value = "Test summary"
        mock_create.return_value = {'completion': 'Test summary'}
        
        summary = summarize_text("Test input")
        self.assertEqual(summary, [{"title": "Summary", "summary": "Test summary"}], "API call did not return expected summary")

    def test_summarize_text_integration(self):
        # Ensure you have a valid API key set in your environment
        os.environ["ANTHROPIC_API_KEY"] = "sk-ant-api03-your-api-key"
        
        # Test input
        test_input = "This is a test input for summarization."
        
        # Call the function
        summary = summarize_text(test_input)
        
        # Check if the summary is not empty
        self.assertTrue(summary, "The summary should not be empty.")

    @patch('anthropic.Client.completions.create')  # Updated patch path
    def test_summarize_text_with_mock(self, mock_create):
        # Mock the API response as a dictionary
        mock_create.return_value = {'completion': 'Test summary'}
        summary = summarize_text("Test input")
        self.assertEqual(summary, [{"title": "Summary", "summary": "Test summary"}], "API call did not return expected summary")

if __name__ == '__main__':
    unittest.main()

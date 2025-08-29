# write code to test-ollama-local.py
import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from PIL import Image
import pytesseract
import img2pdf
import test_ollama_local  # Assuming the file to be tested is named test-ollama-local.py
class TestOllamaLocal(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for input and output
        self.test_dir = tempfile.TemporaryDirectory()
        self.input_dir = os.path.join(self.test_dir.name, 'input')
        self.output_dir = os.path.join(self.test_dir.name, 'output-folder')
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        self.png_file = os.path.join(self.input_dir, 'test_image.png')
        
        # Create a simple PNG file for testing
        image = Image.new('RGB', (100, 100), color = (73, 109, 137))
        image.save(self.png_file)

    def tearDown(self):
        # Clean up the temporary directory
        self.test_dir.cleanup()

    @patch('pytesseract.image_to_string')
    def test_pngs_to_md(self, mock_ocr):
        mock_ocr.return_value = "Extracted text"
        
        # Run the pngs_to_md function from the module
        test_ollama_local.pngs_to_md(input_dir=self.input_dir, output_dir=self.output_dir)
        
        output_md = os.path.join(self.output_dir, 'output.md')
        self.assertTrue(os.path.exists(output_md))
        
        with open(output_md, 'r') as f:
            content = f.read()
            self.assertIn("# test_image.png", content)
            self.assertIn("Extracted text", content)

    def test_pngs_to_pdf(self):
        # Run the pngs_to_pdf function from the module
        test_ollama_local.pngs_to_pdf(input_dir=self.input_dir, output_dir=self.output_dir)
        
        output_pdf = os.path.join(self.output_dir, 'output.pdf')
        self.assertTrue(os.path.exists(output_pdf))
        
        # Check if the PDF file is not empty
        self.assertGreater(os.path.getsize(output_pdf), 0)
if __name__ == '__main__':
    unittest.main()
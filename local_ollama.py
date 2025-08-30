import json
import requests
import os
from typing import List, Optional
from requests.exceptions import RequestException
from pydantic import BaseModel, Field, ValidationError
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from PIL import Image
import pytesseract
import img2pdf
from time import sleep
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaResponse(BaseModel):
    response: str
    done: bool

# class OllamaResponse(BaseModel):
#     id: str
#     object: str
#     created: int
#     model: str
#     choices: List[dict]
#     usage: Optional[dict] = None
class OllamaErrorResponse(BaseModel):
    error: dict
class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
        self.session.mount('http://', HTTPAdapter(max_retries=retries))


    def _post(self, endpoint: str, data: dict) -> str:
        url = f"{self.base_url}/{endpoint}"
        try:
            with self.session.post(url, json=data, stream=True) as response:
                response.raise_for_status()
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        chunk = line.decode('utf-8')
                        try:
                            parsed = json.loads(chunk)
                            full_response += parsed.get("response", "")
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse chunk: {chunk}")
                return full_response
        except RequestException as e:
            raise Exception(f"Request failed: {e}")
    
    def generate(self, model: str, prompt: str) -> OllamaResponse:
        data = {
            "model": model,
            "prompt": prompt
        }
        return self._post("api/generate", data)
def pngs_to_md(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    output_md = os.path.join(output_dir, 'output.md')
    output_images_dir = os.path.join(output_dir, 'images')
    os.makedirs(output_images_dir, exist_ok=True)

    png_files = [os.path.join(input_dir, i) for i in os.listdir(input_dir) if i.endswith('.png')]
    png_files.sort()

    mode = 'a' if os.path.exists(output_md) else 'w'
    with open(output_md, mode) as f:
        for png in png_files:
            img_name = os.path.basename(png)
            dest_path = os.path.join(output_images_dir, img_name)
            if os.path.exists(dest_path):
                continue
            try:
                image = Image.open(png)
                text = pytesseract.image_to_string(image)
                f.write(f"# {img_name}\n\n{text}\n\n")
                with open(png, 'rb') as src, open(dest_path, 'wb') as dst:
                    dst.write(src.read())
            except Exception as e:
                f.write(f"# {img_name}\n\nError extracting text: {e}\n\n")
def pngs_to_pdf(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    output_pdf = os.path.join(output_dir, 'output.pdf')
    png_files = [os.path.join(input_dir, i) for i in os.listdir(input_dir) if i.endswith('.png')]
    png_files.sort()
    if png_files:
        with open(output_pdf, 'wb') as f:
            f.write(img2pdf.convert(png_files))
def main():
    input_dir = os.path.expanduser('~/Pictures/Screenshots')
    output_dir = os.path.join(os.path.dirname(__file__), 'output-folder')
    # pngs_to_md(input_dir, output_dir)
    # pngs_to_pdf(input_dir, output_dir)
    client = OllamaClient()
    try:
        response = client.generate(model="llama3.2-vision:latest", prompt="Hello, Ollama!")
        logger.info(f"Ollama Response: {response}")
    except Exception as e:
        logger.error(f"Error calling Ollama API: {e}")
if __name__ == "__main__":
    main()
else:
    logger.info(f"No PNG files found in {input_dir}")
    print(f"PDF created: {output_pdf}")


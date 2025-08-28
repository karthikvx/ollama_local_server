import os
import img2pdf
from PIL import Image

# Define input and output directories
input_dir = os.path.expanduser('~/Pictures/Screenshots')
output_dir = os.path.join(os.path.dirname(__file__), 'output-folder')
os.makedirs(output_dir, exist_ok=True)
output_pdf = os.path.join(output_dir, 'output.pdf')

# Collect PNG files from input_dir
png_files = [os.path.join(input_dir, i) for i in os.listdir(input_dir) if i.endswith('.png')]
png_files.sort()

if png_files:
    with open(output_pdf, 'wb') as f:
        f.write(img2pdf.convert(png_files))
    print(f"PDF created: {output_pdf}")
else:
    print(f"No PNG files found in {input_dir}")

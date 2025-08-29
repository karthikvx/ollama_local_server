import os
from PIL import Image
import pytesseract

# Define input and output directories
input_dir = os.path.expanduser('~/Pictures/Screenshots')
output_dir = os.path.join(os.path.dirname(__file__), 'output-folder')
os.makedirs(output_dir, exist_ok=True)
output_md = os.path.join(output_dir, 'output.md')
output_images_dir = os.path.join(output_dir, 'images')
os.makedirs(output_images_dir, exist_ok=True)

png_files = [os.path.join(input_dir, i) for i in os.listdir(input_dir) if i.endswith('.png')]
png_files.sort()

# Open output.md in append mode if it exists, else write mode
mode = 'a' if os.path.exists(output_md) else 'w'
with open(output_md, mode) as f:
    for png in png_files:
        img_name = os.path.basename(png)
        dest_path = os.path.join(output_images_dir, img_name)
        if os.path.exists(dest_path):
            print(f"Skipping {img_name}, already processed.")
            continue
        try:
            image = Image.open(png)
            text = pytesseract.image_to_string(image)
            f.write(f"# {img_name}\n\n{text}\n\n")
            # Copy the image to output-folder/images to mark as processed
            with open(png, 'rb') as src, open(dest_path, 'wb') as dst:
                dst.write(src.read())
        except Exception as e:
            f.write(f"# {img_name}\n\nError extracting text: {e}\n\n")
print(f"Markdown file with extracted text updated: {output_md}")


import os
from PIL import Image
import pytesseract
import img2pdf

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

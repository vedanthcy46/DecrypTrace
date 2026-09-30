import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image
import numpy as np

def create_test_pdf(output_path):
    # Create colorful image
    img_size = (512, 512)
    img_data = np.random.randint(0, 256, (img_size[0], img_size[1], 3), dtype=np.uint8)
    img = Image.fromarray(img_data)
    img_path = "temp_image.png"
    img.save(img_path)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    c = canvas.Canvas(output_path, pagesize=letter)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(100, 700, "DecrypTrace Watermark Test Document")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, 670, "This document contains a test image for evaluating watermarking.")
    
    # Draw image
    c.drawImage(img_path, 0, 0, width=letter[0], height=letter[1])
    
    c.save()
    os.remove(img_path)
    print(f"Created PDF: {output_path}")

if __name__ == "__main__":
    create_test_pdf(r"c:\Users\hp victus\Desktop\DecrypTrace\validation-corpus\source-documents\test-image-doc.pdf")

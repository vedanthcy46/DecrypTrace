import os
import tempfile
import logging
import numpy as np
import fitz  # PyMuPDF
from blind_watermark import WaterMark

logger = logging.getLogger(__name__)

def embed_watermark_in_pdf(pdf_bytes: bytes, watermark_id: str) -> bytes:
    """
    Embeds a 128-bit watermark into a PDF by rendering pages as images,
    injecting the DCT watermark, and returning a new PDF composed of the images.
    """
    # 1. Parse the watermark_id (e.g. "WM-7A92ABC1") into 128 bits
    # The ID is WM- + 8 characters. We encode the 8 chars to bytes.
    wm_str = watermark_id.replace("WM-", "")
    wm_bytes = wm_str.encode('utf-8')
    
    # Pad to 16 bytes (128 bits) with null bytes
    wm_bytes = wm_bytes.ljust(16, b'\0')
    
    # Convert bytes to bits array for blind_watermark
    wm_bits = np.unpackbits(np.frombuffer(wm_bytes, dtype=np.uint8)).tolist()
    
    new_pdf = fitz.open()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Save original PDF
        in_path = os.path.join(tmpdir, "in.pdf")
        with open(in_path, "wb") as f:
            f.write(pdf_bytes)
            
        doc = fitz.open(in_path)
        
        for i in range(len(doc)):
            page = doc[i]
            # Render page to high-res image
            pix = page.get_pixmap(dpi=150)
            img_path = os.path.join(tmpdir, f"page_{i}.png")
            pix.save(img_path)
            
            # Embed watermark
            out_img_path = os.path.join(tmpdir, f"page_{i}_wm.png")
            try:
                bwm = WaterMark(password_img=1, password_wm=1)
                bwm.read_img(img_path)
                bwm.read_wm(wm_bits, mode='bit')
                bwm.embed(out_img_path)
                
                # Insert the watermarked image into the new PDF
                img_doc = fitz.open(out_img_path)
                pdf_bytes_from_img = img_doc.convert_to_pdf()
                img_pdf = fitz.open("pdf", pdf_bytes_from_img)
                new_pdf.insert_pdf(img_pdf)
                img_doc.close()
                img_pdf.close()
            except Exception as e:
                logger.error(f"Watermark embed failed on page {i}: {e}")
                # Fallback to unwatermarked page if it fails
                new_pdf.insert_pdf(doc, from_page=i, to_page=i)
                
        doc.close()
        
    return new_pdf.write()

import os
import secrets
import cv2
import numpy as np
import fitz  # PyMuPDF
from blind_watermark import WaterMark
from skimage.metrics import peak_signal_noise_ratio as psnr
from skimage.metrics import structural_similarity as ssim

def generate_wm_id():
    return "WM-" + secrets.token_hex(8).upper()

def pdf_to_image(pdf_path, page_num=0):
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    pix = page.get_pixmap(dpi=72)
    
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
    elif pix.n == 1:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    return img

def embed_watermark(img_path, wm_id, output_path):
    bwm = WaterMark(password_wm=1, password_img=1)
    bwm.read_img(img_path)
    bwm.read_wm(wm_id, mode='str')
    bwm.embed(output_path)
    return len(wm_id) * 8 # rough estimate, blind_watermark handles it internally if we provide the correct length on extract. Wait, blind_watermark mode='str' uses length of bits.

def extract_watermark(img_path, wm_len):
    bwm = WaterMark(password_wm=1, password_img=1)
    wm_extract = bwm.extract(img_path, wm_shape=wm_len, mode='str')
    return wm_extract

def create_watermarked_pdf(pdf_path, img_bgr, wm_id, output_pdf_path):
    temp_img_path = "temp_orig.png"
    temp_wm_img_path = "temp_wm.png"
    cv2.imwrite(temp_img_path, img_bgr)
    
    bwm = WaterMark(password_wm=1, password_img=1)
    bwm.read_img(temp_img_path)
    bwm.read_wm(wm_id, mode='str')
    wm_len = len(bwm.wm_bit)
    bwm.embed(temp_wm_img_path)
    
    # Calculate metrics
    orig_img = cv2.imread(temp_img_path)
    wm_img = cv2.imread(temp_wm_img_path)
    
    psnr_val = psnr(orig_img, wm_img)
    ssim_val = ssim(orig_img, wm_img, channel_axis=2)
    
    print(f"PSNR: {psnr_val:.2f} dB")
    print(f"SSIM: {ssim_val:.4f}")
    
    # Test direct extract
    bwm_test = WaterMark(password_wm=1, password_img=1)
    wm_test = bwm_test.extract(temp_wm_img_path, wm_shape=wm_len, mode='str')
    print(f"Direct Extract from PNG: {wm_test}")
    
    # Replace in PDF
    doc = fitz.open(pdf_path)
    page = doc[0]
    rect = page.rect
    
    new_doc = fitz.open()
    new_page = new_doc.new_page(width=rect.width, height=rect.height)
    new_page.insert_image(rect, filename=temp_wm_img_path)
    new_doc.save(output_pdf_path)
    
    os.remove(temp_img_path)
    os.remove(temp_wm_img_path)
    
    return wm_len

def run_tests():
    print("--- DecrypTrace Watermark Spike Test ---")
    
    wm_id = generate_wm_id()
    print(f"1. Generate Watermark ID: {wm_id} - PASS")
    
    source_pdf = r"c:\Users\hp victus\Desktop\DecrypTrace\validation-corpus\source-documents\test-image-doc.pdf"
    wm_pdf = r"c:\Users\hp victus\Desktop\DecrypTrace\scripts\test_watermarked.pdf"
    
    print("2. Extracting page image from PDF...")
    img = pdf_to_image(source_pdf)
    print("   Extracted image shape:", img.shape, "- PASS")
    
    print(f"3. Embedding watermark and saving PDF...")
    wm_len = create_watermarked_pdf(source_pdf, img, wm_id, wm_pdf)
    print(f"4. Saved watermarked PDF to {wm_pdf} - PASS")
    
    print("5. Extracting watermark from saved PDF...")
    extracted_img = pdf_to_image(wm_pdf)
    temp_extract = "temp_extract.png"
    cv2.imwrite(temp_extract, extracted_img)
    
    wm_extract = extract_watermark(temp_extract, wm_len)
    os.remove(temp_extract)
    
    print(f"   Original WM: {wm_id}")
    print(f"   Extracted WM: {wm_extract}")
    if wm_id == wm_extract:
        print("   Match: PASS")
    else:
        print("   Match: FAIL")

if __name__ == '__main__':
    run_tests()

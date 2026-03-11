import sys
import os
sys.path.insert(0, os.path.abspath(os.curdir))

from services.ocr_service import ocr_service

def test():
    image_path = 'uploads/exames/dd9e31fc790b4e7b859826c983a22ca3.jpg'
    if not os.path.exists(image_path):
        print(f"Arquivo não encontrado: {image_path}")
        return

    print(f"Testando OCR em: {image_path}")
    try:
        result = ocr_service.extract_text(image_path)
        print("--- RESULTADO ---")
        print(f"Confiança: {result['confianca']}")
        print(f"Texto extraído (primeiros 500 chars):\n{result['texto'][:500]}")
    except Exception as e:
        print(f"ERRO: {str(e)}")

if __name__ == "__main__":
    test()

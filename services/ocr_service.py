import pytesseract
import cv2
from PIL import Image
import re
import os
import base64
import tempfile
import logging
from datetime import datetime
from io import BytesIO

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        # Configurar Tesseract para português e inglês
        self.custom_config = r'--oem 3 --psm 6 -l por+eng'

    def preprocess_image(self, image):
        """Pré-processa a imagem para melhorar a qualidade do OCR"""
        try:
            # Converter para escala de cinza
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            # Aplicar filtro de redução de ruído
            denoised = cv2.medianBlur(gray, 3)

            # Melhorar contraste usando equalização de histograma
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)

            # Aplicar threshold para binarização
            _, threshold = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            return threshold

        except Exception as e:
            raise ValueError(f"Erro no pré-processamento da imagem: {str(e)}")

    def extract_text_from_pil(self, pil_image):
        """Extrai texto de um PIL Image"""
        try:
            # Converter PIL para numpy array (OpenCV)
            img_array = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

            # Pré-processar
            processed = self.preprocess_image(img_array)

            # Converter de volta para PIL
            processed_pil = Image.fromarray(processed)

            # Extrair texto
            text = pytesseract.image_to_string(processed_pil, config=self.custom_config, lang='por+eng')

            # Obter dados de confiança
            data = pytesseract.image_to_data(processed_pil, config=self.custom_config, lang='por+eng', output_type=pytesseract.Output.DICT)

            # Calcular confiança média
            confidences = [int(conf) for conf in data['conf'] if conf != '-1']
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            return {
                'texto': text.strip(),
                'confianca': round(avg_confidence, 2),
            }

        except Exception as e:
            raise ValueError(f"Erro na extração de texto: {str(e)}")

    def extract_text_from_base64(self, base64_string: str) -> dict:
        """Extrai texto de uma string base64 (imagem)."""
        try:
            # Limpar prefixo data:image/...;base64,
            if ',' in base64_string:
                base64_string = base64_string.split(',', 1)[1]

            img_data = base64.b64decode(base64_string)
            pil_image = Image.open(BytesIO(img_data))

            return self.extract_text_from_pil(pil_image)
        except Exception as e:
            logger.error(f"Erro OCR base64: {e}")
            return {'texto': '', 'confianca': 0, 'erro': str(e)}

    def extract_text(self, image_path):
        """Extrai texto da imagem usando OCR (caminho de arquivo)"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("Não foi possível ler a imagem")

            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            return self.extract_text_from_pil(pil_image)
        except Exception as e:
            raise ValueError(f"Erro na extração de texto: {str(e)}")

    def parse_medical_data(self, text):
        """Analisa o texto extraído e identifica dados médicos estruturados"""
        structured_data = {
            'tipo_exame': None,
            'valores': [],
            'parametros': [],
            'data_exame': None,
            'paciente_info': {},
            'unidades': [],
            'valores_referencia': []
        }

        lines = text.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detectar tipo de exame
            if re.search(r'hemograma|hemograma completo|blood count', line.lower()):
                structured_data['tipo_exame'] = 'hemograma'
                current_section = 'hemograma'
            elif re.search(r'colesterol|triglicerídeos|lipidograma', line.lower()):
                structured_data['tipo_exame'] = 'lipidograma'
                current_section = 'lipidograma'
            elif re.search(r'glicemia|glucose|açúcar no sangue', line.lower()):
                structured_data['tipo_exame'] = 'glicemia'
                current_section = 'glicemia'
            elif re.search(r'hemoglobina|hb|hematocrito|ht', line.lower()):
                current_section = 'hemograma'

            # Extrair valores numéricos com unidades
            value_pattern = r'(\d+(?:[.,]\d+)?)\s*([a-zA-Z%]+)'
            matches = re.findall(value_pattern, line)

            for match in matches:
                valor, unidade = match
                valor = valor.replace(',', '.')

                try:
                    valor_num = float(valor)
                    structured_data['valores'].append({
                        'valor': valor_num,
                        'unidade': unidade.lower(),
                        'linha': line,
                        'secao': current_section
                    })
                except ValueError:
                    continue

            # Extrair parâmetros
            param_patterns = [
                r'^([A-Z][a-zA-Z\s]+?)(?:\s*\d|\s*$)',
                r'([A-Z][a-zA-Z\s]+?)(?=\s+\d)',
            ]

            for pattern in param_patterns:
                matches = re.findall(pattern, line)
                for match in matches:
                    param = match.strip()
                    if len(param) > 2 and not any(char.isdigit() for char in param):
                        if param not in structured_data['parametros']:
                            structured_data['parametros'].append(param)

            # Extrair valores de referência
            ref_pattern = r'(\d+(?:[.,]\d+)?\s*[-–]\s*\d+(?:[.,]\d+)?|\d+(?:[.,]\d+)?\s*[a-zA-Z]+\s*[-–]\s*\d+(?:[.,]\d+)?)'
            ref_matches = re.findall(ref_pattern, line)
            for match in ref_matches:
                if match not in structured_data['valores_referencia']:
                    structured_data['valores_referencia'].append(match)

            # Extrair data
            if not structured_data['data_exame']:
                date_patterns = [
                    r'(\d{2}[/-]\d{2}[/-]\d{4})',
                    r'(\d{2}[/-]\d{2}[/-]\d{2})',
                    r'(\d{4}[/-]\d{2}[/-]\d{2})'
                ]
                for pattern in date_patterns:
                    date_match = re.search(pattern, line)
                    if date_match:
                        structured_data['data_exame'] = date_match.group(1)
                        break

        return structured_data

    def process_exam_image(self, image_path):
        """Processa uma imagem de exame completo: OCR + análise de dados"""
        try:
            result = self.extract_text(image_path)
            structured = self.parse_medical_data(result['texto'])
            return {
                "status": "success",
                "texto_extraido": result['texto'],
                "confianca": result['confianca'],
                "dados_estruturados": structured,
                "processado_em": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Erro process_exam_image: {e}")
            return {
                "status": "error",
                "message": str(e),
                "texto_extraido": "",
                "confianca": 0,
                "dados_estruturados": {},
                "processado_em": datetime.utcnow().isoformat()
            }

    def process_base64_image(self, base64_string: str):
        """Processa uma imagem em base64: OCR + análise de dados"""
        try:
            result = self.extract_text_from_base64(base64_string)
            if result.get('erro'):
                return {
                    "status": "error",
                    "message": result['erro'],
                    "texto_extraido": "",
                    "confianca": 0,
                    "dados_estruturados": {},
                }
            structured = self.parse_medical_data(result['texto'])
            return {
                "status": "success",
                "texto_extraido": result['texto'],
                "confianca": result['confianca'],
                "dados_estruturados": structured,
                "processado_em": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Erro process_base64_image: {e}")
            return {
                "status": "error",
                "message": str(e),
                "texto_extraido": "",
                "confianca": 0,
                "dados_estruturados": {},
                "processado_em": datetime.utcnow().isoformat()
            }


# Import numpy para o método extract_text_from_pil
import numpy as np

# Instância global do serviço
ocr_service = OCRService()

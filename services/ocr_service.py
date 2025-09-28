import pytesseract
import cv2
import numpy as np
from PIL import Image
import json
import re
from datetime import datetime
import os

class OCRService:
    def __init__(self):
        # Configurar Tesseract para português e inglês
        self.custom_config = r'--oem 3 --psm 6 -l por+eng'

    def preprocess_image(self, image_path):
        """Pré-processa a imagem para melhorar a qualidade do OCR"""
        try:
            # Ler imagem
            image = cv2.imread(image_path)

            if image is None:
                raise ValueError("Não foi possível ler a imagem")

            # Converter para escala de cinza
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

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

    def extract_text(self, image_path):
        """Extrai texto da imagem usando OCR"""
        try:
            # Pré-processar imagem
            processed_image = self.preprocess_image(image_path)

            # Converter para PIL Image para pytesseract
            pil_image = Image.fromarray(processed_image)

            # Extrair texto
            text = pytesseract.image_to_string(pil_image, config=self.custom_config, lang='por+eng')

            # Obter dados de confiança
            data = pytesseract.image_to_data(pil_image, config=self.custom_config, lang='por+eng', output_type=pytesseract.Output.DICT)

            # Calcular confiança média
            confidences = [int(conf) for conf in data['conf'] if conf != '-1']
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            return {
                'texto': text.strip(),
                'confianca': round(avg_confidence, 2),
                'dados_brutos': data
            }

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

                # Tentar converter para float
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

            # Extrair parâmetros (nomes dos exames)
            param_patterns = [
                r'^([A-Z][a-zA-Z\s]+?)(?:\s*\d|\s*$)',  # Linha que começa com palavra capitalizada
                r'([A-Z][a-zA-Z\s]+?)(?=\s+\d)',  # Palavra antes de número
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
            # Extrair texto
            ocr_result = self.extract_text(image_path)

            # Analisar dados médicos
            structured_data = self.parse_medical_data(ocr_result['texto'])

            return {
                'texto_extraido': ocr_result['texto'],
                'confianca': ocr_result['confianca'],
                'dados_estruturados': structured_data,
                'dados_brutos_ocr': ocr_result['dados_brutos'],
                'status': 'concluido',
                'processado_em': datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                'erro': str(e),
                'status': 'erro',
                'processado_em': datetime.utcnow().isoformat()
            }

# Instância global do serviço
ocr_service = OCRService()
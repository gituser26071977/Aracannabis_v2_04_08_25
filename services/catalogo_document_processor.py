"""
Processador de documentos para catálogo de produtos de cannabis
Suporta: PDF, XLSX, CSV, DOCX, TXT
"""
import os
import re
import json
import logging
import tempfile
from typing import Dict, List, Any, Optional
from datetime import datetime

import pandas as pd
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Processa diferentes tipos de documentos para extrair dados de produtos"""
    
    ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls', 'csv', 'docx', 'doc', 'txt'}
    
    def __init__(self):
        self.extracted_data = []
        
    def allowed_file(self, filename: str) -> bool:
        """Verifica se a extensão do arquivo é permitida"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS
    
    def process_file(self, filepath: str, filename: str) -> Dict[str, Any]:
        """
        Processa um arquivo baseado em sua extensão
        
        Returns:
            Dict com dados extraídos e metadados
        """
        ext = filename.rsplit('.', 1)[1].lower()
        
        try:
            if ext in ['xlsx', 'xls']:
                return self._process_excel(filepath, filename)
            elif ext == 'csv':
                return self._process_csv(filepath, filename)
            elif ext == 'pdf':
                return self._process_pdf(filepath, filename)
            elif ext in ['docx', 'doc']:
                return self._process_word(filepath, filename)
            elif ext == 'txt':
                return self._process_txt(filepath, filename)
            else:
                return {"error": f"Formato não suportado: {ext}"}
        except Exception as e:
            logger.error(f"Erro ao processar arquivo {filename}: {str(e)}")
            return {"error": str(e)}
    
    def _process_excel(self, filepath: str, filename: str) -> Dict[str, Any]:
        """Processa arquivo Excel"""
        try:
            # Lê todas as abas
            xls = pd.ExcelFile(filepath)
            all_data = []
            
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(filepath, sheet_name=sheet_name)
                # Converte NaN para None
                df = df.where(pd.notnull(df), None)
                
                # Tenta identificar se é uma aba de produtos
                if self._is_product_sheet(df):
                    products = self._parse_dataframe_to_products(df, filename, sheet_name)
                    all_data.extend(products)
            
            return {
                "tipo": "excel",
                "filename": filename,
                "total_sheets": len(xls.sheet_names),
                "produtos_extraidos": len(all_data),
                "dados": all_data
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar Excel: {str(e)}")
            return {"error": f"Erro no Excel: {str(e)}"}
    
    def _process_csv(self, filepath: str, filename: str) -> Dict[str, Any]:
        """Processa arquivo CSV"""
        try:
            # Tenta diferentes encodings
            encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(filepath, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                return {"error": "Não foi possível decodificar o CSV"}
            
            df = df.where(pd.notnull(df), None)
            products = self._parse_dataframe_to_products(df, filename)
            
            return {
                "tipo": "csv",
                "filename": filename,
                "produtos_extraidos": len(products),
                "dados": products
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar CSV: {str(e)}")
            return {"error": f"Erro no CSV: {str(e)}"}
    
    def _process_pdf(self, filepath: str, filename: str) -> Dict[str, Any]:
        """Processa arquivo PDF usando OCR e extração de texto"""
        try:
            # Tenta extrair texto direto primeiro
            texto = self._extract_pdf_text(filepath)
            
            # Se não conseguir texto suficiente, usa OCR
            if len(texto) < 100:
                texto = self._extract_pdf_with_ocr(filepath)
            
            # Usa IA para estruturar os dados
            produtos = self._parse_text_to_products(texto, filename)
            
            return {
                "tipo": "pdf",
                "filename": filename,
                "texto_extraido": texto[:2000] + "..." if len(texto) > 2000 else texto,
                "produtos_extraidos": len(produtos),
                "dados": produtos
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar PDF: {str(e)}")
            return {"error": f"Erro no PDF: {str(e)}"}
    
    def _process_word(self, filepath: str, filename: str) -> Dict[str, Any]:
        """Processa arquivo Word (DOCX)"""
        try:
            import docx2txt
            
            texto = docx2txt.process(filepath)
            produtos = self._parse_text_to_products(texto, filename)
            
            return {
                "tipo": "docx",
                "filename": filename,
                "texto_extraido": texto[:2000] + "..." if len(texto) > 2000 else texto,
                "produtos_extraidos": len(produtos),
                "dados": produtos
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar DOCX: {str(e)}")
            return {"error": f"Erro no DOCX: {str(e)}"}
    
    def _process_txt(self, filepath: str, filename: str) -> Dict[str, Any]:
        """Processa arquivo de texto simples"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                texto = f.read()
            
            produtos = self._parse_text_to_products(texto, filename)
            
            return {
                "tipo": "txt",
                "filename": filename,
                "texto_extraido": texto[:2000] + "..." if len(texto) > 2000 else texto,
                "produtos_extraidos": len(produtos),
                "dados": produtos
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar TXT: {str(e)}")
            return {"error": f"Erro no TXT: {str(e)}"}
    
    def _is_product_sheet(self, df: pd.DataFrame) -> bool:
        """Verifica se o DataFrame parece ser uma planilha de produtos"""
        if df.empty or len(df.columns) < 3:
            return False
        
        colunas = [str(c).lower() for c in df.columns]
        
        # Palavras-chave que indicam produtos de cannabis
        keywords = ['produto', 'nome', 'marca', 'cbd', 'thc', 'canabidiol', 'óleo', 'cápsula', 
                   'concentração', 'apresentação', 'laboratório', 'código', 'preço']
        
        matches = sum(1 for k in keywords if any(k in c for c in colunas))
        return matches >= 2
    
    def _parse_dataframe_to_products(self, df: pd.DataFrame, filename: str, sheet_name: str = None) -> List[Dict]:
        """Converte DataFrame em lista de produtos normalizados"""
        products = []
        
        # Normaliza nomes das colunas
        col_map = self._map_columns(df.columns)
        
        for idx, row in df.iterrows():
            try:
                product = self._extract_product_from_row(row, col_map, filename, sheet_name, idx)
                if product:
                    products.append(product)
            except Exception as e:
                logger.warning(f"Erro ao processar linha {idx}: {str(e)}")
                continue
        
        return products
    
    def _map_columns(self, columns) -> Dict[str, str]:
        """Mapeia nomes de colunas para campos padronizados"""
        col_map = {}
        
        mapping = {
            'nome': ['nome', 'produto', 'product', 'nome_comercial', 'descrição', 'descricao', 'descrição do produto'],
            'marca': ['marca', 'brand', 'fabricante', 'laboratório', 'laboratorio', 'empresa'],
            'categoria': ['categoria', 'tipo', 'type', 'category', 'apresentação', 'apresentacao'],
            'cbd_mg': ['cbd', 'cbd mg', 'canabidiol', 'cbd (mg)', 'cbd mg/ml', 'concentração cbd'],
            'thc_mg': ['thc', 'thc mg', 'tetrahidrocanabinol', 'thc (mg)', 'thc mg/ml', 'concentração thc'],
            'cbg_mg': ['cbg', 'cbg mg'],
            'volume': ['volume', 'volume ml', 'ml', 'tamanho', 'frasco'],
            'quantidade': ['quantidade', 'qtd', 'cápsulas', 'capsulas', 'cps'],
            'via': ['via', 'administração', 'via de administração', 'uso'],
            'preco': ['preço', 'preco', 'valor', 'price', 'custo', 'r$'],
            'indicacoes': ['indicações', 'indicacoes', 'indicação', 'uso indicado', 'finalidade'],
            'composicao': ['composição', 'composicao', 'ingredientes', 'fórmula'],
            'registro': ['registro', 'anvisa', 'registro anvisa', 'registro ms'],
            'quimiotipo': ['quimiotipo', 'tipo', 'chemotype']
        }
        
        for col in columns:
            col_lower = str(col).lower().strip()
            for field, variations in mapping.items():
                if any(v in col_lower for v in variations):
                    col_map[field] = col
                    break
        
        return col_map
    
    def _extract_product_from_row(self, row, col_map: Dict, filename: str, sheet_name: str = None, row_idx: int = 0) -> Optional[Dict]:
        """Extrai dados de produto de uma linha do DataFrame"""
        product = {
            '_origem': {
                'arquivo': filename,
                'aba': sheet_name,
                'linha': row_idx
            }
        }
        
        # Extrai campos mapeados
        if 'nome' in col_map:
            product['nome'] = str(row[col_map['nome']]) if row[col_map['nome']] else None
        
        if 'marca' in col_map:
            product['marca'] = str(row[col_map['marca']]) if row[col_map['marca']] else None
        
        if 'categoria' in col_map:
            product['categoria'] = str(row[col_map['categoria']]) if row[col_map['categoria']] else None
        
        # Extrai valores numéricos
        for field in ['cbd_mg', 'thc_mg', 'cbg_mg', 'volume', 'preco']:
            if field in col_map:
                val = row[col_map[field]]
                product[field] = self._parse_numeric(val)
        
        # Outros campos
        if 'via' in col_map:
            product['via_administracao'] = str(row[col_map['via']]) if row[col_map['via']] else None
        
        if 'indicacoes' in col_map:
            product['indicacoes'] = str(row[col_map['indicacoes']]) if row[col_map['indicacoes']] else None
        
        if 'composicao' in col_map:
            product['composicao'] = str(row[col_map['composicao']]) if row[col_map['composicao']] else None
        
        if 'registro' in col_map:
            product['registro_anvisa'] = str(row[col_map['registro']]) if row[col_map['registro']] else None
        
        if 'quimiotipo' in col_map:
            product['quimiotipo'] = str(row[col_map['quimiotipo']]) if row[col_map['quimiotipo']] else None
        
        # Determina quimiotipo se não informado
        if 'quimiotipo' not in product and ('cbd_mg' in product or 'thc_mg' in product):
            product['quimiotipo'] = self._determine_chemotype(
                product.get('cbd_mg', 0) or 0,
                product.get('thc_mg', 0) or 0
            )
        
        # Calcula razão CBD:THC
        if 'cbd_mg' in product and 'thc_mg' in product:
            product['razao_cbd_thc'] = self._calculate_ratio(
                product.get('cbd_mg', 0),
                product.get('thc_mg', 0)
            )
        
        # Só retorna se tiver nome ou marca
        if product.get('nome') or product.get('marca'):
            return product
        
        return None
    
    def _parse_numeric(self, value) -> Optional[float]:
        """Converte valor para número"""
        if pd.isna(value) or value is None:
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        # Remove caracteres não numéricos exceto ponto e vírgula
        if isinstance(value, str):
            # Substitui vírgula por ponto
            value = value.replace(',', '.')
            # Remove tudo exceto números e ponto
            value = re.sub(r'[^\d.]', '', value)
            try:
                return float(value) if value else None
            except ValueError:
                return None
        
        return None
    
    def _determine_chemotype(self, cbd: float, thc: float) -> str:
        """Determina o quimiotipo baseado nas concentrações"""
        if thc > 0 and cbd > 0:
            return "Tipo II (THC+CBD)"
        elif thc > 0 and cbd == 0:
            return "Tipo I (THC)"
        elif cbd > 0 and thc == 0:
            return "Tipo III (CBD)"
        elif cbd > 0 and thc > 0 and cbg > 0:
            return "Tipo IV (CBG dominante)"
        else:
            return "Não classificado"
    
    def _calculate_ratio(self, cbd: Optional[float], thc: Optional[float]) -> str:
        """Calcula razão CBD:THC"""
        if not cbd or not thc or thc == 0:
            return None
        
        ratio = cbd / thc
        if ratio >= 10:
            return f"{int(ratio)}:1"
        elif ratio >= 1:
            return f"{ratio:.1f}:1"
        else:
            inverse = 1 / ratio
            return f"1:{int(inverse)}" if inverse == int(inverse) else f"1:{inverse:.1f}"
    
    def _extract_pdf_text(self, filepath: str) -> str:
        """Extrai texto de PDF usando PyPDF2 ou pdfplumber"""
        try:
            import pdfplumber
            
            text = ""
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            return text
            
        except Exception as e:
            logger.warning(f"pdfplumber falhou: {str(e)}, tentando PyPDF2")
            
            try:
                import PyPDF2
                
                text = ""
                with open(filepath, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                
                return text
                
            except Exception as e2:
                logger.error(f"PyPDF2 também falhou: {str(e2)}")
                return ""
    
    def _extract_pdf_with_ocr(self, filepath: str) -> str:
        """Extrai texto de PDF usando OCR (para PDFs scaneados)"""
        try:
            from pdf2image import convert_from_path
            import pytesseract
            
            # Converte PDF para imagens
            images = convert_from_path(filepath, dpi=200)
            
            text = ""
            for image in images:
                text += pytesseract.image_to_string(image, lang='por') + "\n"
            
            return text
            
        except Exception as e:
            logger.error(f"OCR falhou: {str(e)}")
            return ""
    
    def _parse_text_to_products(self, text: str, filename: str) -> List[Dict]:
        """
        Usa IA para extrair produtos de texto não estruturado
        """
        try:
            from services.ai_agents import ai_manager
            
            system_prompt = """Você é um especialista em extrair dados de produtos de cannabis medicinal de textos.
            
            Extraia TODOS os produtos mencionados no texto e retorne em formato JSON.
            
            Para cada produto, extraia:
            - nome: nome completo do produto
            - nome_comercial: nome comercial se diferente
            - marca: marca/laboratório fabricante
            - categoria: Óleo, Cápsula, Floral, Tópico, etc
            - cbd_mg: concentração de CBD em mg/ml ou mg/cápsula (número)
            - thc_mg: concentração de THC em mg/ml ou mg/cápsula (número)
            - cbg_mg: concentração de CBG se mencionada
            - volume_ml: volume em ml
            - quantidade_cps: quantidade de cápsulas se aplicável
            - via_administracao: Via de administração
            - indicacoes: indicações terapêuticas (texto)
            - composicao: composição completa
            - registro_anvisa: número de registro
            - preco: preço se mencionado
            - quimiotipo: Tipo I, II, III, IV se identificável
            
            Retorne um JSON no formato:
            {
                "produtos": [
                    {
                        "nome": "...",
                        "marca": "...",
                        ...
                    }
                ]
            }
            
            Se não encontrar produtos, retorne {"produtos": []}"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extraia produtos deste texto de catálogo:\n\n{text[:8000]}"}
            ]
            
            response = ai_manager.chat_completion(
                messages=messages,
                temperature=0.1,
                max_tokens=4000
            )
            
            content = response.get('content', '')
            
            # Limpa o JSON
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
            
            data = json.loads(content.strip())
            produtos = data.get('produtos', [])
            
            # Adiciona metadados de origem
            for p in produtos:
                p['_origem'] = {
                    'arquivo': filename,
                    'tipo_extracao': 'ia_texto',
                    'data_extracao': datetime.now().isoformat()
                }
                # Calcula quimiotipo e razão
                if 'cbd_mg' in p and 'thc_mg' in p:
                    p['razao_cbd_thc'] = self._calculate_ratio(
                        p.get('cbd_mg'),
                        p.get('thc_mg')
                    )
            
            return produtos
            
        except Exception as e:
            logger.error(f"Erro ao parsear texto com IA: {str(e)}")
            return []


# Instância global
document_processor = DocumentProcessor()
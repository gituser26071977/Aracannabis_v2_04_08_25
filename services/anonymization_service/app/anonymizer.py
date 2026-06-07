import re
import spacy
from typing import List, Tuple
from app.models import AnonymizationMap
from app.crypto import CryptoManager
import logging

# Configuração de Log Seguro (apenas metadados)
logger = logging.getLogger(__name__)

class Anonymizer:
    """Implementa a lógica de regex + NER + tokenização reversível."""

    def __init__(self, key: str = None):
        self.crypto_manager = CryptoManager(key.encode() if key else None)
        self.nlp = None  # Lazy loading do spacy

        # Patterns de Regex
        # CPF (simples)
        self.patterns = {
            "CPF": r"\d{3}\.\d{3}\.\d{3}-\d{2}",
            "PHONE": r"\(?\d{2}\)?\s?\d{4,5}-?\d{4}",
            "EMAIL": r"[a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}",
            "DATE_ISO": r"\d{4}-\d{2}-\d{2}",
            "DATE_PT": r"\d{2}/\d{2}/\d{4}",
            "PRONTUARIO": r"[Pp]rontu[aá]rio\s?\d+", # Exemplo simples, ajustar conforme padrão do cliente
            "CID": r"[A-Z]\d{2}(?:\.\d{1,2})?" # Código CID (pode ser útil manter se não identificar o paciente) - Manter por enquanto, avaliando risco
        }
    
    def load_nlp(self):
        if not self.nlp:
            try:
                # Tentar modelo grande, fallback para pequeno se não existir
                self.nlp = spacy.load("pt_core_news_lg") 
                logger.info("Modelo spaCy pt_core_news_lg carregado com sucesso.")
            except ImportError:
                print("⚠️  Modelo spaCy grande não encontrado, tentando 'sm'.")
                try:
                     self.nlp = spacy.load("pt_core_news_sm")
                     logger.warning("Modelo spaCy pt_core_news_sm carregado (menor precisão).")
                except ImportError:
                    print("❌  Nenhum modelo spaCy encontrado. Instale 'pt_core_news_sm' ou 'pt_core_news_lg'.")
                    raise

    def anonymize_text(self, text: str, consultation_id: int, db_session) -> Tuple[str, List[int], float]:
        """
        Substitui PII por tokens reversíveis e salva no banco.
        Retorna: (texto_anonimizado, lista_ids_mapa, risk_score)
        """
        self.load_nlp()
        
        anonymized_text = text
        maps_created = [] # Lista de (token, encrypted_original, entity_type)

        def replace_match(match, token_type):
            original = match.group(0)
            # Gerar token único para essa sessão/consulta? 
            # Para reversibilidade simples, vamos usar TOKEN_SEQUENCIAL por tipo
            # Na prática real, usaríamos UUID ou hash para evitar colisão entre consultas, 
            # mas aqui o escopo é por request.
            # Vamos gerar um placeholder com hash curto do original para consistência dentro do mesmo texto
            import hashlib
            short_hash = hashlib.md5(original.encode()).hexdigest()[:6].upper()
            token = f"[{token_type}_{short_hash}]"
            
            # Verificar se já mapeamos esse token NESTA sessão (para não duplicar inserts)
            for m in maps_created:
                if m['token'] == token:
                    return token
            
            encrypted_val = self.crypto_manager.encrypt(original)
            maps_created.append({
                "token": token,
                "encrypted_original": encrypted_val,
                "entity_type": token_type,
                "original_len": len(original) # Para calculo de risco (opcional)
            })
            return token

        # 1. Regex Pass
        for label, pattern in self.patterns.items():
            anonymized_text = re.sub(pattern, lambda m: replace_match(m, label), anonymized_text)
            
        # 2. NER Pass (SpaCy)
        # O texto já pode ter tokens de regex. SpaCy pode se confundir com colchetes, mas no geral ok.
        doc = self.nlp(anonymized_text)
        
        # Entidades NER para mascarar
        target_ents = ["PER", "LOC", "ORG"] # Data já coberta por regex, mas NER tb pega formatos extensos. Manter 'MISC' se necessário.
        # Spacy pt usa: PER (Person), LOC (Location), ORG (Organization)
        
        # Iterar reverso para não quebrar indices ao substituir strings
        # Mas como estamos substituindo no texto original (str), e spaCy trabalha com offsets...
        # A estratégia segura é:
        # Achar todas as entidades, converter para (start, end, text, label)
        # Depois substituir no texto base, ajustando offsets?
        # Ou mais simples: substituir uma a uma e reprocessar? Reprocessar é lento.
        
        # Simples: Extrair spans que NÃO colidem com tokens já existentes (regex)
        # Como já substituímos regex, o texto atual tem [CPF_HASH]. O NER provavelmente ignorará isso ou classificará como MISC.
        
        entities_to_replace = []
        for ent in doc.ents:
            if ent.label_ in target_ents:
                # Verificar se é um token já criado (começa com [ e termina com ])
                if ent.text.startswith("[") and ent.text.endswith("]"):
                    continue
                entities_to_replace.append(ent)
                
        # Substituir no texto (string replace simples pode ser perigoso se houver repetições não entidades)
        # Melhor usar re.sub com word boundary ou similar, ou os offsets do spacy
        # Para simplificar aqui e evitar complexidade de offset drift:
        count_ner = 0
        for ent in entities_to_replace:
             # Usar o texto exato da entidade
             original = ent.text
             # Pode haver falsos positivos, mas em saúde: better safe than sorry.
             
             import hashlib
             short_hash = hashlib.md5(original.encode()).hexdigest()[:6].upper()
             token = f"[{ent.label_}_{short_hash}]"
             
             # Check duplicata
             exists = False
             for m in maps_created:
                 if m['token'] == token:
                     exists = True
                     break
             
             if not exists:
                 encrypted_val = self.crypto_manager.encrypt(original)
                 maps_created.append({
                    "token": token,
                    "encrypted_original": encrypted_val,
                    "entity_type": ent.label_
                 })
             
             # Replace first occurrence that is not already tokenized? 
             # Simples replace global do texto da entidade pelo token
             # Cuidado: "Maria" e "Maria Silva". Se substituir "Maria", quebra "Maria Silva".
             # Ideal: ordernar entidades por tamanho (decrescente) antes de substituir.
             pass 

        # Re-aplicar substituição baseada nos mapas gerados pelo NER
        # Ordenar por tamanho do valor original decrescente para evitar substituição parcial indevida
        # Mas como não temos o original fácil aqui (está criptografado), vamos usar o texto da entidade capturada.
        # Refazendo ciclo NER de forma mais robusta:
        
        # Recomeçar NER no texto já regex-ed
        doc = self.nlp(anonymized_text)
        new_text = list(anonymized_text) # Mutável char array
        # Criar lista de intervalos para mascarar
        mask_intervals = []
        
        for ent in doc.ents:
             if ent.label_ in target_ents: 
                # Verificar overlap com tokens regex (que são [..])
                # Tokens regex são fáceis de identificar.
                start = ent.start_char
                end = ent.end_char
                span_text = anonymized_text[start:end]
                
                if "[" in span_text and "]" in span_text:
                    continue # Já é token
                
                import hashlib
                short_hash = hashlib.md5(span_text.encode()).hexdigest()[:6].upper()
                token = f"[{ent.label_}_{short_hash}]"
                
                # Armazenar mapa
                encrypted_val = self.crypto_manager.encrypt(span_text)
                # Evitar duplicar no banco se já existir na lista
                if not any(m['token'] == token for m in maps_created):
                    maps_created.append({
                        "token": token,
                        "encrypted_original": encrypted_val,
                        "entity_type": ent.label_
                    })
                
                mask_intervals.append((start, end, token))
        
        # Aplicar substituição de trás para frente para manter índices
        mask_intervals.sort(key=lambda x: x[0], reverse=True)
        
        final_text = anonymized_text
        for start, end, token in mask_intervals:
            final_text = final_text[:start] + token + final_text[end:]
            
        # 3. Persistir mapas
        saved_ids = []
        for m in maps_created:
            db_map = AnonymizationMap(
                request_id=consultation_id, # Usando consultation_id como request_id temporariamente ou 0
                token=m['token'],
                original_value_encrypted=m['encrypted_original'],
                entity_type=m['entity_type'],
                encryption_key_id="DEFAULT" # Poderia vir do CryptoManager
            )
            db_session.add(db_map)
            # Flush para pegar ID?
        
        db_session.commit()
        # Recarregar para pegar IDs (se precisasse retornar ids exatos, mas aqui retornamos count ou ids se tiver)
        # Simplificação: commit e query IDs or just IDs if flush works.
        
        # Risco Score (0 a 1)
        risk = 0.0
        if re.search(self.patterns['CPF'], final_text): risk += 0.4
        if re.search(self.patterns['EMAIL'], final_text): risk += 0.2
        
        # 4. Refinamento de Risco com LLM Local (Obrigatório para VPS modesto)
        try:
            llm_risk = self.check_residual_risk_local(final_text)
            risk = max(risk, llm_risk)
        except Exception as e:
            logger.warning(f"Falha ao checar risco com LLM local: {e}")
            
        return final_text, [0], round(risk, 2)

    def check_residual_risk_local(self, text: str) -> float:
        """Usa Ollama local (qwen3:1.7b) para avaliar se ainda há dados sensíveis."""
        import requests
        import os
        
        ollama_url = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
        model = os.getenv("ANONYMIZATION_AUDIT_MODEL", "qwen3:1.7b")
        
        prompt = f"""
        Analise o texto médico abaixo. Ele foi anonimizado (dados trocados por tokens como [PER_...]).
        Responda APENAS com um número de 0.0 a 1.0 representando o risco de ainda haver dados identificáveis reais (nomes, endereços, contatos).
        0.0 = Totalmente limpo.
        1.0 = Dados reais detectados.
        
        TEXTO:
        {text[:1000]}
        
        RISCO (0.0 a 1.0):
        """
        
        try:
            resp = requests.post(f"{ollama_url}/api/generate", json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.0}
            }, timeout=5.0)
            
            if resp.status_code == 200:
                result = resp.json().get('response', '0.0').strip()
                # Tentar extrair o número
                import re
                match = re.search(r"(\d\.\d)", result)
                if match:
                    return float(match.group(1))
            return 0.1 # Risco baixo por padrão se processado
        except:
            return 0.2 # Risco moderado se falhar
    
    def rehydrate_text(self, anonymized_text: str, consultation_id: int, db_session) -> str:
        """
        Reverte a anonimização usando os mapas salvos.
        """
        # Buscar todos os mapas deste request/consulta
        maps = db_session.query(AnonymizationMap).filter_by(request_id=consultation_id).all()
        
        restored_text = anonymized_text
        for m in maps:
            try:
                original = self.crypto_manager.decrypt(m.original_value_encrypted)
                restored_text = restored_text.replace(m.token, original)
            except Exception as e:
                logger.error(f"Erro ao descriptografar token {m.token}: {e}")
                # Manter token em caso de falha de criptografia
                
        return restored_text

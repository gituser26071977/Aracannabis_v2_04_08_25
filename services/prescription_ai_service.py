import json
import logging
from typing import Dict, Any, List
from models import Produto, Dosagem
from services.ai_agents import AIProviderManager

logger = logging.getLogger(__name__)

class PrescriptionAIService:
    
    def __init__(self):
        # Utilizar o factory de LLM padronizado da plataforma
        self.ai_manager = AIProviderManager()

    def process_free_text(self, text: str, modo_consultor: bool) -> List[Dict[str, Any]]:
        """
        Recebe um texto livre ditado/digitado pelo médico e retorna uma lista formatada
        de medicamentos e posologias sugeridas.
        
        Se 'modo_consultor' for True, a Inteligência Artificial atuará sugerindo/corrigindo 
        melhores concentrações baseando-se nas diretrizes canabinoides, caso contrário ela 
        atuará como um parser "burro" (apenas extrai e formata o que o médico ditou).
        """
        
        if not text or len(text.strip()) < 5:
            return []

        # Buscar catálogo básico de produtos (CBD, THC, etc) do banco para referenciar (se no modo consultor)
        catalogo = ""
        if modo_consultor:
            produtos = Produto.query.filter_by(status='ativo').limit(20).all()
            if produtos:
                catalogo = "Catálogo disponivel para sugestao de base:\n" + "\n".join([f"- {p.nome} (CBD: {p.concentracao_y}mg, THC: {p.concentracao_x}mg)" for p in produtos])
            else:
                catalogo = "Use CBD e THC genéricos com concentrações habituais de mercado (Ex: 5%, 10%)."
                
        system_prompt = self._build_system_prompt(modo_consultor, catalogo)
        user_prompt = f"Converta ou monte a prescricao baseada na interacao a seguir:\n\n{text}"

        try:
            response = self.ai_manager.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            response_str = response.get('content', '')
            
            # Limpar formatação residual do LLM (Markdown blocos) se houver
            response_str = response_str.replace('```json', '').replace('```', '').strip()
            
            data = json.loads(response_str)
            
            if isinstance(data, dict):
                return {
                    "medicamentos": data.get("medicamentos", []),
                    "exames": data.get("exames", [])
                }
            elif isinstance(data, list):
                return {
                    "medicamentos": data,
                    "exames": []
                }
            
            return {"medicamentos": [], "exames": []}
            
        except Exception as e:
            logger.error(f"Erro no modelo de IA ao processar prescricao: {str(e)}")
            # Retorna um fallback amigável do texto livre caso a IA ou a conta da API falhe
            return [{
                "nome_medicamento": "Prescriçao via IA Falhou (Erro de Provedor)",
                "posologia_texto": text[:50] + "...",
                "via_administracao": "Oral",
                "instrucoes": "Revise o texto digitado."
            }]

    def _build_system_prompt(self, modo_consultor: bool, catalogo: str) -> str:
        base = """Você é um assistente de extração clínica JSON. 
Seu DEVER ABSOLUTO é retornar um JSON válido (e APENAS o JSON).
Formato exato de resposta:
{
  "medicamentos": [
    {
      "nome_medicamento": "Nome do remédio",
      "posologia_texto": "X gotas de manha, Y gotas a noite",
      "gotas_por_dose": 0, // Número inteiro (ex: 5 se bebe 5 gotas). Se for variavel (5 manha e 10 noite), coloque uma media ou a menor
      "frequencia_diaria": 1, // Inteiro: Quantas vezes ao dia tomará (1, 2, 3 ou 4)
      "concentracao_cbd": 0.0, // Float: mg/ml de CBD no produto (0.0 se não souber)
      "concentracao_thc": 0.0, // Float: mg/ml de THC no produto (0.0 se nãp souber)
      "via_administracao": "Oral", // Ou Tópica, Inalatória...
      "instrucoes": "Restrições de uso, como tomar após alimento e afins"
    }
  ],
  "exames": [
    "Hemograma",
    "TGO",
    "TGP"
  ]
}
Ao analisar texto, se o usuário solicitar exames de sangue ou similares, extraia-os para a lista 'exames'.
"""
        if modo_consultor:
            base += """
Voce ESTÁ MODO CONSULTOR ON. O médico digitou algumas notas vagas ou sintomas do paciente (Ex: Ansiedade forte a noite e Insonia). 
Sua função é LEVANTAR uma proposta terapêutica de Canabinoides e preencher o JSON com dosagens progressivas clássicas de medicina endocanabinoide (Ex: Iniciar com CBD Full Spectrum x gotas e óleo rico em THC de noite etc).
Utilize o seguinte catálogo de produtos se disponível para sugerir o rotulo mais adequado: 
""" + catalogo
        else:
            base += """
Voce ESTÁ MODO FORMATAÇÃO OFF. O médico apenas quer que você escaneie o que ele ditou/digitou de forma bagunçada e transcreva rigorosamente isso dividindo nos campos do JSON.
NÃO sugira, NÃO altere a miligramagem e NÃO invente remédios que o médico não tenha falado explicitamente. Apenas seja um formatador NLP de texto para JSON estruturado.
"""
        return base

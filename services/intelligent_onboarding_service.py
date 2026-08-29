"""Serviço de onboarding inteligente com visão computacional (Gemini).

Fluxo:
  1. Upload de documento (imagem/PDF)
  2. Análise por Gemini Vision → identifica tipo (RG, CPF, receita, exame, lista)
  3. Extrai dados estruturados do paciente
  4. Verifica se já existe cadastro
  5. Cria paciente ou abre pendência
  6. Se for lista/planilha → processamento em lote
  7. Compliance check → pendências de documentos faltantes
"""

import base64
import json
import logging
import os
import re
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import or_

from models import db, Paciente, OnboardingPaciente, OnboardingDocumento

logger = logging.getLogger(__name__)


class IntelligentOnboardingService:
    """Serviço principal de onboarding inteligente"""

    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf", "csv", "xlsx"}

    def __init__(self):
        self.ai_manager = None
        self._init_ai()

    def _init_ai(self):
        try:
            from services.ai_agents import ai_manager
            self.ai_manager = ai_manager
        except Exception as e:
            logger.warning(f"AI manager indisponivel: {e}")

    # ────────────────────────────────────────
    # 1. Análise de documento com Gemini Vision
    # ────────────────────────────────────────

    def analisar_documento(self, arquivo_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Analisa documento usando Gemini Vision.

        Retorna:
            tipo: RG | CPF | RECEITA | EXAME | RELATORIO | LISTA | OUTRO
            dados_paciente: {nome, cpf, telefone, email, ...}
            texto_extraido: str
            confianca: float
            multiplos_pacientes: bool (se for lista)
            pacientes: [{}] (se multiplos_pacientes)
            documento_existente: bool (se identifica doc existente no prontuário)
        """
        if not self.ai_manager:
            return self._fallback_analise(arquivo_bytes, filename)

        b64 = base64.b64encode(arquivo_bytes).decode("ascii")
        prompt = """Analise este documento e retorne APENAS UM JSON com:

1. "tipo": classifique como "RG", "CPF", "RECEITA", "EXAME", "RELATORIO", "LISTA" ou "OUTRO"
2. "dados_paciente": extraia nome, cpf, telefone, email, data_nascimento, endereco (se visível)
3. "texto_extraido": todo texto legível do documento
4. "confianca": 0.0 a 1.0 (sua confiança na extração)
5. "multiplos_pacientes": true se for lista/planilha com vários pacientes
6. "pacientes": se multiplos_pacientes=true, array com {nome, cpf, telefone} de cada
7. "documento_titulo": título do documento (ex: "Receita de Canabidiol", "Exame de Sangue")
8. "observacoes": observações relevantes sobre o documento

NÃO invente dados. Se não tiver certeza, deixe o campo vazio ou null.
Responda EXCLUSIVAMENTE o JSON, sem markdown."""
        try:
            response = self.ai_manager.vision_completion(
                prompt=prompt,
                image_data=b64,
                temperature=0.1,
                max_tokens=2000,
            )
            content = response.get("content", "")
            content = re.sub(r"^```(?:json)?|```$", "", content, flags=re.MULTILINE).strip()
            resultado = json.loads(content)
            return self._normalizar_resultado(resultado, filename)
        except Exception as e:
            logger.error(f"Erro na analise de documento com IA: {e}")
            return self._fallback_analise(arquivo_bytes, filename)

    def _normalizar_resultado(self, resultado: Dict, filename: str) -> Dict:
        if not isinstance(resultado.get("dados_paciente"), dict):
            resultado["dados_paciente"] = {}
        dp = resultado["dados_paciente"]
        if dp.get("cpf"):
            dp["cpf"] = re.sub(r"\D", "", dp["cpf"])
        if dp.get("telefone"):
            dp["telefone"] = re.sub(r"\D", "", dp["telefone"])
        resultado["confianca"] = min(float(resultado.get("confianca", 0) or 0), 1.0)
        resultado["nome_arquivo"] = filename
        return resultado

    def _fallback_analise(self, arquivo_bytes: bytes, filename: str) -> Dict[str, Any]:
        from services.onboarding_pacientes import extrair_texto_arquivo, sugerir_dados

        texto, confianca = extrair_texto_arquivo(arquivo_bytes, filename)
        sugestao = sugerir_dados(texto) if texto else {}
        return {
            "tipo": "OUTRO",
            "dados_paciente": sugestao,
            "texto_extraido": texto,
            "confianca": confianca / 100.0,
            "multiplos_pacientes": False,
            "pacientes": [],
            "documento_titulo": None,
            "observacoes": "Analisado via OCR fallback (IA indisponivel)",
            "nome_arquivo": filename,
        }

    # ────────────────────────────────────────
    # 2. Processamento inteligente
    # ────────────────────────────────────────

    def processar_documento(
        self,
        arquivo_bytes: bytes,
        filename: str,
        criado_por: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Pipeline completo: analisar → verificar duplicados → criar/abrir pendência."""
        analise = self.analisar_documento(arquivo_bytes, filename)

        if analise.get("multiplos_pacientes") and analise.get("pacientes"):
            return self._processar_lote(analise, arquivo_bytes, filename, criado_por)

        dados = analise.get("dados_paciente", {})

        doc = self._salvar_documento(arquivo_bytes, filename, analise, criado_por)

        if not dados.get("nome"):
            pendente = self._criar_pendencia(
                dados=dados,
                motivo="dados_incompletos",
                origem="documento",
                criado_por=criado_por,
                documento_id=doc.id,
            )
            return {
                "status": "pendente",
                "motivo": "dados_incompletos",
                "onboarding_id": pendente.id,
                "documento_id": doc.id,
                "analise": analise,
                "mensagem": "Documento processado, mas sem dados suficientes. Crie a pendência para revisão manual.",
            }

        duplicados = self._detectar_duplicados(dados)
        if duplicados:
            paciente_existente = duplicados[0]
            doc_existente = self._documento_ja_existe_no_prontuario(
                analise.get("documento_titulo"), paciente_existente.id
            )
            if doc_existente:
                return {
                    "status": "duplicado",
                    "motivo": "documento_ja_existe",
                    "paciente_id": paciente_existente.id,
                    "documento_id": doc.id,
                    "analise": analise,
                    "mensagem": f"Documento já existe no prontuário de {paciente_existente.nome}.",
                }

            pendente = self._criar_pendencia(
                dados=dados,
                motivo="duplicado",
                origem="documento",
                criado_por=criado_por,
                documento_id=doc.id,
                duplicado_de=paciente_existente.id,
            )
            return {
                "status": "pendente",
                "motivo": "duplicado",
                "onboarding_id": pendente.id,
                "documento_id": doc.id,
                "duplicados": [p.to_dict() for p in duplicados],
                "analise": analise,
                "mensagem": f"Paciente já cadastrado como {paciente_existente.nome}. Deseja vincular o documento ao cadastro existente?",
            }

        paciente = self._criar_paciente(dados)
        self._vincular_documento(doc.id, paciente.id)

        compliance = self._verificar_compliance(paciente)

        return {
            "status": "criado",
            "paciente_id": paciente.id,
            "documento_id": doc.id,
            "analise": analise,
            "compliance": compliance,
            "mensagem": f"Paciente {paciente.nome} cadastrado com sucesso.",
        }

    def _processar_lote(
        self,
        analise: Dict,
        arquivo_bytes: bytes,
        filename: str,
        criado_por: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Processa lista/planilha com múltiplos pacientes."""
        pacientes_lista = analise.get("pacientes", [])
        if not pacientes_lista:
            return {"status": "erro", "mensagem": "Nenhum paciente identificado na lista."}

        resultados = []
        for dados in pacientes_lista:
            try:
                if not dados.get("nome"):
                    resultados.append({"status": "ignorado", "dados": dados, "motivo": "nome_ausente"})
                    continue

                duplicados = self._detectar_duplicados(dados)
                if duplicados:
                    resultados.append({
                        "status": "pendente",
                        "dados": dados,
                        "motivo": "duplicado",
                        "duplicado": duplicados[0].to_dict(),
                    })
                    continue

                paciente = self._criar_paciente(dados)
                compliance = self._verificar_compliance(paciente)
                resultados.append({
                    "status": "criado",
                    "dados": dados,
                    "paciente_id": paciente.id,
                    "compliance": compliance,
                })
            except Exception as e:
                logger.error(f"Erro ao processar paciente em lote: {e}")
                resultados.append({"status": "erro", "dados": dados, "erro": str(e)})

        doc = self._salvar_documento(arquivo_bytes, filename, analise, criado_por)

        return {
            "status": "lote_processado",
            "total": len(pacientes_lista),
            "criados": sum(1 for r in resultados if r["status"] == "criado"),
            "pendentes": sum(1 for r in resultados if r["status"] == "pendente"),
            "ignorados": sum(1 for r in resultados if r["status"] == "ignorado"),
            "erros": sum(1 for r in resultados if r["status"] == "erro"),
            "resultados": resultados,
            "documento_id": doc.id,
        }

    # ────────────────────────────────────────
    # 3. Compliance check
    # ────────────────────────────────────────

    def _verificar_compliance(self, paciente: Paciente) -> Dict[str, Any]:
        """Verifica se o paciente tem dados completos e cria pendências."""
        faltantes = []
        if not paciente.cpf:
            faltantes.append("cpf")
        if not paciente.telefone:
            faltantes.append("telefone")
        if not paciente.email:
            faltantes.append("email")
        if not paciente.endereco:
            faltantes.append("endereco")
        if not paciente.data_nascimento:
            faltantes.append("data_nascimento")

        if faltantes:
            pendente = OnboardingPaciente(
                nome=paciente.nome,
                telefone=paciente.telefone,
                cpf=paciente.cpf,
                email=paciente.email,
                origem="compliance",
                dados_sugeridos={"paciente_id": paciente.id},
                motivo="dados_incompletos",
                status="pendente",
                duplicado_de=paciente.id,
                criado_por="system",
            )
            db.session.add(pendente)
            db.session.commit()

        return {
            "completo": not faltantes,
            "campos_faltantes": faltantes,
        }

    def verificar_compliance_existente(self, paciente_id: int) -> Dict[str, Any]:
        """Re-verifica compliance de paciente já cadastrado."""
        paciente = Paciente.query.get(paciente_id)
        if not paciente:
            return {"error": "Paciente nao encontrado"}
        return self._verificar_compliance(paciente)

    # ────────────────────────────────────────
    # 4. Follow-up: contatar paciente
    # ────────────────────────────────────────

    def follow_up_paciente(
        self, paciente_id: int, canal: str = "email"
    ) -> Dict[str, Any]:
        """Contata paciente solicitando documentos faltantes."""
        paciente = Paciente.query.get(paciente_id)
        if not paciente:
            return {"error": "Paciente nao encontrado"}

        faltantes = self._get_campos_faltantes(paciente)
        if not faltantes:
            return {"status": "completo", "mensagem": "Paciente ja esta completo"}

        mensagem = (
            f"Olá {paciente.nome}! 😊\n\n"
            "Notamos que ainda faltam alguns dados no seu cadastro. "
            "Para mantermos seu prontuário atualizado, pedimos gentilmente que "
            "nos envie os seguintes documentos:\n\n"
        )
        campo_labels = {
            "cpf": "CPF",
            "telefone": "Telefone para contato",
            "email": "E-mail",
            "endereco": "Comprovante de endereço",
            "data_nascimento": "Data de nascimento",
        }
        for campo in faltantes:
            label = campo_labels.get(campo, campo)
            mensagem += f"  • {label}\n"

        mensagem += (
            "\nVocê pode enviar os documentos respondendo a esta mensagem "
            "ou pelo nosso portal do paciente.\n\n"
            "Agradecemos pela atenção! 🌿\n"
            "Equipe AraOS"
        )

        if canal == "whatsapp" and paciente.telefone:
            try:
                from services.whatsapp_service import whatsapp_service
                whatsapp_service.send_message(paciente.telefone, mensagem)
                return {"status": "enviado", "canal": "whatsapp", "telefone": paciente.telefone}
            except Exception as e:
                logger.error(f"Erro whatsapp: {e}")

        if canal in ("email", "whatsapp") and paciente.email:
            try:
                from services.email_service import EmailService
                EmailService().send_email(
                    paciente.email,
                    "Documentos pendentes - AraOS",
                    mensagem.replace("\n", "<br>"),
                )
                return {"status": "enviado", "canal": "email", "email": paciente.email}
            except Exception as e:
                logger.error(f"Erro email: {e}")

        return {"status": "falhou", "motivo": "nenhum canal de contato disponivel"}

    def follow_up_pendentes(self, dias_max: int = 7) -> List[Dict]:
        """Contata todos os pacientes com pendências ativas há mais de N dias."""
        from services.onboarding_pacientes import listar_pendentes

        pendentes = listar_pendentes()
        resultados = []
        corte = datetime.utcnow() - timedelta(days=dias_max)

        for p in pendentes:
            if p.created_at and p.created_at > corte:
                continue
            paciente_id = p.duplicado_de
            if not paciente_id:
                continue
            try:
                paciente = Paciente.query.get(paciente_id)
                if not paciente:
                    continue
                resultado = self.follow_up_paciente(paciente_id)
                resultados.append({
                    "onboarding_id": p.id,
                    "paciente_id": paciente_id,
                    "resultado": resultado,
                })
            except Exception as e:
                logger.error(f"Erro follow-up pendencia {p.id}: {e}")

        return resultados

    # ────────────────────────────────────────
    # Helpers
    # ────────────────────────────────────────

    def _detectar_duplicados(self, dados: Dict) -> List[Paciente]:
        cpf = re.sub(r"\D", "", dados.get("cpf") or "")
        tel = re.sub(r"\D", "", dados.get("telefone") or "")
        nome = (dados.get("nome") or "").strip()

        conds = []
        if cpf:
            conds.append(Paciente.cpf == cpf)
        if tel:
            conds.append(Paciente.telefone == tel)
        if nome:
            conds.append(Paciente.nome.ilike(f"%{nome}%"))
        if not conds:
            return []
        return Paciente.query.filter(or_(*conds)).all()

    def _documento_ja_existe_no_prontuario(self, titulo: Optional[str], paciente_id: int) -> bool:
        """Verifica se documento similar já existe no prontuário."""
        if not titulo:
            return False
        from models import Exame

        existente = Exame.query.filter(
            Exame.paciente_id == paciente_id,
            Exame.titulo.ilike(f"%{titulo}%"),
        ).first()
        return existente is not None

    def _criar_paciente(self, dados: Dict) -> Paciente:
        data_nasc = None
        if dados.get("data_nascimento"):
            try:
                data_nasc = datetime.strptime(dados["data_nascimento"], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                data_nasc = None
        paciente = Paciente(
            nome=(dados.get("nome") or "").strip(),
            cpf=re.sub(r"\D", "", dados.get("cpf") or "") or None,
            telefone=re.sub(r"\D", "", dados.get("telefone") or "") or None,
            email=(dados.get("email") or "").strip() or None,
            data_nascimento=data_nasc,
            endereco=(dados.get("endereco") or "").strip() or None,
        )
        db.session.add(paciente)
        db.session.commit()
        return paciente

    def _criar_pendencia(
        self,
        *,
        dados: Dict,
        motivo: str,
        origem: str = "documento",
        criado_por: Optional[str] = None,
        documento_id: Optional[int] = None,
        duplicado_de: Optional[int] = None,
    ) -> OnboardingPaciente:
        payload = {**dados}
        if documento_id:
            payload["documento_id"] = documento_id
        pendente = OnboardingPaciente(
            nome=(dados.get("nome") or "").strip() or None,
            telefone=re.sub(r"\D", "", dados.get("telefone") or "") or None,
            cpf=re.sub(r"\D", "", dados.get("cpf") or "") or None,
            email=(dados.get("email") or "").strip() or None,
            queixa=dados.get("observacoes"),
            origem=origem,
            dados_sugeridos=payload,
            motivo=motivo,
            status="pendente",
            duplicado_de=duplicado_de,
            criado_por=criado_por,
        )
        db.session.add(pendente)
        db.session.commit()
        return pendente

    def _salvar_documento(
        self,
        arquivo_bytes: bytes,
        filename: str,
        analise: Dict,
        criado_por: Optional[str] = None,
    ) -> OnboardingDocumento:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
        nome_salvo = f"{uuid.uuid4().hex[:16]}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{ext}"
        pasta = os.path.join(os.getcwd(), "uploads", "onboarding")
        os.makedirs(pasta, exist_ok=True)
        caminho = os.path.join(pasta, nome_salvo)
        with open(caminho, "wb") as f:
            f.write(arquivo_bytes)

        doc = OnboardingDocumento(
            nome_original=filename,
            caminho_arquivo=caminho,
            mime=f"image/{ext}" if ext in ("jpg", "jpeg", "png") else "application/octet-stream",
            texto_extraido=analise.get("texto_extraido", "")[:5000] or None,
            confianca=analise.get("confianca", 0),
            criado_por=criado_por,
        )
        db.session.add(doc)
        db.session.commit()
        return doc

    def _vincular_documento(self, documento_id: int, paciente_id: int) -> None:
        doc = OnboardingDocumento.query.get(documento_id)
        if doc:
            doc.paciente_id = paciente_id
            db.session.commit()

    def _get_campos_faltantes(self, paciente: Paciente) -> List[str]:
        faltantes = []
        if not paciente.cpf:
            faltantes.append("cpf")
        if not paciente.telefone:
            faltantes.append("telefone")
        if not paciente.email:
            faltantes.append("email")
        if not paciente.endereco:
            faltantes.append("endereco")
        if not paciente.data_nascimento:
            faltantes.append("data_nascimento")
        return faltantes


onboarding_service = IntelligentOnboardingService()
from datetime import datetime
from flask import current_app
from models import Paciente, Profissional, Dosagem, Evolucao, Sintoma
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from services.ai_agents import ai_manager
import matplotlib.pyplot as plt
import io
import os

class HCReportService:
    
    def gerar_laudo_hc(self, profissional_id, paciente_id, justificativa_medica=None):
        """
        Gera um laudo médico robusto para Habeas Corpus, com gráficos de evolução
        e argumentação baseada em dados clínicos, assistido por IA.
        """
        profissional = Profissional.query.get(profissional_id)
        paciente = Paciente.query.get(paciente_id)
        
        if not profissional or not paciente:
            raise ValueError("Profissional ou Paciente não encontrado")

        # 1. Coletar Dados Clínicos (Histórico)
        evolucoes = Evolucao.query.filter_by(paciente_id=paciente_id).order_by(Evolucao.data.asc()).all()
        sintomas = Sintoma.query.filter_by(paciente_id=paciente_id).order_by(Sintoma.data.asc()).all()
        dosagens = Dosagem.query.filter_by(paciente_id=paciente_id).all()
        
        # 2. Gerar Gráfico de Evolução (Melhora vs Tempo)
        grafico_path = self._gerar_grafico_hc(paciente, sintomas)
        
        # 3. Gerar Argumentação via IA (Se não fornecida manualmente)
        argumentacao = justificativa_medica
        if not argumentacao:
            argumentacao = self._gerar_argumentacao_ia(paciente, evolucoes, sintomas, profissional)

        # 4. Construir PDF
        return self._construir_pdf_hc(paciente, profissional, argumentacao, grafico_path, dosagens)

    def _gerar_grafico_hc(self, paciente, sintomas):
        """Gera um gráfico visual da melhora clínica para anexar ao laudo"""
        if not sintomas:
            return None
            
        # Agrupar sintomas por data e calcular média de intensidade
        datas = []
        intensidades = []
        sintoma_dict = {}
        
        for s in sintomas:
            d_str = s.data.strftime('%d/%m/%Y')
            if d_str not in sintoma_dict:
                sintoma_dict[d_str] = []
            sintoma_dict[d_str].append(s.intensidade)
            
        for d in sorted(sintoma_dict.keys(), key=lambda x: datetime.strptime(x, '%d/%m/%Y')):
            datas.append(d)
            avg = sum(sintoma_dict[d]) / len(sintoma_dict[d])
            intensidades.append(avg)
            
        plt.figure(figsize=(10, 4))
        plt.plot(datas, intensidades, marker='o', linestyle='-', color='green', label='Intensidade dos Sintomas')
        plt.title(f"Evolução Clínica e Resposta Terapêutica - {paciente.nome}")
        plt.xlabel("Data")
        plt.ylabel("Intensidade (0-10)")
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        plt.tight_layout()
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300)
        buffer.seek(0)
        plt.close()
        
        # Salvar temporariamente
        temp_filename = f"grafico_hc_{paciente.id}_{int(datetime.utcnow().timestamp())}.png"
        upload_folder = current_app.config.get('UPLOAD_FOLDER_EXAMES', 'uploads')
        file_path = os.path.join(upload_folder, temp_filename)
        with open(file_path, 'wb') as f:
            f.write(buffer.read())
            
        return file_path

    def _gerar_argumentacao_ia(self, paciente, evolucoes, sintomas, profissional):
        """Usa Zhipu (GLM-4) ou Gemini para redigir o laudo jurídico-médico"""
        
        # Resumir histórico
        resumo_hist = "\n".join([f"- {e.data.strftime('%d/%m/%Y')}: {e.texto_evolucao[:200]}..." for e in evolucoes[-5:]])
        diag = paciente.diagnostico or "Condição crônica refratária"
        
        prompt = f"""
        Você é um médico perito especializado em Canabinologia. Redija a "Justificativa Médica" para um Laudo de Habeas Corpus (Salvo Conduto) para autocultivo de Cannabis Medicinal.
        
        DADOS DO PACIENTE:
        Nome: {paciente.nome}
        Idade: {(datetime.now().date() - paciente.data_nascimento).days // 365} anos
        Diagnóstico: {diag}
        
        HISTÓRICO RECENTE:
        {resumo_hist}
        
        OBJETIVO:
        Demonstrar que o paciente obteve melhora significativa e estabilização clínica apenas com o tratamento canabinoide prescrito, que outras terapias convencionais falharam ou tiveram muitos efeitos colaterais restritivos, e que a continuidade segura do tratamento através do autocultivo contínuo é estritamente essencial para a manutenção da saúde, qualidade de vida e dignidade do paciente.
        
        FORMATO:
        Responda APENAS com o texto final. Não forneça saudações ou comentários.
        O texto deve ser formal, técnico, médico-legal, e dividido EXATAMENTE em 3 parágrafos curtos:
        1. Histórico e falha da terapia convencional anterior.
        2. Resposta clínica estatisticamente e clinicamente positiva aos canabinoides (mencione controle do quadro clínico).
        3. Conclusão atestando a necessidade imperativa do uso contínuo, ininterrupto e seguro, justificando a liminar de cultivo.
        """
        
        try:
            # Tentar primariamente Zhipu (GLM-4) conforme politica de deploy
            resp = ai_manager.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                provider="zhipu",
                model="glm-4-plus"
            )
            return resp.get('content', "Justificativa não gerada automaticamente.")
        except Exception as e_zhipu:
            # Fallback explícito para o Ollama local em caso de falha da API externa
            try:
                resp_fallback = ai_manager.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    provider="ollama_local",
                    model="llama3.1:8b"
                )
                return resp_fallback.get('content', "Justificativa não gerada automaticamente (Fallback Ollama).")
            except Exception as e_ollama:
                return f"Erro ao gerar justificativa automática (Zhipu falhou: {str(e_zhipu)} | Ollama falhou: {str(e_ollama)}). Por favor, redija manualmente."

    def _construir_pdf_hc(self, paciente, profissional, argumentacao, grafico_path, dosagens):
        pdf_filename = f"laudo_hc_{paciente.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        upload_folder = current_app.config.get('UPLOAD_FOLDER_EXAMES', 'uploads')
        pdf_path = os.path.join(upload_folder, pdf_filename)
        
        doc = SimpleDocTemplate(pdf_path, pagesize=A4, margin=(2*cm, 2*cm, 2*cm, 2*cm))
        elements = []
        styles = getSampleStyleSheet()
        
        # Estilos
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], alignment=1, fontSize=16, spaceAfter=20)
        subtitle_style = ParagraphStyle('Sub', parent=styles['Heading2'], fontSize=12, textColor=colors.darkgreen)
        body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=11, leading=14, alignment=4) # Justify
        
        # Título
        elements.append(Paragraph("LAUDO MÉDICO PERICIAL", title_style))
        elements.append(Paragraph("PARA FINS DE SALVO CONDUTO (HABEAS CORPUS)", ParagraphStyle('SubTitle', parent=styles['Normal'], alignment=1, fontSize=12)))
        elements.append(Spacer(1, 1*cm))
        
        # Identificação
        elements.append(Paragraph("1. IDENTIFICAÇÃO", subtitle_style))
        elements.append(Paragraph(f"<b>PACIENTE:</b> {paciente.nome}, CPF: {paciente.cpf}", body_style))
        elements.append(Paragraph(f"<b>MÉDICO ASSISTENTE:</b> Dr(a). {profissional.nome}, CRM: {profissional.crm}", body_style))
        elements.append(Paragraph(f"<b>DATA:</b> {datetime.now().strftime('%d/%m/%Y')}", body_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Diagnóstico
        elements.append(Paragraph("2. DIAGNÓSTICO (CID)", subtitle_style))
        elements.append(Paragraph(f"{paciente.diagnostico}", body_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Justificativa (IA ou Manual)
        elements.append(Paragraph("3. HISTÓRICO CLÍNICO E JUSTIFICATIVA", subtitle_style))
        for para in argumentacao.split('\n'):
            if para.strip():
                elements.append(Paragraph(para.strip(), body_style))
                elements.append(Spacer(1, 0.2*cm))
        
        # Evidência Gráfica
        if grafico_path and os.path.exists(grafico_path):
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph("4. EVIDÊNCIA DE MELHORA CLÍNICA (Gráfico de Sintomas)", subtitle_style))
            img = Image(grafico_path, width=16*cm, height=7*cm)
            elements.append(img)
            elements.append(Paragraph("<i>Gráfico extraído do prontuário eletrônico monitorado, demonstrando a redução da intensidade dos sintomas com o início do tratamento.</i>", ParagraphStyle('Caption', parent=styles['Normal'], fontSize=9, alignment=1, textColor=colors.gray)))
            elements.append(Spacer(1, 0.5*cm))
            
        # Tratamento Atual
        elements.append(Paragraph("5. TRATAMENTO PRESCRITO", subtitle_style))
        for dose in dosagens:
            elements.append(Paragraph(f"- {dose.dosagem}: {dose.gotas} gotas, {dose.frequencia_diaria}x ao dia. ({dose.via_administracao or 'Uso Oral'})", body_style))
            
        elements.append(Spacer(1, 1*cm))
        
        # Conclusão Final
        elements.append(Paragraph("6. CONCLUSÃO", subtitle_style))
        elements.append(Paragraph("Diante do exposto, atesto que o paciente necessita do uso contínuo dos extratos de Cannabis sp. para controle de sua patologia. A interrupção do tratamento pode acarretar grave prejuízo à saúde e retorno dos sintomas incapacitantes.", body_style))
        
        # Assinatura
        elements.append(Spacer(1, 2.5*cm))
        elements.append(Paragraph("_" * 50, ParagraphStyle('Line', parent=styles['Normal'], alignment=1)))
        elements.append(Paragraph(f"Dr(a). {profissional.nome}", ParagraphStyle('Sign', parent=styles['Normal'], alignment=1)))
        elements.append(Paragraph(f"CRM {profissional.crm}/{profissional.uf_crm}", ParagraphStyle('Sign', parent=styles['Normal'], alignment=1)))
        
        doc.build(elements)
        return pdf_filename

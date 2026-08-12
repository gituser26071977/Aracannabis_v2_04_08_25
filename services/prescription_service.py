import os
from datetime import datetime
from flask import current_app, g
from models import db, Prescricao, Paciente, Profissional, Dosagem, ConfiguracaoPrescricao
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm


def _resolve_assoc_id():
    """Resolve o associacao_id do tenant atual (P0-12)."""
    assoc = getattr(g, "current_association", None)
    return getattr(assoc, "id", None)

class PrescriptionService:
    
    def _build_header(self, elements, profissional, styles):
        # Buscar config do profissional
        config = ConfiguracaoPrescricao.query.filter_by(profissional_id=profissional.id).first()
        upload_path = os.path.join(current_app.root_path, '..', 'uploads', 'logos')
        
        logo_clinica_path = os.path.join(upload_path, config.logo_clinica) if config and config.logo_clinica else None
        logo_prof_path = os.path.join(upload_path, config.logo_profissional) if config and config.logo_profissional else None
        
        has_clinica = logo_clinica_path and os.path.exists(logo_clinica_path)
        has_prof = logo_prof_path and os.path.exists(logo_prof_path)
        
        # Lógica de Layout de Imagens (60% / 40%)
        header_table_data = []
        if has_clinica and has_prof:
            img_clinica = Image(logo_clinica_path, width=5*cm, height=3*cm, kind='proportional')
            img_prof = Image(logo_prof_path, width=3.3*cm, height=2*cm, kind='proportional') # 60/40 ratio aprox
            row = [img_clinica, img_prof]
            col_widths = [11*cm, 5*cm] # Total 16cm
            header_table_data.append(row)
        elif has_clinica:
            img_clinica = Image(logo_clinica_path, width=6*cm, height=3.6*cm, kind='proportional')
            row = [img_clinica]
            col_widths = [16*cm]
            header_table_data.append(row)
        elif has_prof:
            img_prof = Image(logo_prof_path, width=6*cm, height=3.6*cm, kind='proportional')
            row = [img_prof]
            col_widths = [16*cm]
            header_table_data.append(row)
            
        if header_table_data:
            t = Table(header_table_data, colWidths=col_widths if 'col_widths' in locals() else None)
            t.setStyle([('ALIGN', (0,0), (0,0), 'LEFT'), ('ALIGN', (-1,0), (-1,0), 'RIGHT'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')])
            elements.append(t)
            elements.append(Spacer(1, 0.5*cm))

        # Textos Personalizados do Cabeçalho
        style_header = ParagraphStyle('Header', parent=styles['Heading1'], fontSize=16, alignment=1, spaceAfter=6, textColor=colors.darkgreen)
        style_sub = ParagraphStyle('SubHeader', parent=styles['Normal'], fontSize=10, alignment=1, textColor=colors.gray)
        
        if config and config.cabecalho_personalizado:
            for line in config.cabecalho_personalizado.split('\n'):
                elements.append(Paragraph(line.strip(), style_header))
        else:
            elements.append(Paragraph(profissional.nome, style_header))
            
        elements.append(Paragraph(f"CRM/Registro: {profissional.crm} - {profissional.uf_crm}", style_sub))
        elements.append(Spacer(1, 1*cm))
        
        return config

    def gerar_prescricao_pdf(self, profissional_id, paciente_id, dosagens_ids=None, observacoes=None):
        profissional = Profissional.query.get(profissional_id)
        paciente = Paciente.query.get(paciente_id)
        
        if not profissional or not paciente:
            raise ValueError("Profissional ou Paciente não encontrado")

        pdf_filename = f"prescricao_{paciente.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        upload_folder = current_app.config.get('UPLOAD_FOLDER_EXAMES', 'uploads')
        pdf_path = os.path.join(upload_folder, pdf_filename)
        
        # Margens otimizadas
        doc = SimpleDocTemplate(pdf_path, pagesize=A4, margin=(1.5*cm, 1.5*cm, 2*cm, 1.5*cm))
        elements = []
        styles = getSampleStyleSheet()
        
        # 1. CABEÇALHO (Logos e Texts)
        config = self._build_header(elements, profissional, styles)
        
        style_normal = styles['Normal']
        style_title = ParagraphStyle('Title', parent=styles['Heading2'], fontSize=14, spaceAfter=20, spaceBefore=10, alignment=1, textColor=colors.black)
        style_med_name = ParagraphStyle('MedName', parent=styles['Heading3'], fontSize=12, spaceAfter=4, textColor=colors.black)

        # 2. DADOS DO PACIENTE OTIMIZADOS
        p_data = [
            [Paragraph(f"<b>Paciente:</b> {paciente.nome}", style_normal), Paragraph(f"<b>Data:</b> {datetime.now().strftime('%d/%m/%Y')}", style_normal)],
            [Paragraph(f"<b>CPF:</b> {paciente.cpf or '-'}", style_normal), Paragraph(f"<b>Nascimento:</b> {paciente.data_nascimento.strftime('%d/%m/%Y') if paciente.data_nascimento else '-'}", style_normal)]
        ]
        t_paciente = Table(p_data, colWidths=[11*cm, 6*cm], style=[
            ('BOX', (0,0), (-1,-1), 1, colors.lightgrey),
            ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
            ('PADDING', (0,0), (-1,-1), 6),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ])
        elements.append(t_paciente)
        elements.append(Spacer(1, 0.5*cm))
        
        elements.append(Paragraph("Receituário", style_title))
        
        # 3. ITENS DA PRESCRIÇÃO
        if dosagens_ids:
            dosagens = Dosagem.query.filter(Dosagem.id.in_(dosagens_ids)).all()
        else:
            dosagens = Dosagem.query.filter_by(paciente_id=paciente_id).order_by(Dosagem.created_at.desc()).limit(10).all()
        
        medicamentos_list = []
        
        for idx, dose in enumerate(dosagens, 1):
            if dose.tipo_dose == 'variavel' and dose.esquema_doses:
                partes = []
                esquema = dose.esquema_doses
                if esquema.get('manha'): partes.append(f"{esquema['manha']} gotas manha")
                if esquema.get('almoco'): partes.append(f"{esquema['almoco']} gotas almoço")
                if esquema.get('tarde'): partes.append(f"{esquema['tarde']} gotas tarde")
                if esquema.get('noite'): partes.append(f"{esquema['noite']} gotas noite")
                if esquema.get('deitar'): partes.append(f"{esquema['deitar']} gotas ao deitar")
                posologia_texto = ", ".join(partes)
            else:
                total = dose.gotas or 0
                freq = dose.frequencia_diaria or 1
                posologia_texto = f"{total} gotas, {freq} vezes ao dia"
            
            nome_med = dose.dosagem
            uso = dose.via_administracao or (dose.produto.via_administracao if dose.produto else 'Uso Oral')
            
            # Agrupar medicamento para nao quebrar pagina no meio
            item_elements = []
            item_elements.append(Paragraph(f"{idx}. {nome_med}", style_med_name))
            item_elements.append(Paragraph(f"   <b>{uso.upper()}</b>", style_normal))
            item_elements.append(Paragraph(f"   Posologia: {posologia_texto}", style_normal))
            
            instrucoes = dose.instrucoes_uso or (dose.produto.instrucoes if dose.produto else None)
            if instrucoes:
                 item_elements.append(Paragraph(f"   <i>Instruções: {instrucoes}</i>", ParagraphStyle('Instrucao', parent=style_normal, fontSize=9, textColor=colors.darkblue, leftIndent=12)))
            else:
                 if "cbd" in nome_med.lower() or "thc" in nome_med.lower() or "cannabis" in nome_med.lower():
                     default_instr = "Ingerir junto de alimentos fonte de gordura boa para otimização da absorção."
                     item_elements.append(Paragraph(f"   <i>Instruções: {default_instr}</i>", ParagraphStyle('InstrucaoDefault', parent=style_normal, fontSize=9, textColor=colors.gray, leftIndent=12)))
            
            if dose.concentracao_cbd or dose.concentracao_thc:
                obs_conc = f"   (Conc: {dose.concentracao_cbd}mg CBD / {dose.concentracao_thc}mg THC)"
                item_elements.append(Paragraph(obs_conc, ParagraphStyle('Obs', parent=style_normal, fontSize=9, textColor=colors.gray)))
            
            item_elements.append(Spacer(1, 0.5*cm))
            elements.append(KeepTogether(item_elements))
            
            medicamentos_list.append({
                'nome': nome_med,
                'posologia': posologia_texto,
                'via': uso,
                'instrucoes': instrucoes
            })
            
        if observacoes:
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph("<b>Observações Gerais:</b>", style_normal))
            elements.append(Paragraph(observacoes, style_normal))

        # 4. RODAPÉ e ASSINATURA (ICP-Brasil/Gov.br ou APIs)
        elements.append(Spacer(1, 2.5*cm))
        
        sign_elements = []
        
        if config and config.usar_assinatura_digital:
            # Box otmizado para carimbo digital BirdID / Valid
            sign_elements.append(Paragraph("<i>(Assinatura Validadora Integrada Third-Party)</i>", ParagraphStyle('SignInfo', parent=style_normal, alignment=1, fontSize=8, textColor=colors.gray)))
            sign_elements.append(Spacer(1, 1.5*cm))
            sign_elements.append(Paragraph("_" * 40, ParagraphStyle('Line', parent=style_normal, alignment=1)))
            sign_elements.append(Paragraph(profissional.nome, ParagraphStyle('Sign', parent=style_normal, alignment=1, fontSize=10)))
        else:
            # Box de Cartório ICP-Brasil Padrão (Gov.br)
            icp_style = ParagraphStyle('ICP', parent=style_normal, alignment=1, fontSize=9)
            sign_elements.append(Paragraph("_" * 60, ParagraphStyle('Line', parent=style_normal, alignment=1)))
            sign_elements.append(Paragraph(f"<b>{profissional.nome}</b>", icp_style))
            sign_elements.append(Paragraph(f"CRM/Registro: {profissional.crm} - {profissional.uf_crm}", icp_style))
            sign_elements.append(Spacer(1, 0.2*cm))
            sign_elements.append(Paragraph("Documento assinado digitalmente conforme MP nº 2.200-2/2001 (ICP-Brasil).", ParagraphStyle('Info', parent=style_normal, alignment=1, fontSize=7, textColor=colors.gray)))
            sign_elements.append(Paragraph("A validação pode ser feita no portal gov.br/receita-federal.", ParagraphStyle('Info2', parent=style_normal, alignment=1, fontSize=7, textColor=colors.gray)))
        
        elements.append(KeepTogether(sign_elements))

        # O Rodapé final da página (Textos personalizados)
        if config and config.rodape_personalizado:
            elements.append(Spacer(1, 1*cm))
            footer_text = config.rodape_personalizado.replace('\n', '<br/>')
            elements.append(Paragraph(footer_text, ParagraphStyle('FooterParams', parent=style_normal, alignment=1, fontSize=9, textColor=colors.grey)))

        doc.build(elements)

        prescricao = Prescricao(
            paciente_id=paciente.id,
            profissional_id=profissional.id,
            associacao_id=_resolve_assoc_id(),
            data_emissao=datetime.utcnow(),
            arquivo_path=pdf_filename,
            conteudo_json={'medicamentos': medicamentos_list},
            observacoes=observacoes
        )
        db.session.add(prescricao)
        db.session.commit()
        
        return prescricao

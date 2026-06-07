"""
Template HTML profissional para relatório médico
"""
from datetime import datetime

def gerar_html_relatorio(relatorio_data: dict) -> str:
    """
    Gera HTML profissional para relatório médico
    
    Args:
        relatorio_data: Dict com dados:
            - paciente: Dict
            - profissional: Dict
            - tipo_relatorio: str
            - conteudo_html: str (texto gerado pela IA formatado em HTML/Markdown)
            - data_geracao: datetime
            - metricas: Dict (opcional)
    
    Returns:
        HTML completo formatado
    """
    paciente = relatorio_data['paciente']
    profissional = relatorio_data['profissional']
    tipo_relatorio = relatorio_data.get('tipo_relatorio', 'Relatório Clínico')
    conteudo = relatorio_data.get('conteudo_html', '').replace('\n', '<br>')
    data_geracao = relatorio_data['data_geracao']
    
    data_formatada = data_geracao.strftime('%d/%m/%Y às %H:%M')
    
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{tipo_relatorio} - {paciente.get('nome', '')}</title>
        <style>
            @page {{
                size: A4;
                margin: 2cm;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 21cm;
                margin: 0 auto;
                padding: 20px;
                background: white;
            }}
            
            .cabecalho {{
                border-bottom: 3px solid #2c5f2d;
                padding-bottom: 20px;
                margin-bottom: 30px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            
            .logo-area h1 {{
                color: #2c5f2d;
                font-size: 24px;
                margin: 0;
                text-transform: uppercase;
            }}
            
            .logo-area span {{
                font-size: 14px;
                color: #666;
            }}
            
            .meta-info {{
                text-align: right;
                font-size: 12px;
                color: #888;
            }}
            
            .paciente-card {{
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 30px;
                border-left: 5px solid #2c5f2d;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }}
            
            .paciente-header {{
                font-size: 18px;
                font-weight: bold;
                color: #2c5f2d;
                margin-bottom: 10px;
                border-bottom: 1px solid #ddd;
                padding-bottom: 5px;
            }}
            
            .grid-info {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
                font-size: 14px;
            }}
            
            .conteudo-relatorio {{
                margin: 30px 0;
            }}
            
            .conteudo-relatorio h1, .conteudo-relatorio h2, .conteudo-relatorio h3 {{
                color: #2c5f2d;
            }}
            
            .conteudo-relatorio p {{
                margin-bottom: 15px;
                text-align: justify;
            }}
            
            .assinatura {{
                margin-top: 80px;
                text-align: center;
                page-break-inside: avoid;
            }}
            
            .assinatura-linha {{
                width: 300px;
                border-top: 1px solid #333;
                margin: 0 auto 10px;
            }}
            
            .rodape {{
                margin-top: 50px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                font-size: 11px;
                color: #999;
                text-align: center;
            }}
            
            /* Markdown styles simulation */
            blockquote {{
                border-left: 4px solid #ddd;
                padding-left: 15px;
                color: #666;
                margin: 20px 0;
            }}
            
            ul, ol {{
                margin-bottom: 15px;
            }}
            
            li {{
                margin-bottom: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="cabecalho">
            <div class="logo-area">
                <h1>{tipo_relatorio}</h1>
                <span>Sistema de Prontuário Inteligente</span>
            </div>
            <div class="meta-info">
                <p>Gerado em: {data_formatada}</p>
                <p>ID Referência: {paciente.get('id', '')}-{datetime.now().strftime('%H%M%S')}</p>
            </div>
        </div>
        
        <div class="paciente-card">
            <div class="paciente-header">Identificação do Paciente</div>
            <div class="grid-info">
                <div><strong>Nome:</strong> {paciente.get('nome', 'N/A')}</div>
                <div><strong>CPF:</strong> {paciente.get('cpf', 'N/A')}</div>
                <div><strong>Data Nasc.:</strong> {paciente.get('data_nascimento', 'N/A')}</div>
                <div><strong>Telefone:</strong> {paciente.get('telefone', 'N/A')}</div>
                <div style="grid-column: 1 / -1;"><strong>Diagnóstico Principal:</strong> {paciente.get('diagnostico', 'Não informado')}</div>
            </div>
        </div>
        
        <div class="conteudo-relatorio">
            <!-- Conteúdo gerado pela IA injetado aqui -->
            {conteudo}
        </div>
        
        <div class="assinatura">
            <div class="assinatura-linha"></div>
            <p><strong>{profissional.get('nome', '')}</strong></p>
            <p>CRM {profissional.get('crm', '')} / {profissional.get('uf_crm', '')}</p>
            <p><small>{profissional.get('especialidade', 'Médico Responsável')}</small></p>
        </div>
        
        <div class="rodape">
            <p>Documento gerado eletronicamente pelo Sistema Aracannabis em {data_formatada}</p>
            <p>Este relatório é confidencial e destinado apenas ao paciente e equipe médica autorizada.</p>
        </div>
    </body>
    </html>
    """
    
    return html

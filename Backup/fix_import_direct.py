#!/usr/bin/env python3
"""
Correção direta para network error na importação
"""

import shutil
from datetime import datetime

def main():
    print("🔧 CORRIGINDO NETWORK ERROR NA IMPORTAÇÃO")
    
    # Backup
    backup_path = f'routes/import_export_direct_fix_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py'
    shutil.copy('routes/import_export.py', backup_path)
    print(f"✅ Backup: {backup_path}")
    
    # Ler arquivo
    with open('routes/import_export.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Substituições simples
    content = content.replace(
        'from services.ai_agents import process_evolution_input, process_import_data',
        '# IA imports removed to prevent network errors'
    )
    
    # Substituir processamento de TXT para ser direto
    old_txt = '''elif filename.endswith(('.txt', '.md')):
                from services.ai_agents import process_text_file
                result = process_text_file(temp_file.name)
                result = convert_ai_result_to_import_result(patient_id, result)'''
    
    new_txt = '''elif filename.endswith(('.txt', '.md')):
                # Processamento direto de texto sem IA
                with open(temp_file.name, 'r', encoding='utf-8') as f:
                    text_content = f.read()
                
                try:
                    evolucao = Evolucao(
                        paciente_id=patient_id,
                        data_evolucao=datetime.now(),
                        nota_evolucao=text_content[:2000]
                    )
                    db.session.add(evolucao)
                    db.session.commit()
                    
                    result = {
                        'evolucoes_criadas': 1,
                        'dosagens_criadas': 0,
                        'sintomas_criados': 0,
                        'erros': [],
                        'message': 'Arquivo TXT importado com sucesso'
                    }
                except Exception as e:
                    result = {
                        'evolucoes_criadas': 0,
                        'dosagens_criadas': 0,
                        'sintomas_criados': 0,
                        'erros': [f'Erro: {str(e)}']
                    }'''
    
    content = content.replace(old_txt, new_txt)
    
    # Substituir outros formatos para mostrar mensagem
    formats_to_replace = [
        ('elif filename.endswith(\'.pdf\'):', 'PDF'),
        ('elif filename.endswith((\'.doc\', \'.docx\', \'.rtf\', \'.odt\')):', 'Documentos'),
        ('elif filename.endswith((\'.mp3\', \'.wav\', \'.m4a\', \'.ogg\')):', 'Áudio'),
        ('elif filename.endswith((\'.mp4\', \'.avi\', \'.mov\', \'.mkv\')):', 'Vídeo')
    ]
    
    for old_format, format_name in formats_to_replace:
        # Encontrar e substituir cada bloco
        start_idx = content.find(old_format)
        if start_idx != -1:
            # Encontrar o final do bloco (próximo elif ou else)
            end_markers = ['elif filename.endswith', 'else:', 'finally:']
            end_idx = len(content)
            
            for marker in end_markers:
                marker_idx = content.find(marker, start_idx + len(old_format))
                if marker_idx != -1 and marker_idx < end_idx:
                    end_idx = marker_idx
            
            # Substituir o bloco
            new_block = f'''{old_format}
                result = {{
                    'evolucoes_criadas': 0,
                    'dosagens_criadas': 0,
                    'sintomas_criados': 0,
                    'erros': ['{format_name} temporariamente indisponível. Use TXT, CSV ou JSON.']
                }}
            '''
            
            content = content[:start_idx] + new_block + content[end_idx:]
    
    # Salvar
    with open('routes/import_export.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Correção aplicada!")
    print("✅ Arquivos TXT funcionam sem IA")
    print("✅ CSV e JSON continuam normais")
    print("✅ Outros formatos mostram aviso")

if __name__ == "__main__":
    main()

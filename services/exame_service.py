import os
from werkzeug.utils import secure_filename
from models import Exame, ExameImagem, ExameLabResultado, db
from datetime import datetime
import uuid

def criar_exame(data, files=None):
    paciente_id = data.get('paciente_id')
    profissional_id = data.get('profissional_id')
    data_exame_str = data.get('data_exame')
    tipo_exame = data.get('tipo_exame')
    titulo = data.get('titulo')
    descricao = data.get('descricao')
    valor = data.get('valor')
    unidade = data.get('unidade')

    if not paciente_id:
        return {"error": "ID do paciente é obrigatório"}, 400
    if not tipo_exame or tipo_exame not in ['texto', 'arquivo', 'numerico']:
        return {"error": "Tipo de exame inválido. Deve ser 'texto', 'arquivo' ou 'numerico'"}, 400
    if not titulo:
        return {"error": "Título do exame é obrigatório"}, 400
    if tipo_exame == 'texto' and not descricao:
        return {"error": "Descrição é obrigatória para exames de texto"}, 400
    if tipo_exame == 'numerico' and not valor:
        return {"error": "Valor é obrigatório para exames numéricos"}, 400

    try:
        data_exame = datetime.strptime(data_exame_str, '%Y-%m-%d') if data_exame_str else datetime.utcnow()
    except ValueError:
        return {"error": "Formato de data inválido. Use YYYY-MM-DD"}, 400

    novo_exame = Exame(
        paciente_id=paciente_id,
        profissional_id=profissional_id,
        data_exame=data_exame,
        tipo_exame=tipo_exame,
        titulo=titulo,
        descricao=descricao,
        valor=valor,
        unidade=unidade
    )

    db.session.add(novo_exame)
    db.session.commit()

    # Processar arquivos se for exame do tipo 'arquivo'
    if tipo_exame == 'arquivo' and files:
        arquivos = files.getlist('arquivos')
        for arq in arquivos:
            if arq.filename == '':
                continue
            filename = secure_filename(arq.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            # Note: filepath creation would need current_app context
            
            nova_imagem = ExameImagem(
                exame_id=novo_exame.id,
                arquivo_nome=filename,
                arquivo_caminho=unique_filename,
                laudo=descricao or ''
            )
            db.session.add(nova_imagem)

    db.session.commit()
    return novo_exame.to_dict(), 201

def atualizar_exame(exame_id, data):
    exame = Exame.query.get(exame_id)
    if not exame:
        return {"error": "Exame não encontrado"}, 404
    
    if 'data_exame' in data:
        try:
            exame.data_exame = datetime.strptime(data['data_exame'], '%Y-%m-%d')
        except ValueError:
            return {"error": "Formato de data inválido. Use YYYY-MM-DD"}, 400
    
    if 'tipo_exame' in data:
        exame.tipo_exame = data['tipo_exame']
    
    db.session.commit()
    return exame.to_dict()

def excluir_exame(exame_id):
    exame = Exame.query.get(exame_id)
    if not exame:
        return {"error": "Exame não encontrado"}, 404
    
    db.session.delete(exame)
    db.session.commit()
    return {"message": "Exame excluído com sucesso"}, 200

def listar_exames_paciente(paciente_id):
    exames = Exame.query.filter_by(paciente_id=paciente_id).all()
    return [exame.to_dict() for exame in exames]

def obter_exame(exame_id):
    exame = Exame.query.get(exame_id)
    if not exame:
        return {"error": "Exame não encontrado"}, 404
    return exame.to_dict()

def listar_imagens_exame(exame_id):
    imagens = ExameImagem.query.filter_by(exame_id=exame_id).all()
    return [img.to_dict() for img in imagens]

def listar_resultados_exame(exame_id):
    resultados = ExameLabResultado.query.filter_by(exame_id=exame_id).all()
    return [res.to_dict() for res in resultados]

def excluir_imagem(imagem_id, upload_folder):
    imagem = ExameImagem.query.get(imagem_id)
    if not imagem:
        return {"error": "Imagem não encontrada"}, 404
    
    filepath = os.path.join(upload_folder, imagem.arquivo_caminho)
    if os.path.exists(filepath):
        os.remove(filepath)
    
    db.session.delete(imagem)
    db.session.commit()
    return {"message": "Imagem excluída com sucesso"}, 200

def atualizar_resultado(resultado_id, data):
    resultado = ExameLabResultado.query.get(resultado_id)
    if not resultado:
        return {"error": "Resultado não encontrado"}, 404
    
    resultado.teste_nome = data.get('teste_nome', resultado.teste_nome)
    resultado.valor = data.get('valor', resultado.valor)
    resultado.unidade = data.get('unidade', resultado.unidade)
    resultado.valor_referencia = data.get('valor_referencia', resultado.valor_referencia)
    
    db.session.commit()
    return resultado.to_dict()

def excluir_resultado(resultado_id):
    resultado = ExameLabResultado.query.get(resultado_id)
    if not resultado:
        return {"error": "Resultado não encontrado"}, 404
    
    db.session.delete(resultado)
    db.session.commit()
    return {"message": "Resultado excluído com sucesso"}, 200

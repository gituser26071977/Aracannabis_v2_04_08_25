"""
Rotas para geração e download de Laudos de HC (Health Cannabis).

P0-01 (Missão 18): Path Traversal eliminado.
- secure_filename em qualquer input do usuário
- validação por UUID (laudos são gerados como <uuid>.pdf)
- bloqueio de '..' e caminhos absolutos
- bloqueio de symlink (uso de os.path.realpath + verificação de prefixo)
- validação de tenant: o filename deve corresponder a um exame pertencente
  ao tenant do JWT (g.current_association). Se não houver registro,
  o download é negado.
"""
from flask import Blueprint, request, jsonify, send_file, current_app, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from sqlalchemy import select
import os
import re
import uuid as _uuid

from models import db, Exame, ExameImagem
from services.hc_report_service import HCReportService

hc_report_bp = Blueprint('hc_report', __name__)
service = HCReportService()

# Filenames gerados pelo service seguem o padrão "<uuid>_laudo.pdf".
# Esta regex é o ÚNICO formato aceitável para download.
_UUID_FILENAME_RE = re.compile(r'^[a-f0-9]{32}_laudo\.pdf$', re.IGNORECASE)


def _validate_filename(filename: str) -> bool:
    """
    Retorna True somente se o filename é um UUID válido seguido de '_laudo.pdf'.

    Bloqueia:
    - path traversal: '../', '..\\', '/etc/passwd'
    - caminhos absolutos: '/...', 'C:\\...'
    - symlinks apontando para fora do upload_folder
    - caracteres não-ASCII / caracteres especiais
    """
    if not filename or not isinstance(filename, str):
        return False
    # Bloqueia path separators e caracteres de traversal
    if '/' in filename or '\\' in filename or '..' in filename:
        return False
    # Bloqueia caminhos absolutos
    if filename.startswith(('/', '\\')):
        return False
    # Filename deve casar com o padrão UUID gerado pelo service
    if not _UUID_FILENAME_RE.match(filename):
        return False
    # Sanitização extra com secure_filename (no-op se já passou nos testes acima,
    # mas garante que nenhum path separator sobreviva)
    safe = secure_filename(filename)
    return safe == filename


@hc_report_bp.route('/generate', methods=['POST'])
@jwt_required()
def gerar_laudo_hc():
    data = request.get_json()
    profissional_id = get_jwt_identity()
    paciente_id = data.get('paciente_id')
    justificativa = data.get('justificativa_medica')

    if not paciente_id:
        return jsonify({'error': 'ID do paciente é obrigatório'}), 400

    try:
        filename = service.gerar_laudo_hc(profissional_id, paciente_id, justificativa)

        # Re-validar o filename gerado pelo service antes de devolver na URL.
        if not _validate_filename(filename):
            current_app.logger.error(
                "hc_report.generate: filename gerado pelo service é inseguro: %r",
                filename,
            )
            return jsonify({'error': 'Falha ao gerar laudo (filename inválido)'}), 500

        upload_folder = current_app.config.get('UPLOAD_FOLDER_EXAMES', 'uploads')
        file_path = os.path.realpath(os.path.join(upload_folder, filename))

        return jsonify({
            'success': True,
            'message': 'Laudo de HC gerado com sucesso',
            'filename': filename,
            'url': f'/api/reports/hc/download/{filename}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# P0-12: o tenant NÃO pode vir de X-Association-ID; vem só do JWT (g.current_association)
# que é populado por middleware/tenant_middleware.py a partir do JWT.
@hc_report_bp.route('/download/<string:filename>', methods=['GET'])
@jwt_required()
def download_laudo(filename):
    """
    Download seguro de laudo HC.

    Validações aplicadas (P0-01):
      1. Filename é UUID válido + _laudo.pdf
      2. Sem '..', '/', '\\', caminhos absolutos
      3. realpath() do arquivo resolvido está dentro do upload_folder
      4. Não é symlink para fora
      5. Existe ExameImagem (ou Exame) cujo arquivo_caminho == filename
         E cujo Exame.associacao_id == g.current_association.id
    """
    # 1) Validação estática do filename
    if not _validate_filename(filename):
        current_app.logger.warning(
            "hc_report.download: filename inválido/rejeitado: %r (user=%s)",
            filename, get_jwt_identity(),
        )
        return jsonify({'error': 'Filename inválido'}), 400

    upload_folder = current_app.config.get('UPLOAD_FOLDER_EXAMES', 'uploads')
    upload_folder_abs = os.path.realpath(upload_folder)
    file_path = os.path.realpath(os.path.join(upload_folder_abs, filename))

    # 2) Prevenir escape de diretório (symlink ou '..')
    if not file_path.startswith(upload_folder_abs + os.sep):
        current_app.logger.warning(
            "hc_report.download: tentativa de path traversal detectada: %r",
            filename,
        )
        return jsonify({'error': 'Acesso negado'}), 403

    # 3) Verificar existência física do arquivo
    if not os.path.isfile(file_path):
        return jsonify({'error': 'Arquivo não encontrado'}), 404

    # 4) Validação de tenant: o filename deve corresponder a um registro
    # ExameImagem ou Exame que pertença ao tenant do JWT.
    profissional_id = int(get_jwt_identity())
    current_assoc_id = getattr(g, 'current_association', None)
    current_assoc_id = current_assoc_id.id if current_assoc_id else None

    if current_assoc_id is None:
        return jsonify({'error': 'Tenant não resolvido para este usuário'}), 403

    # Buscar o exame ao qual o filename pertence (ExameImagem.arquivo_caminho)
    stmt = select(ExameImagem).where(ExameImagem.arquivo_caminho == filename)
    img = db.session.execute(stmt).scalar_one_or_none()

    if img is None:
        # Fallback: filename pode ser de HCReport (não está em ExameImagem).
        # Nesse caso a propriedade do arquivo é derivada do próprio gerador.
        # Aqui exigimos um Exame cuja associacao_id casa com o tenant E
        # cujo filename bate com um padrão conhecido (registrado em log).
        # Por segurança, retornamos 404 para evitar leak de existência.
        return jsonify({'error': 'Arquivo não encontrado'}), 404

    # Carregar Exame relacionado para checar tenant
    exame = db.session.get(Exame, img.exame_id)
    if exame is None or exame.associacao_id != current_assoc_id:
        current_app.logger.warning(
            "hc_report.download: tenant mismatch filename=%r user=%s assoc=%s file_assoc=%s",
            filename, profissional_id, current_assoc_id,
            exame.associacao_id if exame else None,
        )
        return jsonify({'error': 'Acesso negado'}), 403

    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename,
    )

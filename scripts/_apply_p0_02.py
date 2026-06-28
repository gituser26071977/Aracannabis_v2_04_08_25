"""Aplicar P0-02 em routes/exames.py — substituir bloco servir_arquivo_exame."""
import re

PATH = 'routes/exames.py'
with open(PATH, 'rb') as f:
    data = f.read()

# Encontra o trecho a partir do comentário '# Rota para servir arquivos de exames'
# até (mas não incluindo) o próximo bloco de rota para gráfico.
start_marker = b"# Rota para servir arquivos de exames\n"
end_marker = b"\n# Rota para gerar dados de gr\xc3\xa1fico para exames num\xc3\xa9ricos"

start = data.find(start_marker)
assert start != -1, "start marker not found"
end = data.find(end_marker, start)
assert end != -1, "end marker not found"

OLD_LEN = end - start
print(f"Replacing bytes {start}..{end} (len={OLD_LEN})")

NEW = b"""# P0-02 (Miss\xc3\xa3o 18): servir arquivo de exame agora exige:
#   - @jwt_required (autentica\xc3\xa7\xc3\xa3o obrigat\xc3\xb3ria)
#   - Valida\xc3\xa7\xc3\xa3o de filename (sem '..', '/', '\\\\', absoluto, s\xc3\xb3 UUID_<nome>)
#   - Valida\xc3\xa7\xc3\xa3o de tenant via banco (Exame.associacao_id == g.current_association.id)
#   - Bloqueio de symlink/path traversal via realpath() + startswith()
from sqlalchemy import select as _select
import re as _re

_EXAME_FILE_RE = _re.compile(r'^[a-f0-9]{32}_[A-Za-z0-9._-]+$')


def _validate_exame_filename(filename):
    if not filename or not isinstance(filename, str):
        return False
    if '/' in filename or '\\\\' in filename or '..' in filename:
        return False
    if filename.startswith(('/', '\\\\')):
        return False
    if not _EXAME_FILE_RE.match(filename):
        return False
    return secure_filename(filename) == filename


@exames_bp.route('/exames/arquivos/<string:filename>')
@jwt_required()
def servir_arquivo_exame(filename):
    \"\"\"
    Servir arquivo de exame de forma segura (P0-02).

    Pr\xc3\xa9-condi\xc3\xa7\xc3\xb5es:
      1. JWT v\xc3\xa1lido (qualquer profissional autenticado).
      2. Filename bate no padr\xc3\xa3o UUID_{nome}.
      3. Existe ExameImagem com esse arquivo_caminho E o Exame correspondente
         pertence ao tenant do JWT (g.current_association.id).
      4. Arquivo real est\xc3\xa1 dentro de UPLOAD_FOLDER_EXAMES (anti symlink).
    \"\"\"
    if not _validate_exame_filename(filename):
        current_app.logger.warning(
            \"exames.servir_arquivo_exame: filename inv\xc3\xa1lido: %r\", filename,
        )
        return jsonify({\"error\": \"Filename inv\xc3\xa1lido\"}), 400

    uploads_dir = os.path.realpath(
        os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER_EXAMES'])
    )
    file_path = os.path.realpath(os.path.join(uploads_dir, filename))
    if not file_path.startswith(uploads_dir + os.sep):
        current_app.logger.warning(
            \"exames.servir_arquivo_exame: tentativa de path traversal: %r\", filename,
        )
        return jsonify({\"error\": \"Acesso negado\"}), 403

    current_assoc = getattr(g, 'current_association', None)
    current_assoc_id = current_assoc.id if current_assoc else None
    if current_assoc_id is None:
        return jsonify({\"error\": \"Tenant n\xc3\xa3o resolvido\"}), 403

    # Cruzar com banco: o filename deve pertencer a um Exame do tenant.
    stmt = _select(ExameImagem).where(ExameImagem.arquivo_caminho == filename)
    img = db.session.execute(stmt).scalar_one_or_none()
    if img is None:
        return jsonify({\"error\": \"Arquivo n\xc3\xa3o encontrado\"}), 404

    exame = db.session.get(Exame, img.exame_id)
    if exame is None or exame.associacao_id != current_assoc_id:
        current_app.logger.warning(
            \"exames.servir_arquivo_exame: tenant mismatch filename=%r user=%s assoc=%s file_assoc=%s\",
            filename, get_jwt_identity(), current_assoc_id,
            exame.associacao_id if exame else None,
        )
        return jsonify({\"error\": \"Acesso negado\"}), 403

    if not os.path.isfile(file_path):
        return jsonify({\"error\": \"Arquivo n\xc3\xa3o encontrado\"}), 404

    return send_from_directory(uploads_dir, filename)
"""

new_data = data[:start] + NEW + data[end:]
with open(PATH, 'wb') as f:
    f.write(new_data)
print(f"Written {len(new_data)} bytes (was {len(data)})")

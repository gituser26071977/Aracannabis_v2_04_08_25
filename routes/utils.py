from flask import Blueprint, jsonify
from services.brasil_api_service import BrasilAPIService

utils_bp = Blueprint('utils_bp', __name__)

@utils_bp.route('/cep/<string:cep>', methods=['GET'])
def get_cep_info(cep):
    """
    GET /api/utils/cep/<cep>
    Busca informações de endereço pelo CEP usando BrasilAPI.
    """
    result = BrasilAPIService.get_address_by_cep(cep)
    if result['success']:
        return jsonify(result), 200
    return jsonify(result), 400

@utils_bp.route('/cnpj/<string:cnpj>', methods=['GET'])
def get_cnpj_info(cnpj):
    """
    GET /api/utils/cnpj/<cnpj>
    Busca informações de empresa pelo CNPJ usando BrasilAPI.
    """
    result = BrasilAPIService.get_cnpj_info(cnpj)
    if result['success']:
        return jsonify(result), 200
    return jsonify(result), 400

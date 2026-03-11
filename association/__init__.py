from flask import Blueprint

association_bp = Blueprint('association', __name__)

from . import routes

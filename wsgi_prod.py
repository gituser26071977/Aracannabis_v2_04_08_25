"""WSGI de produção — oculta o header Server e wrappers de segurança.

Roda com gunicorn (como docker-compose.prod.yml): a entrada é
`wsgi_prod:application` para que o header `Server` não exponha
Werkzeug/versão Python (hardening — sem fingerprinting de stack).
"""

from app_cors_livre import create_app

application = create_app()


class _HideServer:
    """Wraper WSGI que remove o header Server antes de enviar."""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        def _start_response(status, headers, exc_info=None):
            filtered = [(k, v) for k, v in headers if k.lower() != "server"]
            filtered.append(("Server", "AraOS"))
            return start_response(status, filtered, exc_info)

        return self.app(environ, _start_response)


application = _HideServer(application)

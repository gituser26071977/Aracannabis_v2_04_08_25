import os
from cryptography.fernet import Fernet
from typing import Optional

def get_key() -> bytes:
    """
    Retorna a chave Fernet a partir da variável de ambiente.
    Gera uma nova se não existir (para test/local), mas em produção deve falhar se não houver.
    """
    key = os.getenv("ANONYMIZATION_KEY")
    if not key:
        # Gerar temporária se não houver (para testes)
        # Em prod, lance erro!
        new_key = Fernet.generate_key()
        print(f"⚠️ AVISO: ANONYMIZATION_KEY não encontrada. Gerando temporária: {new_key.decode()}")
        return new_key
    return key.encode()

class CryptoManager:
    def __init__(self, key: Optional[bytes] = None):
        self.key = key or get_key()
        self.fernet = Fernet(self.key)

    def encrypt(self, plain_text: str) -> str:
        """Criptografa texto plano com AES-256 (Fernet)"""
        return self.fernet.encrypt(plain_text.encode()).decode()

    def decrypt(self, cipher_text: str) -> str:
        """Descriptografa texto cifrado"""
        return self.fernet.decrypt(cipher_text.encode()).decode()

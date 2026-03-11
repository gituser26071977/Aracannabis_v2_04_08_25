
import requests
import json

BASE_URL = "http://localhost:5002/api"
TEST_USER = {
    "usuario": "admin",
    "senha": "Aracannabis@2025"
}

def debug_dosagens():
    print("🔐 Login...")
    resp = requests.post(f"{BASE_URL}/auth/login", json=TEST_USER)
    if resp.status_code != 200:
        print("Login failed")
        return
    
    token = resp.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    
    # Listar pacientes para pegar ID
    print("🔍 Buscando paciente...")
    p_resp = requests.get(f"{BASE_URL}/pacientes/", headers=headers)
    pacientes = p_resp.json().get('pacientes', [])
    if not pacientes:
        print("Sem pacientes")
        return
    
    paciente_id = pacientes[0]['id']
    print(f"Paciente ID: {paciente_id}")
    
    # Pegar grafico
    print("📊 Buscando gráfico...")
    g_resp = requests.get(f"{BASE_URL}/dosagens/grafico/paciente/{paciente_id}", headers=headers)
    print(f"Status: {g_resp.status_code}")
    try:
        data = g_resp.json()
        print("JSON Structure:")
        print(json.dumps(data, indent=2))
    except:
        print("Response text:", g_resp.text)

if __name__ == "__main__":
    debug_dosagens()

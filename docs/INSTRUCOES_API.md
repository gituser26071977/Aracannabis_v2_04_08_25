# 📚 Instruções de Uso da API Aracannabis

## 🔐 Autenticação
Para acessar a API, primeiro obtenha um token de autenticação:

```bash
curl -X POST http://localhost:5002/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"usuario": "admin", "senha": "Aracannabis@2025"}'
```

**Resposta de Exemplo:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "message": "Login realizado com sucesso",
  "user": {
    "id": 1,
    "nome": "Administrador",
    "usuario": "admin",
    "crm": "ADMIN001"
  }
}
```

Use o token em requisições subsequentes:
```bash
curl -H "Authorization: Bearer <SEU_TOKEN>" http://localhost:5002/api/pacientes
```

## 📋 Endpoints Principais

### 👥 Pacientes
- `GET /api/pacientes` - Listar todos pacientes
- `GET /api/pacientes/{id}` - Detalhes de um paciente
- `POST /api/pacientes` - Criar novo paciente
```json
{
  "nome": "Fulano da Silva",
  "data_nascimento": "1990-01-15",
  "telefone": "(11) 99999-9999"
}
```

### 📈 Sintomas
- `GET /api/sintomas/paciente/{id}` - Sintomas de um paciente
- `POST /api/sintomas` - Registrar novo sintoma
```json
{
  "paciente_id": 7,
  "sintoma": "Dor de cabeça",
  "intensidade": 8,
  "data": "2025-07-21"
}
```

### 💊 Dosagens
- `GET /api/dosagens/paciente/{id}` - Dosagens de um paciente
- `POST /api/dosagens` - Registrar nova dosagem
```json
{
  "paciente_id": 7,
  "dosagem": "10mg de CBD",
  "data": "2025-07-21"
}
```

### 🏥 Evoluções Médicas
- `GET /api/evolucoes/paciente/{id}` - Evoluções de um paciente
- `POST /api/evolucoes` - Registrar nova evolução
```json
{
  "paciente_id": 7,
  "nota_evolucao": "Paciente relatou melhora significativa"
}
```

### 🧪 Exames
- `GET /api/pacientes/{id}/exames` - Exames de um paciente
- `GET /api/exames/{id}/imagens` - Imagens de um exame

## 📊 Gráficos
- `GET /api/sintomas/grafico/paciente/{id}?periodo=integral` - Gráfico de sintomas
- `GET /api/dosagens/grafico/paciente/{id}?periodo=integral` - Gráfico de dosagens

Parâmetros:
- `periodo`: `7dias`, `30dias`, `integral`

## 🧪 Testando a API
### Verificar status:
```bash
curl http://localhost:5002/api/status
```

### Listar pacientes:
```bash
curl -H "Authorization: Bearer <SEU_TOKEN>" \
  http://localhost:5002/api/pacientes
```

## ⚠️ Códigos de Erro Comuns
- `401 Unauthorized`: Token inválido ou expirado
- `404 Not Found`: Recurso não encontrado
- `500 Internal Server Error`: Erro no servidor

## 🔗 Documentação Completa
A documentação Swagger completa está disponível em:  
http://localhost:5002

## 📝 Exemplo em JavaScript (Axios)
```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5002/api',
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  }
});

// Obter lista de pacientes
async function getPacientes() {
  try {
    const response = await api.get('/pacientes');
    return response.data;
  } catch (error) {
    console.error('Erro ao obter pacientes:', error);
  }
}
```

Atualizado em: 21/Jul/2025  
Versão da API: 2.0

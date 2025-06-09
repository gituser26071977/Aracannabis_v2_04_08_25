# 🏥 CAMPO "EM TRATAMENTO" - SISTEMA ARACANNABIS

## 🎯 **O que é o Campo "Em Tratamento"?**

O campo `em_tratamento` é um **indicador booleano** (verdadeiro/falso) que identifica se um paciente está **atualmente em tratamento ativo** com cannabis medicinal.

## 📋 **Como Funciona Atualmente**

### **🔧 Estrutura no Banco de Dados**
```sql
em_tratamento BOOLEAN DEFAULT FALSE NOT NULL
```

- **Tipo**: Boolean (verdadeiro/falso)
- **Padrão**: `false` (não em tratamento)
- **Obrigatório**: Sim (não pode ser nulo)

### **📊 Uso no Sistema**

#### **1. Estatísticas na Lista de Pacientes**
```javascript
// Contador automático na PatientList.js
const patientsInTreatment = patients.filter(patient => patient.em_tratamento).length;
const totalPatients = patients.length;
```

**Exibe:**
- 📊 **Total**: X pacientes
- ✅ **Em tratamento**: Y pacientes

#### **2. Dashboard de Estatísticas**
```javascript
// Endpoint: GET /api/pacientes/dashboard
{
  "total_pacientes": 10,
  "em_tratamento": 7,
  "taxa_tratamento": 70.0
}
```

## ⚠️ **PROBLEMA ATUAL: Campo Não Está no Formulário**

### **❌ O que está faltando:**

1. **Formulário de Paciente** (`PatientForm.js`):
   - ❌ **Não tem checkbox** para "Em Tratamento"
   - ❌ **Não envia o campo** para o backend
   - ❌ **Sempre fica como `false`** por padrão

2. **Edição de Paciente**:
   - ❌ **Não é possível alterar** o status de tratamento
   - ❌ **Campo invisível** para o usuário

## 🔧 **Como Corrigir - Implementação Necessária**

### **1. Adicionar ao Formulário de Paciente**

**Localização**: `frontend/src/components/PatientForm.js`

```javascript
// Adicionar ao estado inicial
const [formData, setFormData] = useState({
  // ... outros campos
  em_tratamento: initialData?.em_tratamento || false
});

// Adicionar ao JSX do formulário
<Grid item xs={12}>
  <FormControlLabel
    control={
      <Checkbox
        checked={formData.em_tratamento}
        onChange={(e) => setFormData({...formData, em_tratamento: e.target.checked})}
        name="em_tratamento"
        color="primary"
      />
    }
    label="Paciente está em tratamento ativo com cannabis medicinal"
  />
</Grid>
```

### **2. Adicionar à Tabela de Pacientes**

**Localização**: `frontend/src/components/PatientList.js`

```javascript
// Adicionar coluna na tabela
<TableCell>Status</TableCell>

// Adicionar célula com chip colorido
<TableCell>
  <Chip
    label={patient.em_tratamento ? "Em Tratamento" : "Não Tratando"}
    color={patient.em_tratamento ? "success" : "default"}
    size="small"
  />
</TableCell>
```

### **3. Adicionar aos Detalhes do Paciente**

**Localização**: `frontend/src/components/PatientDetails.js`

```javascript
<Grid item xs={12} sm={6}>
  <Typography variant="body2" color="text.secondary">
    Status do Tratamento
  </Typography>
  <Chip
    label={patient.em_tratamento ? "Em Tratamento Ativo" : "Não em Tratamento"}
    color={patient.em_tratamento ? "success" : "default"}
    icon={patient.em_tratamento ? <CheckCircleIcon /> : <CancelIcon />}
  />
</Grid>
```

## 🎯 **Critérios Sugeridos para "Em Tratamento"**

### **✅ Paciente DEVE estar "Em Tratamento" quando:**

1. **Tem prescrição ativa** de cannabis medicinal
2. **Está seguindo protocolo** de dosagem
3. **Tem consultas regulares** agendadas
4. **Está monitorando sintomas** ativamente
5. **Tem dosagens registradas** recentemente

### **❌ Paciente NÃO deve estar "Em Tratamento" quando:**

1. **Parou o tratamento** temporariamente
2. **Concluiu o ciclo** de tratamento
3. **Está em pausa** por orientação médica
4. **Mudou para outro tratamento**
5. **Apenas em consulta inicial** (ainda não iniciou)

## 🔄 **Automação Inteligente (Sugestão Futura)**

### **Atualização Automática Baseada em:**

1. **Dosagens Recentes**:
   ```javascript
   // Se tem dosagem nos últimos 30 dias = Em Tratamento
   const temDosagemRecente = dosagens.some(d => 
     new Date(d.data) > new Date(Date.now() - 30*24*60*60*1000)
   );
   ```

2. **Consultas Agendadas**:
   ```javascript
   // Se tem consulta futura agendada = Em Tratamento
   const temConsultaFutura = consultas.some(c => 
     new Date(c.data_hora) > new Date() && c.status !== 'cancelada'
   );
   ```

3. **Evolução Médica**:
   ```javascript
   // Se tem evolução recente = Em Tratamento
   const temEvolucaoRecente = evolucoes.some(e => 
     new Date(e.data_evolucao) > new Date(Date.now() - 60*24*60*60*1000)
   );
   ```

## 📊 **Relatórios e Análises Possíveis**

### **Com o campo "Em Tratamento" funcionando:**

1. **Taxa de Adesão ao Tratamento**
2. **Pacientes Ativos vs Inativos**
3. **Tempo Médio de Tratamento**
4. **Eficácia por Período**
5. **Pacientes que Abandonaram**

## 🚀 **Implementação Prioritária**

### **Ordem de Implementação:**

1. **🔥 URGENTE**: Adicionar checkbox no formulário
2. **📊 IMPORTANTE**: Mostrar status na tabela
3. **📋 ÚTIL**: Exibir nos detalhes do paciente
4. **🤖 FUTURO**: Automação inteligente

## 💡 **Exemplo de Uso Prático**

### **Cenário Real:**

1. **Dr. João** cadastra **Maria Silva**
2. **Marca checkbox** "Em Tratamento" ✅
3. **Sistema mostra**:
   - Lista: "Em tratamento: 8 pacientes"
   - Tabela: Chip verde "Em Tratamento"
   - Dashboard: Taxa 80% em tratamento

4. **Após 6 meses**, Maria conclui tratamento
5. **Dr. João desmarca** checkbox ❌
6. **Sistema atualiza** estatísticas automaticamente

---

**🎯 Conclusão**: O campo existe no banco e backend, mas **precisa ser exposto na interface** para que os profissionais possam gerenciá-lo adequadamente.

# 🌿 Sistema de Anúncios - Aracannabis

## 📋 Resumo da Implementação

Foi implementado um sistema completo de anúncios para monetizar a versão free do sistema Aracannabis, permitindo que empresas da indústria de cannabis anunciem seus produtos e serviços.

## 🎯 Objetivos Alcançados

✅ **Sistema de Anúncios Completo**
- API backend para gerenciar anúncios
- Componente frontend responsivo
- Analytics e tracking de cliques
- Integração com banco de dados

✅ **Plano Free com Anúncios**
- Novo plano "Free" adicionado à página de preços
- Anúncios exibidos para usuários não logados
- Monetização através de parceiros da indústria

✅ **Analytics e Métricas**
- Tracking de visualizações e cliques
- Estatísticas detalhadas por anúncio
- CTR (Click-Through Rate) automático
- Relatórios por categoria

## 🏗️ Arquitetura Implementada

### Backend (Python/Flask)

#### 1. Rota de Anúncios (`routes/anuncios.py`)
```python
# Endpoints implementados:
GET  /api/anuncios              # Listar anúncios
GET  /api/anuncios?limite=N     # Listar com limite
GET  /api/anuncios?categoria=X  # Filtrar por categoria
POST /api/anuncios/{id}/view    # Registrar visualização
POST /api/anuncios/{id}/click   # Registrar clique
GET  /api/anuncios/stats        # Estatísticas
```

#### 2. Banco de Dados
```sql
-- Tabela principal de anúncios
CREATE TABLE anuncios (
    id INTEGER PRIMARY KEY,
    titulo TEXT NOT NULL,
    descricao TEXT NOT NULL,
    imagem TEXT,
    url TEXT NOT NULL,
    empresa TEXT NOT NULL,
    categoria TEXT NOT NULL,
    preco TEXT,
    destaque TEXT,
    tipo TEXT NOT NULL,
    ativo BOOLEAN DEFAULT 1,
    data_inicio DATE,
    data_fim DATE,
    visualizacoes INTEGER DEFAULT 0,
    cliques INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de analytics
CREATE TABLE anuncios_analytics (
    id INTEGER PRIMARY KEY,
    anuncio_id INTEGER,
    tipo_evento TEXT NOT NULL, -- 'view' ou 'click'
    user_agent TEXT,
    ip_address TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Frontend (React/Material-UI)

#### 1. Componente AdBanner (`frontend/src/components/AdBanner.js`)
```jsx
// Três layouts diferentes:
<AdBanner position="sidebar" />   // Coluna lateral
<AdBanner position="banner" />    // Banner horizontal
<AdBanner position="inline" />    // Dentro do conteúdo
```

#### 2. Integração nas Páginas
- **Página Inicial**: Banner de anúncios para usuários não logados
- **Página de Planos**: Novo plano "Free" com anúncios
- **Futuro**: Sidebar em páginas internas (versão free)

## 📊 Categorias de Anúncios

### 1. **Produtos** 🌿
- Óleos medicinais
- Extratos e concentrados
- Produtos farmacêuticos

### 2. **Educação** 📚
- Cursos de capacitação
- Certificações profissionais
- Workshops e seminários

### 3. **Serviços** 🔬
- Laboratórios de análise
- Consultoria médica
- Telemedicina

### 4. **Equipamentos** ⚙️
- Equipamentos de cultivo
- Tecnologia médica
- Dispositivos de vaporização

### 5. **Jurídico** ⚖️
- Assessoria jurídica
- Licenças e autorizações
- Compliance regulatório

## 💰 Modelo de Monetização

### Planos Implementados

#### 🆓 **Plano Free** (NOVO)
- **Preço**: Gratuito
- **Limitações**: Até 5 pacientes
- **Anúncios**: Sim (3-5 anúncios por página)
- **Funcionalidades**: Básicas
- **Target**: Profissionais iniciantes

#### 🏥 **Plano Profissional**
- **Preço**: R$ 180/mês
- **Limitações**: Sem limites
- **Anúncios**: Não
- **Funcionalidades**: Completas
- **Target**: Profissionais estabelecidos

### Oportunidades de Receita

1. **Anúncios por Impressão (CPM)**
   - R$ 5-15 por 1.000 visualizações
   - Estimativa: 10.000 visualizações/mês = R$ 50-150

2. **Anúncios por Clique (CPC)**
   - R$ 0,50-2,00 por clique
   - Estimativa: 500 cliques/mês = R$ 250-1.000

3. **Anúncios Premium**
   - Posicionamento destacado
   - R$ 500-2.000/mês por anúncio

4. **Pacotes de Anunciantes**
   - Múltiplas posições
   - Desconto por volume
   - R$ 1.500-5.000/mês

## 🎨 Design e UX

### Princípios Seguidos
- **Não Intrusivo**: Anúncios integrados naturalmente
- **Relevante**: Focado na indústria de cannabis
- **Responsivo**: Funciona em todos os dispositivos
- **Performance**: Carregamento rápido e otimizado

### Layouts Implementados

#### 1. **Banner Horizontal**
```
┌─────────────────────────────────────────────┐
│ 📢 Parceiros Recomendados                   │
├─────────────────────────────────────────────┤
│ [IMG] Produto 1  [IMG] Produto 2  [IMG] ... │
└─────────────────────────────────────────────┘
```

#### 2. **Sidebar Vertical**
```
┌─────────────┐
│ 🌿 Parceiros│
├─────────────┤
│ [IMAGEM]    │
│ Título      │
│ Descrição   │
│ Preço       │
│ [Ver Mais]  │
├─────────────┤
│ [IMAGEM]    │
│ Título      │
│ ...         │
└─────────────┘
```

#### 3. **Inline (Conteúdo)**
```
┌─────────────────────────────────────┐
│ 📢 Anúncio Patrocinado              │
├─────────────────────────────────────┤
│ [IMG] Título do Produto             │
│       Descrição breve               │
│       Preço: R$ XXX,XX              │
└─────────────────────────────────────┘
```

## 📈 Analytics e Métricas

### Métricas Coletadas
- **Impressões**: Quantas vezes o anúncio foi visto
- **Cliques**: Quantas vezes foi clicado
- **CTR**: Taxa de cliques (cliques/impressões)
- **Origem**: IP e User-Agent do usuário
- **Timestamp**: Data e hora da interação

### Relatórios Disponíveis
1. **Estatísticas Gerais**
   - Total de anúncios ativos
   - Total de impressões
   - Total de cliques
   - CTR médio

2. **Top Anúncios**
   - Ranking por cliques
   - Performance individual
   - Comparação temporal

3. **Por Categoria**
   - Performance por segmento
   - Identificação de nichos
   - Otimização de conteúdo

## 🔧 Configuração e Deploy

### Requisitos
- Python 3.8+
- Flask
- SQLite3
- React 18+
- Material-UI 5+

### Instalação

1. **Backend**
```bash
# A rota já está registrada no app.py
# Tabelas são criadas automaticamente
python app.py
```

2. **Frontend**
```bash
# Componente já está importado
cd frontend
npm start
```

### Configuração de Anúncios

#### Adicionar Novo Anúncio (Manual)
```sql
INSERT INTO anuncios (titulo, descricao, imagem, url, empresa, categoria, preco, destaque, tipo, data_inicio, data_fim)
VALUES (
    'Título do Anúncio',
    'Descrição detalhada...',
    '/caminho/imagem.jpg',
    'https://site-anunciante.com',
    'Nome da Empresa',
    'Categoria',
    'R$ XXX,XX',
    'Destaque especial',
    'product',
    '2025-01-01',
    '2025-12-31'
);
```

#### Configurar Período de Exibição
```sql
-- Ativar anúncio
UPDATE anuncios SET ativo = 1 WHERE id = X;

-- Desativar anúncio
UPDATE anuncios SET ativo = 0 WHERE id = X;

-- Definir período
UPDATE anuncios SET 
    data_inicio = '2025-01-01',
    data_fim = '2025-12-31'
WHERE id = X;
```

## 🧪 Testes

### Script de Teste Automatizado
```bash
python test_anuncios_system.py
```

### Testes Manuais
1. **Página Inicial**
   - Acessar sem login
   - Verificar anúncios no banner
   - Testar cliques

2. **Página de Planos**
   - Verificar plano "Free"
   - Confirmar descrição dos anúncios

3. **API**
   - Testar endpoints
   - Verificar analytics
   - Validar CORS

## 🚀 Próximos Passos

### Fase 1: Validação (Concluída)
- ✅ Implementação básica
- ✅ Testes funcionais
- ✅ Integração frontend

### Fase 2: Otimização
- [ ] Dashboard de anunciantes
- [ ] Segmentação de audiência
- [ ] A/B testing de anúncios
- [ ] Otimização de performance

### Fase 3: Expansão
- [ ] Anúncios em vídeo
- [ ] Remarketing
- [ ] Programmatic advertising
- [ ] Mobile app integration

### Fase 4: Monetização Avançada
- [ ] Leilão de anúncios
- [ ] Targeting geográfico
- [ ] Anúncios nativos
- [ ] Partnerships estratégicas

## 💡 Estratégias de Vendas

### Para Anunciantes

#### 1. **Produtos Canábicos**
- **Pitch**: "Alcance profissionais de saúde que prescrevem cannabis"
- **Valor**: Audiência qualificada e segmentada
- **Preço**: R$ 1.000-3.000/mês

#### 2. **Educação e Cursos**
- **Pitch**: "Eduque os profissionais que mais precisam"
- **Valor**: Lead generation qualificado
- **Preço**: R$ 500-1.500/mês

#### 3. **Equipamentos Médicos**
- **Pitch**: "Equipamentos para quem trata com cannabis"
- **Valor**: B2B direto com decisores
- **Preço**: R$ 800-2.500/mês

#### 4. **Serviços Jurídicos**
- **Pitch**: "Conecte-se com profissionais que precisam de compliance"
- **Valor**: Alto valor por conversão
- **Preço**: R$ 1.200-4.000/mês

### Pacotes Promocionais

#### 🥉 **Pacote Básico** - R$ 800/mês
- 1 anúncio ativo
- Posição rotativa
- Relatório mensal
- Suporte por email

#### 🥈 **Pacote Profissional** - R$ 1.500/mês
- 2 anúncios ativos
- Posição preferencial
- Relatório semanal
- Suporte prioritário
- A/B testing

#### 🥇 **Pacote Premium** - R$ 3.000/mês
- 3 anúncios ativos
- Posição garantida
- Relatório diário
- Suporte dedicado
- Customização avançada
- Analytics detalhados

## 📞 Contato para Anunciantes

### Informações de Vendas
- **Email**: anuncios@aracannabis.com
- **WhatsApp**: (11) 99999-9999
- **Site**: www.aracannabis.com/anuncie

### Materiais de Apoio
- Kit de mídia com especificações
- Casos de sucesso
- Demonstração da plataforma
- Proposta comercial personalizada

## 🎉 Conclusão

O sistema de anúncios foi implementado com sucesso, oferecendo:

1. **Monetização Efetiva**: Nova fonte de receita através do plano free
2. **Experiência do Usuário**: Anúncios relevantes e não intrusivos
3. **Analytics Completos**: Métricas detalhadas para otimização
4. **Escalabilidade**: Arquitetura preparada para crescimento
5. **Facilidade de Gestão**: Interface simples para administração

O sistema está pronto para começar a gerar receita através de parcerias com empresas da indústria de cannabis, oferecendo valor tanto para anunciantes quanto para usuários do sistema.

---

**Data de Implementação**: 30/05/2025  
**Versão**: 1.0  
**Status**: ✅ Implementado e Testado

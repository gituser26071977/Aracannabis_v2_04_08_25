# Guia para Conexão à VPS usando Termius

O Termius é um cliente SSH multiplataforma que facilita a conexão e gerenciamento de servidores remotos. Este guia mostra como usar o Termius para se conectar à sua VPS da Hostinger.

## 1. Instalação do Termius

1. Baixe e instale o Termius do site oficial: [https://termius.com/download](https://termius.com/download)
2. Abra o Termius e crie uma conta ou faça login

## 2. Configuração da Conexão SSH

### Usando Interface Gráfica

1. Clique no botão "New Host" (Novo Host)
2. Preencha os seguintes campos:
   - **Label**: Um nome para identificar sua VPS (ex: "Aracannabis VPS")
   - **Address**: O endereço IP da sua VPS
   - **Username**: Seu nome de usuário na VPS (geralmente "root" para VPS da Hostinger)
   - **Password**: Sua senha (se estiver usando autenticação por senha)

3. Se estiver usando autenticação por chave SSH:
   - Clique na aba "Keys" (Chaves)
   - Clique em "New Key" (Nova Chave)
   - Cole sua chave privada no campo apropriado
   - Dê um nome à chave
   - Salve a chave
   - Volte à configuração do host e selecione a chave que você acabou de criar

4. Clique em "Save" (Salvar) para salvar a configuração do host

### Importando Credenciais do Termius

Se você tiver um arquivo de credenciais do Termius (como o que você compartilhou):

1. No Termius, vá para "Settings" (Configurações)
2. Selecione "Sync" (Sincronização)
3. Escolha "Import" (Importar)
4. Selecione o arquivo de credenciais
5. Siga as instruções na tela para completar a importação

## 3. Conectando-se à VPS

1. Na lista de hosts, localize sua VPS
2. Clique nela para iniciar a conexão
3. Se solicitado, confirme a autenticidade do host (geralmente na primeira conexão)
4. Você agora deve estar conectado à sua VPS via SSH

## 4. Executando Comandos

Uma vez conectado, você pode executar comandos diretamente no terminal do Termius:

1. Verifique se você está conectado como root ou um usuário com privilégios sudo
2. Siga as instruções no arquivo `vps_deploy_guide.md` para configurar e implantar a aplicação

## 5. Transferência de Arquivos com SFTP

O Termius também permite transferir arquivos facilmente:

1. Com o host selecionado, clique na aba "SFTP" na parte inferior da janela
2. Você verá um gerenciador de arquivos dividido em duas partes:
   - À esquerda: arquivos locais
   - À direita: arquivos remotos na VPS
3. Navegue até os diretórios desejados e arraste arquivos entre os painéis para transferi-los

## 6. Salvando Snippets para Comandos Frequentes

Para facilitar o deploy, você pode salvar snippets dos comandos mais usados:

1. Vá para a seção "Snippets" no menu lateral
2. Clique em "New Snippet" (Novo Snippet)
3. Dê um nome ao snippet (ex: "Reiniciar Nginx")
4. Cole o comando (ex: `sudo systemctl restart nginx`)
5. Salve o snippet
6. Para usar, basta clicar no snippet enquanto estiver conectado à VPS

## Dicas de Segurança

1. **Nunca compartilhe suas credenciais** ou chaves privadas com terceiros
2. Considere usar autenticação de dois fatores (2FA) para sua conta Termius
3. Desabilite o login por senha na sua VPS e use apenas chaves SSH para maior segurança
4. Mantenha o Termius atualizado para obter as últimas correções de segurança

Seguindo este guia e as instruções detalhadas no arquivo `vps_deploy_guide.md`, você poderá conectar-se à sua VPS e realizar o deploy da aplicação Aracannabis Prontuário de forma eficiente e segura.

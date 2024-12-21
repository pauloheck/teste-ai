# Guia de Segurança

## Controle de Versão e Arquivos Sensíveis

### Arquivos Protegidos
O `.gitignore` foi configurado para proteger os seguintes tipos de arquivos sensíveis:

1. **Arquivos de Ambiente e Configuração**
   - `.env` e variantes (exceto `.env.example`)
   - Arquivos de configuração local
   - Arquivos de segredos (secrets.yaml, credentials.json)

2. **Certificados e Chaves**
   - Arquivos de certificado (*.pem, *.crt, *.key)
   - Chaves privadas e certificados SSL/TLS
   - Arquivos de solicitação de certificado

3. **Dados Sensíveis**
   - Diretórios de dados privados
   - Arquivos de banco de dados
   - Arquivos CSV e planilhas
   - Logs e arquivos temporários

### Boas Práticas

1. **Antes de Commitar**
   - Sempre verifique `git status` antes de commit
   - Use `git add` com arquivos específicos em vez de `git add .`
   - Verifique `git diff --cached` antes do commit

2. **Proteção de Credenciais**
   - Nunca armazene senhas ou chaves no código
   - Use variáveis de ambiente para configurações sensíveis
   - Mantenha diferentes .env para desenvolvimento e produção

3. **Verificação de Segurança**
   ```bash
   # Verificar se arquivos sensíveis estão sendo rastreados
   git ls-files | grep -i 'secret\|password\|credential'
   
   # Verificar commits por conteúdo sensível
   git log -p | grep -i 'secret\|password\|credential'
   ```

4. **Em Caso de Exposição Acidental**
   - Altere imediatamente as credenciais expostas
   - Use `git filter-branch` ou BFG Repo-Cleaner para remover dados sensíveis
   - Notifique a equipe de segurança

### Configuração do Ambiente

1. **Arquivo .env**
   ```bash
   # Copie o template
   cp .env.example .env
   
   # Configure suas variáveis
   nano .env
   ```

2. **Verificação de Configuração**
   ```bash
   # Verifique se .env está ignorado
   git check-ignore .env
   
   # Verifique arquivos rastreados
   git ls-files
   ```

### Monitoramento Contínuo

1. **Hooks do Git**
   - Use pre-commit hooks para verificar dados sensíveis
   - Configure hooks para validar arquivos de configuração

2. **Revisão Regular**
   - Audite regularmente arquivos rastreados
   - Verifique permissões de arquivos
   - Mantenha o .gitignore atualizado

### Recursos Adicionais

- [Git Documentation - gitignore](https://git-scm.com/docs/gitignore)
- [GitHub - Collection of .gitignore templates](https://github.com/github/gitignore)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)

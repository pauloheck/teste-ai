# Ada 🤖

Ada é um sistema inteligente para geração e gestão de projetos, utilizando IA para automatizar e otimizar processos de desenvolvimento.

## 🎯 Visão Geral

A Ada combina várias tecnologias de IA para criar uma suite completa de ferramentas para desenvolvedores e gerentes de projeto, incluindo:

- 📚 **Sistema RAG (Retrieval-Augmented Generation)**
  - Consulta inteligente de documentos
  - Base de conhecimento pesquisável
  - Indexação automática de documentação

- 📋 **Geração de Épicos e User Stories**
  - Criação automatizada de épicos
  - Geração de user stories detalhadas
  - Templates personalizáveis

## 🚀 Começando

### Pré-requisitos

- Python 3.10 ou superior
- Poetry (gerenciador de dependências)
- Chave de API da OpenAI

### Instalação

1. Clone o repositório:
```bash
git clone [URL_DO_REPOSITORIO]
cd ada
```

2. Instale as dependências com Poetry:
```bash
poetry install
```


### Uso

Execute o sistema com:
```bash
poetry run ada
poetry run python src/api/run.py
```

## 🛠️ Funcionalidades

### Sistema RAG
- Carregamento e indexação de documentos
- Busca semântica em documentos
- Visualização de documentos relevantes

### Gerador de Épicos
- Geração de épicos baseada em descrições
- Criação automática de user stories
- Critérios de aceitação e métricas

## 📁 Estrutura do Projeto

```
ada/
├── data/               # Dados e documentos
├── src/               
│   ├── agents/        # Agentes de IA
│   ├── models/        # Modelos de dados
│   ├── utils/         # Utilitários
│   └── main.py        # Ponto de entrada
├── tests/             # Testes
├── .env              # Configurações
├── pyproject.toml    # Configuração Poetry
├── README.md         # Este arquivo
└── tasks.md          # Backlog do projeto
```

## 🔧 Tecnologias

- [LangChain](https://python.langchain.com/) - Framework de IA
- [OpenAI GPT-4](https://openai.com/) - Modelo de linguagem
- [MongoDB](https://www.mongodb.com/) - Banco de dados
- [Poetry](https://python-poetry.org/) - Gerenciamento de dependências

## 📊 Métricas e Analytics

A Ada inclui um sistema completo de métricas para acompanhamento de:
- Velocidade de desenvolvimento
- Qualidade de código
- Progresso do projeto
- Eficácia das sugestões de IA

## 🔒 Segurança

### Configuração do Ambiente
1. Copie o arquivo `.env.example` para `.env`:
```bash
cp .env.example .env
```

2. Configure suas variáveis de ambiente no arquivo `.env`:
- Nunca compartilhe ou comite o arquivo `.env`
- Mantenha suas chaves de API e credenciais seguras
- Use valores diferentes para ambientes de desenvolvimento e produção

### Boas Práticas
- Nunca comite credenciais ou chaves de API no controle de versão
- Use sempre HTTPS em produção
- Mantenha suas dependências atualizadas
- Siga as recomendações de segurança da Azure e MongoDB

## 🤝 Contribuindo

1. Fork o projeto
2. Crie sua branch de feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## ✨ Roadmap

Veja nosso [tasks.md](tasks.md) para o roadmap completo e backlog do projeto.

## 📫 Contato

Link do Projeto: [https://github.com/seu-usuario/ada](https://github.com/seu-usuario/ada)

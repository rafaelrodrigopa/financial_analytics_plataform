# Documentação de Erros e Diagnóstico do GitHub Actions

Este documento compila todos os erros encontrados durante a configuração e execução do pipeline de ingestão diária no **GitHub Actions** (`.github/workflows/daily_ingestion.yml`), detalhando as causas raízes e as soluções aplicadas para homologação em produção.

---

## 1. Histórico de Erros e Diagnósticos

### Erro 1: `google.auth.exceptions.DefaultCredentialsError: File credenciais/chave_conta_servico.json is not a valid json file`
- **Sintoma**: O job falhava na etapa `Execute Daily Ingestion Pipeline` com o erro `JSONDecodeError: Expecting property name enclosed in double quotes: line 2 column 3`.
- **Causa Raíz**: 
  1. O comando bash `echo "${{ secrets.GCP_SA_KEY }}"` ou `cat << EOF` aplicou o recuo de 10 espaços (espaçamento YAML) em cada linha do texto do segredo durante a execução no Linux Runner.
  2. O formulário web de criação de Secrets do GitHub converteu aspas duplas internas ou quebras de linha da chave privada em caracteres codificados.
- **Solução Aplicada**:
  - Implementação de parser nativo em **Python** no passo `Setup GCP Service Account Credentials` para reconstruir o JSON sem recuos YAML.
  - Codificação da chave `chave_conta_servico.json` em **Base64** no repositório (`GCP_SA_KEY`).
  - Adição de fallback inteligente com suporte triplo (`json.loads`, `base64.b64decode` e `ast.literal_eval`).

---

### Erro 2: `Node.js 20 is deprecated... forced to run on Node.js 24`
- **Sintoma**: Aparecia como um aviso em amarelo (*Warning*) nas anotações do GitHub Actions.
- **Causa Raíz**: Notificação global do GitHub Actions referente à migração interna da versão do runtime do Node.js nos runners padrão `ubuntu-latest`.
- **Solução Aplicada**:
  - Confirmação de que a notificação é informativa e não bloqueia a execução do pipeline.
  - Atualização dos *actions* oficiais (`actions/checkout@v4` e `actions/setup-python@v5`).

---

### Erro 3: `Could not resolve host: github.com`
- **Sintoma**: Falha pontual ao executar `git push origin main` via terminal local.
- **Causa Raíz**: Instabilidade temporária de DNS/conectividade de rede durante a comunicação com a API remota do GitHub.
- **Solução Aplicada**:
  - Reexecução do comando `git push origin main` com sucesso.

---

## 2. Estrutura Atualizada do Workflow (`daily_ingestion.yml`)

O workflow `.github/workflows/daily_ingestion.yml` foi configurado com validação defensiva em Python para garantir tolerância a falhas na montagem de credenciais:

```yaml
- name: Setup GCP Service Account Credentials
  env:
    GCP_SA_KEY: ${{ secrets.GCP_SA_KEY }}
  run: |
    mkdir -p credenciais
    python -c "
    import os, base64, json, ast, sys
    raw = os.environ.get('GCP_SA_KEY', '').strip()
    if not raw:
        print('ERRO CRÍTICO: Secret GCP_SA_KEY está VAZIO!', file=sys.stderr)
        sys.exit(1)
    parsed = None
    try:
        parsed = json.loads(raw)
    except Exception:
        try:
            parsed = json.loads(base64.b64decode(raw).decode('utf-8'))
        except Exception:
            try:
                parsed = ast.literal_eval(raw)
            except Exception as err:
                print(f'ERRO AO DECODIFICAR GCP_SA_KEY: {err}', file=sys.stderr)
                sys.exit(1)
    if not isinstance(parsed, dict) or 'type' not in parsed:
        print('ERRO CRÍTICO: Estrutura inválida na chave GCP_SA_KEY!', file=sys.stderr)
        sys.exit(1)
    with open('credenciais/chave_conta_servico.json', 'w') as f:
        json.dump(parsed, f, indent=2)
    print('Credencial GCP salva com sucesso! Projeto:', parsed.get('project_id'))
    "
```

---

## 3. Checklist de Homologação dos Secrets

| Secret | Descrição | Formato Aceito |
| :--- | :--- | :--- |
| `GCP_PROJECT_ID` | ID do Projeto no GCP (`civil-glyph-503402-c9`) | Texto simples |
| `FMP_API_KEY` | Chave de API da Financial Modeling Prep | Texto simples |
| `GCP_SA_KEY` | Conteúdo do arquivo `chave_conta_servico.json` | Texto JSON ou Base64 (Recomendado) |

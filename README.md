# Monitor de preços LG

O `main.py` consulta os preços PIX dos produtos configurados e envia um e-mail
quando algum deles fica abaixo do limite definido em `PRODUCTS`.

## Variáveis de ambiente

- `GMAIL_EMAIL`: conta Gmail usada para enviar a mensagem.
- `GMAIL_APP_PASSWORD`: senha de app de 16 caracteres dessa conta.
- `ALERT_EMAIL`: endereço que receberá o alerta.

Não use a senha normal da conta. No Google, ative a verificação em duas etapas e
crie uma senha de app em **Conta Google > Segurança > Senhas de app**.

## Rodar localmente

```bash
python -m pip install -r requirements.txt
python main.py
```

No Windows PowerShell, antes de executar:

```powershell
$env:GMAIL_EMAIL = "seu-email@gmail.com"
$env:GMAIL_APP_PASSWORD = "sua-senha-de-app"
$env:ALERT_EMAIL = "seu-email-de-alerta@exemplo.com"
python .\main.py
```

O workflow em `.github/workflows/price-monitor.yml` executa automaticamente a
cada 30 minutos e também pode ser iniciado manualmente pelo GitHub.

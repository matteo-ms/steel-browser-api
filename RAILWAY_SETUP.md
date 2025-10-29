# 🚀 Deploy su Railway - Setup Rapido

Repository GitHub: **https://github.com/matteo-ms/steel-browser-api**

---

## Step 1: Collega Repository a Railway

1. Vai su **https://railway.app**
2. Click su **"New Project"**
3. Seleziona **"Deploy from GitHub repo"**
4. Cerca e seleziona **`matteo-ms/steel-browser-api`**
5. Railway rileverà automaticamente il **Dockerfile** ✅

---

## Step 2: Configura Variabile d'Ambiente

Nel dashboard Railway, vai su **"Variables"** e aggiungi:

```
STEEL_URL = https://steel-browser-production-9a2a.up.railway.app
```

---

## Step 3: Deploy e Verifica

1. Railway farà il deploy automaticamente
2. Una volta completato, otterrai un URL pubblico (es. `https://steel-browser-api-production.up.railway.app`)
3. Testa l'API:

```bash
# Health check
curl https://TUO-URL.railway.app/health

# API Info
curl https://TUO-URL.railway.app/

# API Docs (apri nel browser)
open https://TUO-URL.railway.app/docs
```

---

## Step 4: Test Completo

```bash
curl -X POST https://TUO-URL.railway.app/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Bitcoin news",
    "language": "en",
    "search_type": "news",
    "time_filter": "day",
    "num_results": 3
  }'
```

---

## 🔗 Collegamenti Utili

- **Repository**: https://github.com/matteo-ms/steel-browser-api
- **README**: Documentazione completa dell'API
- **DEPLOY.md**: Istruzioni dettagliate deploy
- **n8n-workflow-example.json**: Esempio integrazione n8n

---

## ⚙️ Configurazione n8n

Una volta deployata l'API su Railway:

**HTTP Request Node:**
- Method: `POST`
- URL: `https://TUO-URL.railway.app/search`
- Body Content Type: `JSON`
- Body:
```json
{
  "query": "{{ $json.searchQuery }}",
  "language": "it",
  "region": "it",
  "search_type": "news",
  "time_filter": "3days",
  "num_results": 5
}
```

---

## 📊 Monitoring

Nel dashboard Railway puoi:
- ✅ Visualizzare logs in tempo reale
- ✅ Monitorare CPU/RAM usage
- ✅ Vedere metriche di richieste
- ✅ Scalare verticalmente/orizzontalmente

---

## 💰 Costi Stimati

**Free Tier**: $5/mese credito incluso  
**Uso stimato API**: ~$2-3/mese con uso moderato

---

## 🎯 Status: READY TO DEPLOY! ✅

Tutto configurato e pronto. Segui gli step sopra per completare il deploy.


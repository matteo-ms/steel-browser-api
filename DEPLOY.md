# Deploy su Railway - Istruzioni

## Opzione 1: Deploy da GitHub (Raccomandato)

### Step 1: Push su GitHub

```bash
# Crea un nuovo repository su GitHub (es. steel-browser-api)
# Poi collega e pusha:

cd steel-api
git remote add origin https://github.com/TUO_USERNAME/steel-browser-api.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy su Railway

1. Vai su https://railway.app
2. Click su "New Project"
3. Seleziona "Deploy from GitHub repo"
4. Seleziona il repository `steel-browser-api`
5. Railway rileverà automaticamente il `Dockerfile` e farà il deploy

### Step 3: Configurazione Variabili d'Ambiente

Nel dashboard di Railway:
1. Vai su "Variables"
2. Aggiungi: `STEEL_URL` = `https://steel-browser-production-9a2a.up.railway.app`
3. (Opzionale) `PORT` = `8000` (già impostato nel Dockerfile)

### Step 4: Verifica Deploy

Una volta completato il deploy, Railway ti fornirà un URL pubblico.
Testa l'API:

```bash
# Health check
curl https://your-project.railway.app/health

# Root endpoint
curl https://your-project.railway.app/

# API Docs
open https://your-project.railway.app/docs
```

---

## Opzione 2: Deploy con Railway CLI

### Installazione CLI

```bash
npm install -g @railway/cli
railway login
```

### Deploy

```bash
cd steel-api
railway init
railway up
```

---

## Opzione 3: Deploy Diretto (senza GitHub)

### Step 1: Installa Railway CLI

```bash
npm install -g @railway/cli
railway login
```

### Step 2: Deploy dalla cartella locale

```bash
cd steel-api
railway init
railway up
```

### Step 3: Configura variabili

```bash
railway variables set STEEL_URL=https://steel-browser-production-9a2a.up.railway.app
```

### Step 4: Ottieni URL

```bash
railway domain
```

---

## Test dell'API Deployata

Una volta deployata, testa con curl:

```bash
# Health check
curl https://your-api.railway.app/health

# Test search (esempio veloce)
curl -X POST https://your-api.railway.app/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test query",
    "language": "en",
    "search_type": "web",
    "num_results": 2
  }'
```

---

## Integrazione con n8n

Una volta deployata l'API su Railway, usa l'**HTTP Request Node** in n8n:

### Configurazione Node n8n:

**Method**: `POST`  
**URL**: `https://your-api.railway.app/search`  
**Body Content Type**: `JSON`

**Body (JSON)**:
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

**Headers**:
```
Content-Type: application/json
```

---

## Monitoring e Logs

### Visualizza Logs

```bash
railway logs
```

### Dashboard Railway

Accedi al dashboard per:
- Visualizzare metriche di utilizzo
- Controllare i logs in tempo reale
- Gestire variabili d'ambiente
- Scalare l'applicazione

---

## Troubleshooting

### Problema: Deploy fallisce

**Soluzione**: Controlla i logs con `railway logs` o nel dashboard

### Problema: API non risponde

**Soluzione**: 
1. Verifica che `STEEL_URL` sia configurato correttamente
2. Controlla che il PORT sia 8000 (o quello configurato)
3. Verifica logs per errori

### Problema: Timeout durante scraping

**Soluzione**: 
- Riduci `num_results` (es. da 10 a 5)
- Verifica che Steel Browser sia online: `curl https://steel-browser-production-9a2a.up.railway.app/health`

---

## Costi Railway

- **Free Tier**: $5/mese di credito incluso
- **Starter**: $5/mese + utilizzo
- **Pro**: $20/mese + utilizzo

Questa API dovrebbe rientrare comodamente nel free tier per uso moderato.

---

## Note Finali

✅ API pronta per il deploy  
✅ Dockerfile configurato  
✅ Variabili d'ambiente documentate  
✅ Test locali superati  
✅ Ready per integrazione n8n  

**Prossimi Passi**:
1. Push su GitHub
2. Deploy su Railway
3. Configurare variabile `STEEL_URL`
4. Testare endpoint `/health` e `/search`
5. Integrare in n8n workflows


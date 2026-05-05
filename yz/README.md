# ITSM → RAG → Ollama RCA

Mock ITSM biletleri, **10 bilgi tabanı dokümanı** ile **Chroma RAG** ve **Ollama** LLM kullanılarak **Root Cause Analysis** üretir. Mimari: [ARCHITECTURE.md](ARCHITECTURE.md).

## Önkoşul

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Compose v2)

## Çalıştırma (Docker Compose — önerilen)

Proje klasöründe:

```bash
docker compose up --build
```

- API / Swagger: http://localhost:8000/docs  
- **Web arayüz:** http://localhost:8000/ui/ (veya kök http://localhost:8000/ → `/ui/` yönlendirmesi)  
- `GET /health` — API ayakta  
- `GET /health/ollama` — uygulama konteynerinden Ollama’ya erişim (Compose içinde `http://ollama:11434`)

## Web arayüzü (React)

Üç sütun: **bilet listesi (MCP)**, **sohbet (MCP listesi tetikleyebilir)**, **RCA paneli** (`POST /analyze/ticket/{id}`).

| Geliştirme (iki terminal) | Üretim (Docker imajında UI gömülü) |
|---------------------------|-------------------------------------|
| Terminal 1: `docker compose up` veya `uvicorn app.main:app --port 8000` | `docker compose up --build` — `frontend` imaj aşamasında derlenir |
| Terminal 2: `cd frontend && npm install && npm run dev` → http://localhost:5173 | Tarayıcı: http://localhost:8000/ui/ |

Vite dev sunucusu API’yi `8000` portuna proxy’ler (`/api`, `/analyze`, `/health`). Sadece FastAPI kullanacaksanız: `cd frontend && npm run build` çıktısı `app/static_ui/` altına yazılır; sonra `http://localhost:8000/ui/`.

### İlk kurulum: modeller

Ollama konteyneri ayağa kalktıktan sonra **bir kez** (hosttan):

```bash
docker compose exec ollama ollama pull llama3
docker compose exec ollama ollama pull nomic-embed-text
```

> `mistral` için: `docker compose exec ollama ollama pull mistral` ve `app` servisinde `OLLAMA_MODEL=mistral` (ör. `docker compose run` ile geçici env veya `environment` bloğunda).

Modeller yokken embedding/RCA **503** veya model bulunamadı hatası verebilir; `docker compose logs -f app` ile logları izleyin.

### Arka planda çalıştırma

```bash
docker compose up -d --build
```

Durdurmak: `docker compose down` (volume’lar kalır; tam silmek için `docker compose down -v`).

## API

| Metot | Açıklama |
|--------|-----------|
| `GET /health` | API ayakta |
| `GET /health/ollama` | Ollama erişilebilir mi |
| `GET /tickets` | Mock ITSM bilet listesi |
| `POST /analyze/ticket/{id}` | Bilet ID ile RCA |
| `POST /analyze/text` | Serbest metin ile RCA (`{"text":"..."}`) |
| `POST /admin/reindex` | Bilgi tabanı değişince vektör indeksini yeniden kurar |

Ollama erişilemezse `503`, `detail.error`: `ollama_unreachable` ve Türkçe `hint`.

### RCA API’yi nasıl test ederim?

Uygulama ayaktaysa (`docker compose up` veya `uvicorn …`) üç yol:

1. **Swagger (en kolay)**  
   Tarayıcıda **http://localhost:8000/docs** açın → **`POST /analyze/ticket/{ticket_id}`** → **Try it out** → `ticket_id` = `2` → **Execute**.  
   Aynı sayfadan **`POST /analyze/text`** → Request body örneğini doldurup **Execute**.

2. **PowerShell**

```powershell
Invoke-RestMethod http://localhost:8000/health/ollama
Invoke-RestMethod -Method Post -Uri http://localhost:8000/analyze/ticket/2
$body = '{"text":"Database connection timeout from payment service","title":"DB timeout","priority":"P1"}'
Invoke-RestMethod -Method Post -Uri http://localhost:8000/analyze/text -Body $body -ContentType "application/json; charset=utf-8"
```

3. **Tek script (health + ticket/2 + analyze/text)** — proje kökünden:

```powershell
.\.venv\Scripts\python.exe scripts\test_rca_http.py
# veya farkli port: .\.venv\Scripts\python.exe scripts\test_rca_http.py http://127.0.0.1:8000
```

Docker kullanıyorsanız (hostta venv yoksa), konteyner içinden kendi API’nize:

```powershell
docker compose exec app python scripts/test_rca_http.py http://127.0.0.1:8000
```

Başarılı yanıtta JSON içinde **`rca_markdown`** görmelisiniz. `health/ollama` **down** ise önce Ollama ve modelleri hazırlayın (README Docker bölümü).

## Örnek

```bash
curl http://localhost:8000/tickets
curl -X POST http://localhost:8000/analyze/ticket/2
```

Örnek RCA şablonları: [samples/ornek_rca_ciktilari.md](samples/ornek_rca_ciktilari.md).

## Ortam değişkenleri (`app` servisi)

| Değişken | Compose varsayılanı |
|-----------|---------------------|
| `OLLAMA_BASE_URL` | `http://ollama:11434` |
| `OLLAMA_MODEL` | `llama3` |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` |
| `KNOWLEDGE_DIR` | `knowledge` (host `./knowledge` salt okunur bağlı) |
| `CHROMA_DIR` | `data/chroma` (kalıcı volume `chroma_data`) |
| `RAG_TOP_K` | `4` |

## Kendi MCP sunucumuz (ITSM mock)

Bu repoda **stdio** üzerinden çalışan küçük bir MCP sunucusu vardır; araçlar doğrudan `app/itsm_connector.py` ile aynı mock veriyi kullanır.

| Araç | Açıklama |
|------|-----------|
| `itsm_list_tickets` | Özet bilet listesi |
| `itsm_get_ticket` | `ticket_id` ile tam bilet (yoksa `not_found`) |

### Çalıştırma (proje kökü)

**Önemli:** `python -m mcp_server` komutunu **`yz` proje kök klasöründen** çalıştırın. Örneğin `.venv\Scripts` içindeyken çalıştırırsanız `No module named mcp_server` alırsınız; çünkü Python paketi `yz\mcp_server\` altında, `sys.path` ise çoğunlukla o anki çalışma dizinidir.

```powershell
cd C:\Users\FAHRETTIN.DALGA\Desktop\yz
.\.venv\Scripts\python.exe -m mcp_server
```

Alternatif (her yerden, repo köküne göre): `.\run_mcp.ps1`

```bash
cd /path/to/yz
python -m mcp_server
```

### Test (otomatik)

Proje kökünden MCP istemcisi sunucuyu başlatıp `itsm_list_tickets` çağırır:

```powershell
.\.venv\Scripts\python.exe scripts\test_mcp_list_tickets.py
.\.venv\Scripts\python.exe scripts\test_mcp_get_ticket.py    # varsayilan id=2
.\.venv\Scripts\python.exe scripts\test_mcp_get_ticket.py 3  # baska id
```

### MCP + RCA tek akış (otomatik birlestirme)

Önce MCP ile `itsm_get_ticket`, ardından aynı biletle `POST /analyze/text` (RAG + Ollama) — **tek komut**:

```powershell
.\.venv\Scripts\python.exe scripts\test_mcp_then_rca.py
.\.venv\Scripts\python.exe scripts\test_mcp_then_rca.py --base http://127.0.0.1:8000 --ticket-id 2
```

**Cursor / ajan:** Aynı zinciri elle iki adımda da yapabilirsiniz: (1) MCP aracı `itsm_get_ticket`, (2) eldeki `text`/`title`/`priority` ile `POST /analyze/text` veya tarayıcıda `/docs`.

### Cursor’da tanımlama

**Cursor Settings → MCP → Add new global MCP server** (veya proje MCP JSON’u) içinde örnek:

```json
{
  "mcpServers": {
    "itsm-mock": {
      "command": "C:\\Users\\FAHRETTIN.DALGA\\Desktop\\yz\\.venv\\Scripts\\python.exe",
      "args": ["-m", "mcp_server"],
      "cwd": "C:\\Users\\FAHRETTIN.DALGA\\Desktop\\yz"
    }
  }
}
```

`command` / `cwd` yollarını kendi makinenize göre düzenleyin.

### MCP sonrası: fotoğraftaki diğer adımlar (LLM → çözüm → RAG → ajan RCA)

MCP yalnızca **ITSM verisini** getirir. Ödevdeki sırayı pratikte şöyle ilerletirsiniz:

| Ödev maddesi | Bu repoda ne yapıyorsunuz |
|----------------|----------------------------|
| Offline LLM analizi | **Ollama** çalışır olmalı (`docker compose up`, modeller çekili). |
| Çözüm önerisi + RCA | FastAPI **`POST /analyze/...`** çağrısı; yanıtta **`rca_markdown`** içinde Root Cause / Reason / **Solution** üretilir. |
| 10 bilgi tabanı + RAG | Aynı endpoint içinde **Chroma** + `knowledge/` dokümanları otomatik devreye girer (ilk istekte indeks kurulur). |
| Ajan (bilet başına RCA) | Tek istek = sınıflandırma → RAG → LLM; ekstra ayrı servis yok, pipeline `app/agent.py` içinde. |

**Akış (önerilen):**

1. **Altyapı:** `docker compose up --build`, sonra `docker compose exec ollama ollama pull llama3` ve `nomic-embed-text`. Kontrol: `GET http://localhost:8000/health/ollama` → `up`.
2. **Bilet (MCP):** Cursor veya test scripti ile `itsm_get_ticket` → `text`, `title`, `priority` elinizde.
3. **Analiz (HTTP):** MCP’den gelen metni API’ye verin — **mock id ile aynı kayıt** ise kısayol: `POST /analyze/ticket/2`. Gerçek ITSM’den farklı metin geliyorsa:

```powershell
$body = '{"text":"Database connection timeout from payment service","title":"DB timeout","priority":"P1"}'
Invoke-RestMethod -Method Post -Uri http://localhost:8000/analyze/text -Body $body -ContentType "application/json; charset=utf-8"
```

4. **Sonuç:** Dönen JSON’da `category`, `rag_sources`, **`rca_markdown`** varsa pipeline tamamlanmıştır. Örnek metinler: `samples/ornek_rca_ciktilari.md`.

**İnsan / ajan sırası özeti:** `itsm_get_ticket` → **`POST /analyze/text`** (veya script: `test_mcp_then_rca.py`). Mock id ile doğrudan RCA için kısayol: **`POST /analyze/ticket/{id}`** (MCP atlanır).

### Üretim (ServiceNow / Jira)

`mcp_server/itsm.py` içindeki araç gövdelerini gerçek API çağrılarıyla değiştirmeniz yeterli; MCP sözleşmesi (isim + parametre) aynı kalır.

## Yerel geliştirme (isteğe bağlı, venv)

Docker kullanmak istemezseniz: `python -m venv .venv`, `pip install -r requirements.txt` (MCP için `mcp` paketi dahildir), `uvicorn app.main:app --reload --port 8000` ve ayrıca makinede **Ollama** (`OLLAMA_BASE_URL=http://localhost:11434`).

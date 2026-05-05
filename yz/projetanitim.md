PROJE TANITIMI — ITSM, MCP, RAG ve Offline LLM ile RCA
================================================================

1. Projenin amacı
-----------------
Mock ITSM bilet verisini (REST ve/veya MCP araçları) alıp, on bilgi tabanı dokümanı üzerinden RAG (Chroma + embedding) ile zenginleştirerek, yerel (offline) büyük dil modeli ile her bilet için Root Cause Analysis (RCA: kök neden, gerekçe, çözüm) üretmek.

Ana bileşenler: FastAPI (RCA API), Ollama (LLM + embedding), Chroma (RAG), stdio MCP sunucusu (bilet araçları), **React + Vite web arayüzü** (tarayıcıdan MCP listesi / sohbet ve RCA).


2. Offline LLM olarak ne kullandım, nerede?
---------------------------------------------
**Ollama** kullanılıyor — veri dışarı çıkmadan, konteyner veya yerel süreç üzerinden çalışan açık kaynak “offline” LLM sunucusu.

• **Metin üretimi (RCA):** `app/agent.py` içindeki `ollama_generate()` fonksiyonu, Ollama’nın HTTP API’sine `POST .../api/generate` ile istek atar. Gönderilen tek “prompt”, `build_rca_prompt()` ile oluşturulur (bilet + RAG bağlamı + Root Cause / Reason / Solution formatı).

• **Embedding (RAG için):** `app/rag_store.py` içinde `langchain_ollama.OllamaEmbeddings` kullanılır. Bilgi tabanı parçaları ve sorgu metni Ollama üzerinden vektöre çevrilir; vektörler **Chroma**’da saklanır ve `similarity_search` ile geri çağrılır.

Özet: **Üretim = `OLLAMA_MODEL` (varsayılan `llama3`)**, **embedding = `OLLAMA_EMBED_MODEL` (varsayılan `nomic-embed-text`)**. Her ikisi de `app/config.py` ortam değişkenleriyle yönetilir.


3. Docker Compose ile ne yaptım, hangi konteynerler?
----------------------------------------------------
Dosya: `docker-compose.yml`

**a) `ollama` servisi**
• Görüntü: `ollama/ollama:latest`
• Port: `11434:11434` (hosttan da erişilebilir)
• Kalıcılık: `ollama_data` volume → model ve Ollama verisi diske yazılır
• **Healthcheck:** `ollama list` ile süreç ayakta mı kontrol edilir; `app` bu servis **healthy** olmadan kalkmaz (`depends_on: condition: service_healthy`)

**b) `app` servisi**
• `build: .` → proje kökündeki **`Dockerfile`** ile imaj üretilir
• Port: `8000:8000` → FastAPI (Swagger `/docs`, arayüz `/ui/`)
• **Ortam değişkenleri (Compose içi ağ):**
  - `OLLAMA_BASE_URL=http://ollama:11434` → uygulama konteyneri, Ollama’ya servis adıyla ulaşır
  - `OLLAMA_MODEL=llama3` → RCA üretim modeli
  - `OLLAMA_EMBED_MODEL=nomic-embed-text` → RAG embedding modeli
• **Volume’lar:**
  - `./knowledge:/app/knowledge:ro` → 10 bilgi dosyası hosttan salt okunur bağlanır
  - `chroma_data:/app/data/chroma` → vektör indeksi kalıcı volume’da kalır

**İlk kurulumda (bir kez) hosttan çalıştırılması gerekenler:** Ollama konteynerinde modellerin çekilmesi:
  `docker compose exec ollama ollama pull llama3`
  `docker compose exec ollama ollama pull nomic-embed-text`


4. Dockerfile’da ne var?
-------------------------
Çok aşamalı (`multi-stage`) yapı:

1. **Node aşaması (`uibuild`):** `frontend/` için `npm install` + `npm run build` → çıktı `app/static_ui/` altına (Vite `outDir` ayarı ile) yazılır; böylece tek imajda web arayüzü de gömülür.

2. **Python aşaması:** `python:3.12-slim`, `requirements.txt` ile bağımlılıklar, ardından `app/`, `mcp_server/`, `knowledge/`, `scripts/` ve önceki aşamadan **`app/static_ui`** kopyalanır.

Çalıştırma: `uvicorn app.main:app --host 0.0.0.0 --port 8000`


5. Veri ve RAG akışı (kısa)
----------------------------
• Biletler: `app/itsm_connector.py` (mock liste); aynı kaynak MCP araçları (`itsm_list_tickets`, `itsm_get_ticket`) ile `mcp_server/` üzerinden de sunulur.

• Bilgi tabanı: `knowledge/*.md` (10 doküman).

• İlk analiz veya boş koleksiyonda: `app/rag_store.py` dokümanları böler, Ollama embedding ile Chroma’ya yazar; sonraki isteklerde koleksiyon varsa diskten yüklenir. Yeniden kurulum: `POST /admin/reindex`.

• RCA: `app/agent.py` → sınıflandırma (kural tabanlı) → RAG parçaları → `build_rca_prompt` → Ollama `generate` → `rca_markdown` döner.


6. API, web arayüzü (frontend) ve tarayıcıdan RCA
-------------------------------------------------
**REST API:** `/tickets`, `/analyze/ticket/{id}`, `/analyze/text`, `/health`, `/health/ollama`, `/api/mcp/...`, `/api/chat` vb. (Swagger: `/docs`).

**Web arayüzü (`frontend/`, derleme çıktısı `app/static_ui/`):** React + Vite. Docker imajında `Dockerfile` içindeki Node aşamasıyla üretilir ve Python imajına kopyalanır. Adres: **`http://localhost:8000/ui/`** (kök `http://localhost:8000/` → `/ui/` yönlendirmesi).

Arayüz üç bölümdür:
• **Biletler:** “MCP ile listele” → `GET /api/mcp/tickets` (MCP `itsm_list_tickets`). Satıra tıklayınca → `GET /api/mcp/tickets/{id}` (`itsm_get_ticket`).
• **Sohbet:** `POST /api/chat` ile doğal dil; liste veya tekil bilet niyeti MCP üzerinden işlenir, seçili bilet sağ panele aktarılabilir.
• **RCA (root cause):** Seçili bilet için **“RCA üret”** → `POST /analyze/ticket/{id}`; dönen **`rca_markdown`** (Root Cause / Reason / Solution) sağ panelde gösterilir. **Kök neden analizi böylece yalnızca Postman/Swagger değil, doğrudan web arayüzünden de** tetiklenir; arka uçta yine RAG + Ollama aynı pipeline’dır.

**Yerel geliştirme:** `cd frontend && npm run dev` → `http://localhost:5173` (Vite proxy: `/api`, `/analyze`, `/health` → port 8000).


7. Özet cümle (sunum için)
--------------------------
Bu projede **offline LLM olarak Ollama** kullanıldı; **Docker Compose** ile **iki konteyner** (Ollama + FastAPI) ayağa kaldırıldı; **`llama3`** üretim ve **`nomic-embed-text`** embedding modelleri Compose ortamında tanımlandı; modeller **`ollama pull`** ile indirilir. **RAG** `app/rag_store.py` + Chroma’da, **RCA üretimi** `app/agent.py` + Ollama `/api/generate` ile yapılır; ayrıca **React arayüzünden** (`/ui/`) MCP ile bilet seçilip **root cause analizi** aynı API üzerinden çalıştırılabilir.

Örnek proje fotoğraflarını projefotoğrafları kısmından bulabilirsiniz.

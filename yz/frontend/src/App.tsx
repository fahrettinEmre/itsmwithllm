import { useCallback, useEffect, useState } from "react";

type TicketRow = {
  id: number;
  title: string | null;
  priority: string | null;
  preview?: string;
};

type TicketFull = {
  id: number;
  title: string | null;
  priority: string | null;
  text: string;
};

type ChatMsg = { role: "user" | "assistant"; text: string };

async function j<T>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(url, init);
  if (!r.ok) {
    const t = await r.text();
    throw new Error(`${r.status}: ${t.slice(0, 400)}`);
  }
  return r.json() as Promise<T>;
}

export default function App() {
  const [ollama, setOllama] = useState<string>("…");
  const [tickets, setTickets] = useState<TicketRow[]>([]);
  const [selected, setSelected] = useState<TicketFull | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [chat, setChat] = useState<ChatMsg[]>([
    {
      role: "assistant",
      text: "Merhaba. **Biletleri listele** veya **2 numaralı ticketı getir** / **#2** yazabilirsiniz; soldaki **MCP ile listele** de tüm listeyi MCP üzerinden getirir.",
    },
  ]);
  const [input, setInput] = useState("");
  const [rca, setRca] = useState<Record<string, unknown> | null>(null);

  const refreshHealth = useCallback(async () => {
    try {
      const h = await j<{ ollama?: string }>("/health/ollama");
      setOllama(h.ollama === "up" ? "Ollama: ayakta" : "Ollama: kapalı / erişilemiyor");
    } catch {
      setOllama("API’ye ulaşılamıyor");
    }
  }, []);

  useEffect(() => {
    void refreshHealth();
  }, [refreshHealth]);

  const loadTicketsMcp = async () => {
    setErr(null);
    setBusy(true);
    try {
      const data = await j<{ tickets: TicketRow[] }>("/api/mcp/tickets");
      setTickets(data.tickets);
      setChat((c) => [
        ...c,
        {
          role: "assistant",
          text: `MCP **itsm_list_tickets** sonucu: ${data.tickets.length} kayıt (mock ITSM).`,
        },
      ]);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const openTicketMcp = async (id: number) => {
    setErr(null);
    setBusy(true);
    try {
      const data = await j<{ ticket: TicketFull }>(`/api/mcp/tickets/${id}`);
      setSelected(data.ticket);
      setChat((c) => [
        ...c,
        {
          role: "assistant",
          text: `MCP **itsm_get_ticket(${id})** açıldı: **${data.ticket.title ?? "—"}** — sağda RCA çalıştırabilirsiniz.`,
        },
      ]);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const sendChat = async () => {
    const t = input.trim();
    if (!t) return;
    setInput("");
    setChat((c) => [...c, { role: "user", text: t }]);
    setErr(null);
    setBusy(true);
    try {
      const res = await j<{
        intent: string;
        reply: string;
        tickets: TicketRow[] | null;
        ticket: TicketFull | null;
      }>("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: t }),
      });
      setChat((c) => [...c, { role: "assistant", text: res.reply }]);
      if (res.tickets?.length) setTickets(res.tickets);
      if (res.ticket) setSelected(res.ticket);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const runRca = async () => {
    if (!selected) return;
    setErr(null);
    setBusy(true);
    setRca(null);
    try {
      const body = await j<Record<string, unknown>>(`/analyze/ticket/${selected.id}`, { method: "POST" });
      setRca(body);
      setChat((c) => [
        ...c,
        {
          role: "assistant",
          text: `RCA tamamlandı (bilet #${selected.id}). Özet sağ panelde.`,
        },
      ]);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      <header
        style={{
          padding: "1rem 1.5rem",
          borderBottom: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "1rem",
        }}
      >
        <h1 style={{ margin: 0, fontSize: "1.15rem", fontWeight: 600 }}>ITSM — MCP + RCA</h1>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <span style={{ color: "var(--muted)", fontSize: "0.9rem" }}>{ollama}</span>
          <button type="button" onClick={() => void refreshHealth()} style={{ background: "#374151" }}>
            Sağlık yenile
          </button>
        </div>
      </header>

      {err && (
        <div
          style={{
            margin: "0 1rem",
            padding: "0.75rem 1rem",
            background: "#3f1d1d",
            border: "1px solid #7f1d1d",
            borderRadius: 8,
            color: "#fecaca",
          }}
        >
          {err}
        </div>
      )}

      <main
        className="layout-grid"
        style={{
          flex: 1,
          padding: "1rem",
          maxWidth: 1400,
          margin: "0 auto",
          width: "100%",
        }}
      >
        <section
          style={{
            background: "var(--panel)",
            border: "1px solid var(--border)",
            borderRadius: 12,
            padding: "1rem",
            display: "flex",
            flexDirection: "column",
            gap: "0.75rem",
          }}
        >
          <h2 style={{ margin: 0, fontSize: "1rem" }}>Biletler</h2>
          <button type="button" disabled={busy} onClick={() => void loadTicketsMcp()}>
            MCP ile listele
          </button>
          <ul style={{ listStyle: "none", margin: 0, padding: 0, overflow: "auto", flex: 1 }}>
            {tickets.map((t) => (
              <li key={t.id} style={{ marginBottom: "0.35rem" }}>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void openTicketMcp(t.id)}
                  style={{
                    width: "100%",
                    textAlign: "left",
                    background: selected?.id === t.id ? "var(--accent-dim)" : "#243044",
                    fontSize: "0.85rem",
                  }}
                >
                  <strong>#{t.id}</strong> {t.title ?? "—"}{" "}
                  <span style={{ color: "var(--muted)" }}>{t.priority}</span>
                </button>
              </li>
            ))}
          </ul>
        </section>

        <section
          style={{
            background: "var(--panel)",
            border: "1px solid var(--border)",
            borderRadius: 12,
            padding: "1rem",
            display: "flex",
            flexDirection: "column",
            minHeight: 420,
          }}
        >
          <h2 style={{ margin: "0 0 0.75rem", fontSize: "1rem" }}>Sohbet (MCP listesi)</h2>
          <div
            style={{
              flex: 1,
              overflow: "auto",
              border: "1px solid var(--border)",
              borderRadius: 8,
              padding: "0.75rem",
              marginBottom: "0.75rem",
              background: "#0d1218",
            }}
          >
            {chat.map((m, i) => (
              <div
                key={i}
                style={{
                  marginBottom: "0.65rem",
                  color: m.role === "user" ? "#93c5fd" : "var(--text)",
                }}
              >
                <strong>{m.role === "user" ? "Siz" : "Asistan"}:</strong> {m.text}
              </div>
            ))}
          </div>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <input
              style={{ flex: 1 }}
              placeholder='Örn: "biletleri listele"'
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && void sendChat()}
            />
            <button type="button" disabled={busy} onClick={() => void sendChat()}>
              Gönder
            </button>
          </div>
        </section>

        <section
          style={{
            background: "var(--panel)",
            border: "1px solid var(--border)",
            borderRadius: 12,
            padding: "1rem",
            display: "flex",
            flexDirection: "column",
            gap: "0.75rem",
            minHeight: 420,
          }}
        >
          <h2 style={{ margin: 0, fontSize: "1rem" }}>RCA (RAG + Ollama)</h2>
          {!selected ? (
            <p style={{ color: "var(--muted)", margin: 0 }}>Soldan bir bilet seçin veya MCP ile açın.</p>
          ) : (
            <>
              <div style={{ fontSize: "0.9rem" }}>
                <div>
                  <strong>#{selected.id}</strong> {selected.title}
                </div>
                <div style={{ color: "var(--muted)", marginTop: "0.25rem" }}>{selected.priority}</div>
                <pre
                  style={{
                    margin: "0.5rem 0 0",
                    whiteSpace: "pre-wrap",
                    fontSize: "0.8rem",
                    color: "var(--muted)",
                    maxHeight: 120,
                    overflow: "auto",
                  }}
                >
                  {selected.text}
                </pre>
              </div>
              <button type="button" disabled={busy} onClick={() => void runRca()}>
                RCA üret (POST /analyze/ticket/{selected.id})
              </button>
            </>
          )}
          {rca && (
            <div style={{ flex: 1, overflow: "auto", marginTop: "0.5rem" }}>
              <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
                Kategori: <strong style={{ color: "var(--text)" }}>{String(rca.category ?? "—")}</strong>
              </div>
              <div style={{ fontSize: "0.8rem", color: "var(--muted)", marginTop: "0.35rem" }}>
                RAG: {(rca.rag_sources as string[])?.join(", ") ?? "—"}
              </div>
              <pre
                style={{
                  marginTop: "0.75rem",
                  padding: "0.75rem",
                  background: "#0d1218",
                  borderRadius: 8,
                  fontSize: "0.82rem",
                  whiteSpace: "pre-wrap",
                  border: "1px solid var(--border)",
                }}
              >
                {String(rca.rca_markdown ?? "")}
              </pre>
            </div>
          )}
        </section>
      </main>

      <footer style={{ padding: "0.75rem 1rem", color: "var(--muted)", fontSize: "0.8rem", borderTop: "1px solid var(--border)" }}>
        Geliştirme: <code>npm run dev</code> (5173) + API <code>uvicorn</code> veya Docker :8000. Üretim: <code>npm run build</code> sonra{" "}
        <a href="/ui/" style={{ color: "var(--accent)" }}>
          /ui/
        </a>
      </footer>
    </div>
  );
}

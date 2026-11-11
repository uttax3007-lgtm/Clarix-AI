"use client";
import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Play, Pause, Send } from "lucide-react";
import { api, apiBlob, LANGUAGES } from "@/lib/api";
import { useAuth } from "@/contexts/auth";

type Item = Record<string, string | number>;
type Sum = { document_title: string; document_type: string; explanation: string; key_points: string[]; important_dates: Item[];
  eligibility: Item[]; required_documents: string[]; action_items: Item[]; warnings: string[] };
type Msg = { role: string; content: string; sources?: { page: number; excerpt: string }[] };

export default function DocPage() {
  const { id } = useParams<{ id: string }>(); const { user } = useAuth();
  const [lang, setLang] = useState("en"); const [level, setLevel] = useState(2);
  const [s, setS] = useState<Sum | null>(null); const [err, setErr] = useState(""); const [msgs, setMsgs] = useState<Msg[]>([]);
  const [q, setQ] = useState(""); const [sending, setSending] = useState(false); const [playing, setPlaying] = useState(false);
  const audio = useRef<HTMLAudioElement | null>(null);
  useEffect(() => { if (!user) return; setS(null); setErr("");
    api<Sum>(`/documents/${id}/summary?level=${level}&language=${lang}`).then(setS).catch((e) => setErr(e.message)); }, [user, id, lang, level]);
  useEffect(() => { if (user) api<{ messages: Msg[] }>(`/documents/${id}/chat`).then((r) => setMsgs(r.messages)).catch(() => {}); }, [user, id]);

  async function ask() {
    if (q.trim().length < 2) return; const question = q; setQ(""); setSending(true);
    setMsgs((m) => [...m, { role: "user", content: question }]);
    try { const r = await api<{ answer: string; sources: Msg["sources"] }>(`/documents/${id}/chat`, { method: "POST", body: JSON.stringify({ question, language: lang }) });
      setMsgs((m) => [...m, { role: "assistant", content: r.answer, sources: r.sources }]); }
    catch (e) { setMsgs((m) => [...m, { role: "assistant", content: (e as Error).message }]); } finally { setSending(false); }
  }
  async function listen() {
    if (audio.current && !audio.current.paused) { audio.current.pause(); return setPlaying(false); }
    if (audio.current?.src && audio.current.currentTime > 0 && !audio.current.ended) { audio.current.play(); return setPlaying(true); }
    if (!s || !["en", "hi", "mr"].includes(lang)) return setErr("Audio supports English, Hindi and Marathi.");
    const blob = await apiBlob("/voice/synthesize", { text: s.explanation.slice(0, 4000), language: lang });
    audio.current = new Audio(URL.createObjectURL(blob)); audio.current.onended = () => setPlaying(false); audio.current.play(); setPlaying(true);
  }
  const Sec = ({ t, children }: { t: string; children: React.ReactNode }) => <section className="mt-8"><h2 className="font-head font-semibold">{t}</h2><div className="mt-2 text-sm text-ink2">{children}</div></section>;
  return (<main className="mx-auto max-w-3xl px-6 py-10">
    <Link href="/documents" className="text-sm text-muted">← Documents</Link>
    {err && <p role="alert" className="mt-4 text-sm text-err">{err}</p>}
    <div className="mt-4 flex flex-wrap items-center gap-3">
      <select value={lang} onChange={(e) => setLang(e.target.value)} className="rounded-lg border border-line bg-surface px-3 py-2 text-sm">{LANGUAGES.map(([c, , n]) => <option key={c} value={c}>{n}</option>)}</select>
      <select value={level} onChange={(e) => setLevel(+e.target.value)} className="rounded-lg border border-line bg-surface px-3 py-2 text-sm"><option value={1}>Very simple</option><option value={2}>Everyday</option><option value={3}>Detailed</option></select>
      <button onClick={listen} className="flex items-center gap-2 rounded-lg bg-coral px-4 py-2 text-sm font-medium text-surface hover:bg-coralHover">{playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}Listen to explanation</button></div>
    {!s && !err && <p className="mt-8 text-muted">Preparing explanation…</p>}
    {s && <>
      <h1 className="mt-6 font-head text-2xl font-bold">{s.document_title}</h1><p className="text-sm text-muted">{s.document_type}</p>
      <p className="mt-4 whitespace-pre-wrap leading-relaxed">{s.explanation}</p>
      <Sec t="Important dates">{s.important_dates.length ? s.important_dates.map((d, i) => <p key={i}>{d.label}: <b>{d.date}</b> <span className="text-muted">(page {d.page})</span></p>) : "Not specified in the document."}</Sec>
      <Sec t="Eligibility stated in the document">{s.eligibility.length ? s.eligibility.map((e, i) => <p key={i}>• {e.condition} <span className="text-muted">(page {e.page})</span></p>) : "Not specified in the document."}<p className="mt-2 text-xs text-muted">Whether you are eligible cannot be decided from the document alone.</p></Sec>
      <Sec t="Checklist">{s.action_items.length ? <ol className="list-decimal pl-5">{s.action_items.map((a, i) => <li key={i}>{a.step} <span className="text-muted">(page {a.page})</span></li>)}</ol> : "Not specified in the document."}</Sec>
      {s.warnings.length > 0 && <Sec t="Warnings">{s.warnings.map((w, i) => <p key={i} className="text-warn">• {w}</p>)}</Sec>}
      <p className="mt-6 text-xs text-muted">AI-generated. Verify dates and amounts against the original document.</p></>}
    <Sec t="Ask about this document"><div className="space-y-3">{msgs.map((m, i) => <div key={i} className={m.role === "user" ? "text-right" : ""}>
      <p className={`inline-block max-w-[90%] rounded-lg px-3 py-2 text-left ${m.role === "user" ? "bg-ink text-surface" : "border border-line bg-surface"}`}>{m.content}</p>
      {m.sources?.map((x, j) => <p key={j} className="mt-1 text-xs text-muted">Page {x.page}: “{x.excerpt}…”</p>)}</div>)}</div>
      <div className="mt-4 flex gap-2"><input value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && ask()} placeholder="What is the last date to apply?" className="flex-1 rounded-lg border border-line bg-surface px-3 py-2" />
        <button aria-label="Send" disabled={sending} onClick={ask} className="rounded-lg bg-coral px-3 text-surface disabled:opacity-60"><Send className="h-4 w-4" /></button></div></Sec>
  </main>);
}

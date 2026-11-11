"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { UploadCloud, Trash2, Loader2 } from "lucide-react";
import { signOut } from "firebase/auth";
import { auth } from "@/lib/firebase";
import { api, Doc } from "@/lib/api";
import { useAuth } from "@/contexts/auth";

const OK = ["pdf", "docx", "png", "jpg", "jpeg"], MAX_MB = 15;
const LABEL: Record<string, string> = { queued: "Queued", extracting: "Reading document", indexing: "Indexing", summarizing: "Understanding", ready: "Ready", failed: "Failed" };

export default function Documents() {
  const { user, loading } = useAuth(); const router = useRouter();
  const [docs, setDocs] = useState<Doc[]>([]); const [q, setQ] = useState(""); const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => { if (!loading && !user) router.replace("/login"); }, [user, loading, router]);
  const load = useCallback(() => api<{ items: Doc[] }>(`/documents?q=${encodeURIComponent(q)}`).then((r) => setDocs(r.items)).catch((e) => setErr(e.message)), [q]);
  useEffect(() => { if (user) load(); }, [user, load]);
  useEffect(() => { // poll while anything is processing
    if (!docs.some((d) => !["ready", "failed"].includes(d.status))) return;
    const t = setInterval(load, 2500); return () => clearInterval(t);
  }, [docs, load]);

  async function upload(f?: File) {
    if (!f) return; setErr("");
    const ext = f.name.split(".").pop()?.toLowerCase() ?? "";
    if (!OK.includes(ext)) return setErr("Unsupported file. Use PDF, DOCX, PNG, JPG or JPEG.");
    if (f.size > MAX_MB * 1048576) return setErr(`File exceeds ${MAX_MB} MB.`);
    setBusy(true);
    try { const fd = new FormData(); fd.append("file", f); await api("/documents/upload", { method: "POST", body: fd }); await load(); }
    catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  }
  if (!user) return null;
  return (<main className="mx-auto max-w-4xl px-6 py-10">
    <div className="flex items-center justify-between"><h1 className="font-head text-2xl font-bold">Your documents</h1>
      <button onClick={() => signOut(auth)} className="text-sm text-muted">Sign out</button></div>
    <motion.div onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); upload(e.dataTransfer.files[0]); }}
      whileHover={{ scale: 1.005 }} className="mt-6 rounded-xl border border-dashed border-line bg-surface p-10 text-center">
      {busy ? <Loader2 className="mx-auto h-6 w-6 animate-spin text-coral" /> : <UploadCloud className="mx-auto h-6 w-6 text-coral" />}
      <p className="mt-3 font-medium">Drop a document here, or <button className="text-coral underline" onClick={() => input.current?.click()}>choose a file</button></p>
      <p className="mt-1 text-sm text-muted">PDF, DOCX, PNG, JPG · up to {MAX_MB} MB</p>
      <input ref={input} type="file" hidden accept=".pdf,.docx,.png,.jpg,.jpeg" onChange={(e) => upload(e.target.files?.[0])} />
    </motion.div>
    {err && <p role="alert" className="mt-3 text-sm text-err">{err}</p>}
    <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search documents" className="mt-8 w-full rounded-lg border border-line bg-surface px-3 py-2" />
    <ul className="mt-4 divide-y divide-line">{docs.length === 0 && <li className="py-8 text-center text-muted">No documents yet.</li>}
      {docs.map((d) => <li key={d.id} className="flex items-center justify-between py-3">
        <div><Link href={`/documents/${d.id}`} className="font-medium hover:text-coral">{d.title}</Link>
          <p className="text-xs text-muted">{d.file_type.toUpperCase()} · {new Date(d.created_at).toLocaleDateString()} · <span className={d.status === "failed" ? "text-err" : d.status === "ready" ? "text-ok" : "text-warn"}>{LABEL[d.status] ?? d.status}</span>{d.error && ` — ${d.error}`}</p></div>
        <button aria-label="Delete" onClick={async () => { await api(`/documents/${d.id}`, { method: "DELETE" }); load(); }}><Trash2 className="h-4 w-4 text-muted hover:text-err" /></button></li>)}
    </ul></main>);
}

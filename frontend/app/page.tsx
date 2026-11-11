"use client";
import Link from "next/link";
import { motion } from "framer-motion";
import { FileText, Languages, MessageSquareText, Volume2, CalendarClock, Sparkles } from "lucide-react";
import { LANGUAGES } from "@/lib/api";

const features = [
  [FileText, "Understand documents", "Notices, schemes, bank and legal papers, read page by page."],
  [Sparkles, "Simplify", "Three explanation levels, from very simple to detailed."],
  [Languages, "Translate", "Indian languages with official terms preserved and explained."],
  [MessageSquareText, "Ask questions", "Answers grounded in your document, with page references."],
  [Volume2, "Listen", "Hear the explanation in Hindi, Marathi or English."],
  [CalendarClock, "Track deadlines", "Dates are shown with the page they were found on."],
] as const;

export default function Landing() {
  return (<main>
    <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
      <span className="font-head text-xl font-bold tracking-tight">CLARIX <span className="text-coral">AI</span></span>
      <nav className="flex items-center gap-6 text-sm text-ink2">
        <a href="#features">Features</a><a href="#languages">Languages</a><a href="#privacy">Privacy</a>
        <Link href="/login" className="rounded-lg bg-ink px-4 py-2 text-surface">Sign in</Link></nav>
    </header>
    <section className="mx-auto max-w-4xl px-6 pb-20 pt-16 text-center">
      <motion.h1 initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .5 }}
        className="font-head text-4xl font-extrabold leading-tight tracking-tight sm:text-6xl">
        Understand Anything. <span className="text-coral">In Your Language.</span></motion.h1>
      <p className="mx-auto mt-6 max-w-2xl text-lg text-muted">Upload a government notice, scholarship circular or bank letter. CLARIX reads it, explains it simply and answers your questions in your language.</p>
      <div className="mt-8 flex justify-center gap-3">
        <Link href="/register" className="rounded-lg bg-coral px-6 py-3 font-medium text-surface transition hover:bg-coralHover">Get Started</Link>
        <a href="#features" className="rounded-lg border border-line bg-surface px-6 py-3 font-medium">Explore Features</a></div>
    </section>
    <section id="features" className="border-y border-line bg-bg2 py-16"><div className="mx-auto grid max-w-6xl gap-x-10 gap-y-8 px-6 sm:grid-cols-2 lg:grid-cols-3">
      {features.map(([Icon, t, d]) => <div key={t}><Icon className="mb-3 h-5 w-5 text-coral" /><h3 className="font-head font-semibold">{t}</h3><p className="mt-1 text-sm text-muted">{d}</p></div>)}
    </div></section>
    <section className="mx-auto max-w-4xl px-6 py-16"><h2 className="font-head text-2xl font-bold">How it works</h2>
      <ol className="mt-6 space-y-3 text-ink2">{["Upload a document", "CLARIX reads and understands it", "Choose your language", "Receive a simplified explanation"].map((s, i) =>
        <li key={s} className="flex gap-4 border-b border-line pb-3"><span className="font-head font-bold text-coral">0{i + 1}</span>{s}</li>)}</ol></section>
    <section id="languages" className="bg-bg2 py-16"><div className="mx-auto max-w-6xl px-6"><h2 className="font-head text-2xl font-bold">Supported languages</h2>
      <div className="mt-6 flex flex-wrap gap-3">{LANGUAGES.map(([c, n, native]) => <span key={c} className="rounded-lg border border-line bg-surface px-4 py-2 text-sm">{native} <span className="text-muted">· {n}</span></span>)}</div>
      <p className="mt-4 text-sm text-muted">Voice playback currently supports English, Hindi and Marathi.</p></div></section>
    <section id="privacy" className="mx-auto max-w-4xl px-6 py-16"><h2 className="font-head text-2xl font-bold">Privacy</h2>
      <p className="mt-3 text-ink2">Documents are private to your account. To analyse them, extracted text is sent to a third-party AI provider (OpenRouter and the model it routes to). You can delete a document at any time.</p></section>
    <footer className="border-t border-line py-8 text-center text-sm text-muted">© CLARIX AI · contact@example.com (placeholder)</footer>
  </main>);
}

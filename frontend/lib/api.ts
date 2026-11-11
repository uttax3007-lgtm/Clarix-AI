import { auth } from "./firebase";
const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await auth.currentUser?.getIdToken();
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    const e = await res.json().catch(() => null);
    throw new Error(e?.error?.message ?? `Request failed (${res.status})`);
  }
  return res.status === 204 ? (undefined as T) : res.json();
}
export async function apiBlob(path: string, body: unknown): Promise<Blob> {
  const token = await auth.currentUser?.getIdToken();
  const res = await fetch(`${BASE}${path}`, { method: "POST", body: JSON.stringify(body),
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` } });
  if (!res.ok) throw new Error("Audio generation failed");
  return res.blob();
}
export type Doc = { id: string; title: string; file_type: string; status: string; error?: string; language?: string; created_at: string };
export const LANGUAGES = [
  ["en", "English", "English"], ["hi", "Hindi", "हिन्दी"], ["mr", "Marathi", "मराठी"], ["gu", "Gujarati", "ગુજરાતી"],
  ["bn", "Bengali", "বাংলা"], ["ta", "Tamil", "தமிழ்"], ["te", "Telugu", "తెలుగు"], ["kn", "Kannada", "ಕನ್ನಡ"],
  ["ml", "Malayalam", "മലയാളം"], ["pa", "Punjabi", "ਪੰਜਾਬੀ"]] as const;

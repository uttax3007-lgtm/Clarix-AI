"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { createUserWithEmailAndPassword, signInWithEmailAndPassword, signInWithPopup, GoogleAuthProvider } from "firebase/auth";
import { auth } from "@/lib/firebase";

const schema = z.object({ email: z.string().email("Enter a valid email"), password: z.string().min(8, "At least 8 characters") });
type F = z.infer<typeof schema>;

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter(); const [err, setErr] = useState("");
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<F>({ resolver: zodResolver(schema) });
  const go = async (fn: () => Promise<unknown>) => { setErr(""); try { await fn(); router.push("/documents"); } catch (e) { setErr((e as Error).message.replace("Firebase: ", "")); } };
  const input = "w-full rounded-lg border border-line bg-surface px-3 py-2.5 outline-none focus:border-coral";
  return (<main className="grid min-h-screen place-items-center px-6"><div className="w-full max-w-sm">
    <h1 className="font-head text-2xl font-bold">{mode === "login" ? "Welcome back" : "Create your account"}</h1>
    <form className="mt-6 space-y-4" onSubmit={handleSubmit((v) => go(() => (mode === "login" ? signInWithEmailAndPassword : createUserWithEmailAndPassword)(auth, v.email, v.password)))}>
      <div><input className={input} placeholder="Email" {...register("email")} />{errors.email && <p className="mt-1 text-sm text-err">{errors.email.message}</p>}</div>
      <div><input className={input} type="password" placeholder="Password" {...register("password")} />{errors.password && <p className="mt-1 text-sm text-err">{errors.password.message}</p>}</div>
      {err && <p role="alert" className="text-sm text-err">{err}</p>}
      <button disabled={isSubmitting} className="w-full rounded-lg bg-coral py-2.5 font-medium text-surface hover:bg-coralHover disabled:opacity-60">{mode === "login" ? "Sign in" : "Register"}</button>
    </form>
    <button onClick={() => go(() => signInWithPopup(auth, new GoogleAuthProvider()))} className="mt-3 w-full rounded-lg border border-line bg-surface py-2.5">Continue with Google</button>
    <a className="mt-6 block text-center text-sm text-muted" href={mode === "login" ? "/register" : "/login"}>{mode === "login" ? "New here? Create an account" : "Have an account? Sign in"}</a>
  </div></main>);
}
export default function Login() { return <AuthForm mode="login" />; }

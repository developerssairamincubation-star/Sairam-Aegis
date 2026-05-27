"use client";

import { Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { getStoredUserId, setStoredUserId } from "@/lib/localAuth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const existingUserId = getStoredUserId();
    if (existingUserId) router.replace("/chat");
  }, [router]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setMessage("");

    const endpoint = mode === "login" ? "/auth/login" : "/auth/signup";
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    setSubmitting(false);

    if (!response.ok) {
      const detail = await response.text();
      setMessage(detail || "Authentication failed.");
      return;
    }

    const data = (await response.json()) as { user_id: string; email: string };
    setStoredUserId(data.user_id);
    router.replace("/chat");
  }

  return (
    <main className="auth-page">
      <section className="auth-panel" aria-label="Authentication">
        <div className="auth-brand">
          <Sparkles size={28} />
          <div>
            <h1>Aegis</h1>
            {/* <p>Digital Study</p> */}
          </div>
        </div>

        <div className="auth-tabs" role="tablist">
          <button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>
            Login
          </button>
          <button className={mode === "signup" ? "active" : ""} onClick={() => setMode("signup")}>
            Sign up
          </button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            Email
            <input
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              type="email"
            />
          </label>
          <label>
            Password
            <input
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              value={password}
              minLength={6}
              onChange={(event) => setPassword(event.target.value)}
              required
              type="password"
            />
          </label>
          <button className="primary-button" type="submit" disabled={submitting}>
            {submitting ? "Please wait..." : mode === "login" ? "Login" : "Create account"}
          </button>
          {message ? <p className="form-message">{message}</p> : null}
        </form>
      </section>
    </main>
  );
}

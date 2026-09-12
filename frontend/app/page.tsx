"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8001";

function MailIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="field-icon">
      <path d="M4 6.5h16v11H4z" />
      <path d="m4.5 7 7.5 6 7.5-6" />
    </svg>
  );
}

function LockIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="field-icon">
      <rect x="5" y="10" width="14" height="10" rx="1.5" />
      <path d="M8 10V7a4 4 0 0 1 8 0v3" />
    </svg>
  );
}

function EyeIcon({ isVisible }: { isVisible: boolean }) {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="eye-icon">
      {isVisible ? <path d="m4 4 16 16M10.6 10.6a2 2 0 0 0 2.8 2.8M9.9 5.3A10.8 10.8 0 0 1 12 5c5 0 8.5 5 8.5 5a15 15 0 0 1-3.1 3.3M6.3 7.1C4.5 8.5 3.5 10 3.5 10S7 15 12 15c.7 0 1.3-.1 1.9-.2" /> : <><path d="M3.5 12S7 7 12 7s8.5 5 8.5 5-3.5 5-8.5 5-8.5-5-8.5-5Z" /><circle cx="12" cy="12" r="2" /></>}
      {isVisible ? <><path d="M3.5 12S7 7 12 7s8.5 5 8.5 5-3.5 5-8.5 5-8.5-5-8.5-5Z" /><circle cx="12" cy="12" r="2" /></> : <path d="m4 4 16 16M10.6 10.6a2 2 0 0 0 2.8 2.8M9.9 5.3A10.8 10.8 0 0 1 12 5c5 0 8.5 5 8.5 5a15 15 0 0 1 3.1 3.3M6.3 7.1C4.5 8.5 3.5 10 3.5 10S7 15 12 15c.7 0 1.3-.1 1.9-.2" />}
    </svg>
  );
}

export default function Home() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isVisible, setIsVisible] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (!email.trim() || !email.includes("@")) {
      setError("Enter a valid email address.");
      return;
    }
    if (!password) {
      setError("Enter your password.");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch(`${apiUrl}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!response.ok) {
        setError("The email or password is incorrect.");
        return;
      }
      const result = await response.json();
      if (result.user?.user_type_id !== 1) {
        setError("This account does not have administrator access.");
        return;
      }
      sessionStorage.setItem("access_token", result.access_token);
      router.replace("/admin/dashboard");
    } catch {
      setError("The server could not be reached. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="login-shell">
      <section className="login-intro">
        <div className="brand-lockup">
          <div className="brand-mark" aria-hidden="true"><span /><span /><span /></div>
          <p className="eyebrow">AI Multi-Channel CRM</p>
        </div>
        <div className="intro-content">
          <p className="intro-eyebrow">CUSTOMER INTELLIGENCE, UNIFIED</p>
          <h1>Every conversation.<br />One clear view.</h1>
          <p className="intro">Manage every customer conversation in one place, and<br className="desktop-break" /> turn meaningful interactions into lasting relationships.</p>
        </div>
        <div className="system-status">
          <span className="status-indicator" aria-hidden="true" />
          <span>All systems operational</span>
          <span className="status-divider" aria-hidden="true" />
          <span>Trusted by modern revenue teams</span>
        </div>
      </section>
      <form className="login-form" onSubmit={handleSubmit} noValidate>
        <div className="form-heading">
          <h1>Sign in to your account</h1>
          <p>Enter your credentials to continue.</p>
        </div>
        <div className="field-group">
          <label htmlFor="email">Email</label>
          <div className="input-wrap">
            <MailIcon />
            <input id="email" type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} />
          </div>
        </div>
        <div className="field-group">
          <div className="label-row">
            <label htmlFor="password">Password</label>
            <button className="forgot-password" type="button">Forgot password?</button>
          </div>
          <div className="input-wrap">
            <LockIcon />
            <input id="password" type={isVisible ? "text" : "password"} autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} />
            <button className="visibility-button" type="button" aria-label={isVisible ? "Hide password" : "Show password"} onClick={() => setIsVisible((prev) => !prev)}>
              <EyeIcon isVisible={isVisible} />
            </button>
          </div>
        </div>
        <label className="remember-me">
          <input type="checkbox" />
          <span>Keep me signed in</span>
        </label>
        {error && <p className="form-error" role="alert">{error}</p>}
        <button className="submit-button" type="submit" disabled={isSubmitting}>{isSubmitting ? "Signing in..." : "Sign In"}</button>
        <div className="form-divider" aria-hidden="true"><span>or</span></div>
        <button className="google-button" type="button"><span className="google-mark">G</span>Continue with Google</button>
      </form>
    </main>
  );
}
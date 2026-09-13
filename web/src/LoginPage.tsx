import { FormEvent, useState } from "react";
import { Logo } from "./Logo";

interface LoginPageProps { onAuthenticated: () => void; register?: boolean; }

export function PasswordResetPage() {
  const token = new URLSearchParams(window.location.hash.split("?")[1] || "").get("token") || "";
  const [password, setPassword] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(null);
    const response = await fetch("/auth/password-reset/confirm", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ token, password }) });
    if (!response.ok) { setError("reset link is invalid or expired."); return; }
    setDone(true);
  }
  return <main className="minimal-login-shell"><section className="minimal-login-card"><h1>reset password</h1>{done ? <><p className="login-note">password updated.</p><a className="back-link" href="#/login">sign in</a></> : <form onSubmit={submit}><label><span className="sr-only">new password</span><input type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="new password" minLength={12} required autoFocus /></label><button className="login-submit" type="submit">reset password</button>{error ? <p className="login-note" role="alert">{error}</p> : null}</form>}</section></main>;
}

export function LoginPage({ onAuthenticated, register = false }: LoginPageProps) {
  const [step, setStep] = useState<"email" | "password">("email");
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [resetRequested, setResetRequested] = useState(false);
  const [resetMode, setResetMode] = useState(false);

  async function requestReset(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(null);
    try {
      await fetch("/auth/password-reset/request", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email }) });
      setResetRequested(true);
    } finally { setBusy(false); }
  }

  async function submitLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (step === "email") { setStep("password"); return; }
    setBusy(true);
    const form = new FormData(event.currentTarget);
    try {
      const response = await fetch("/auth/login", { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" }, body: JSON.stringify({ email, password: form.get("password") }) });
      if (!response.ok) throw new Error(response.status === 401 ? "Invalid email or password." : "Sign in is unavailable.");
      onAuthenticated();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Sign in is unavailable."); }
    finally { setBusy(false); }
  }

  async function submitRegistration(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(null); setBusy(true);
    const form = new FormData(event.currentTarget);
    try {
      const response = await fetch("/auth/register", { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" }, body: JSON.stringify({ email: form.get("email"), password: form.get("password"), workspace_name: form.get("workspace_name") || "default", newsletter_opt_in: form.get("newsletter_opt_in") === "on" }) });
      if (!response.ok) throw new Error("Account could not be created.");
      onAuthenticated();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Account could not be created."); }
    finally { setBusy(false); }
  }

  if (!register && resetMode) return (
    <main className="minimal-login-shell"><section className="minimal-login-card"><h1>reset password</h1>{resetRequested ? <p className="login-note">if the account exists, a reset link was sent.</p> : <form onSubmit={requestReset}><label><span className="sr-only">email</span><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="email" required autoFocus /></label><button className="login-submit" type="submit" disabled={busy}>{busy ? "sending…" : "send reset link"}</button></form>}<a className="back-link" href="#/login" onClick={() => setResetMode(false)}>back to sign in</a></section></main>
  );

  if (!register) return (
    <main className="minimal-login-shell">
      <section className="login-art" aria-label="Raffael mark">
        <Logo light className="login-large-logo" />
      </section>
      <section className="minimal-login-card" aria-labelledby="login-title">
        <form onSubmit={submitLogin}>
          <label><span className="sr-only">Email</span><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" placeholder="Email" required autoFocus /></label>
          {step === "password" ? <label><span className="sr-only">Password</span><input type="password" name="password" autoComplete="current-password" placeholder="Password" minLength={12} required autoFocus /></label> : null}
          <button className="login-submit" type="submit" disabled={busy}>{busy ? "Signing in..." : step === "email" ? "Continue" : "Sign in"}</button>
        </form>
        {error ? <p className="login-note" role="alert">{error}</p> : null}
        {step === "password" ? <button className="login-back-step" type="button" onClick={() => setStep("email")}>Use a different email</button> : null}
        <div className="login-secondary-actions">
          <button className="back-link" type="button" onClick={() => { setResetMode(true); setStep("email"); }}>forgot password?</button>
          <a className="back-link" href="#/register">Create a new account</a>
        </div>
      </section>
    </main>
  );

  return (
    <main className="minimal-login-shell register-shell">
      <header className="register-header"><a href="#/login" aria-label="Raffael login"><Logo light /></a></header>
      <section className="minimal-login-card" aria-labelledby="register-title">
        <h1 id="register-title">create account</h1>
        <form onSubmit={submitRegistration}>
          <label><span className="sr-only">email</span><input type="email" name="email" autoComplete="email" placeholder="email" required /></label>
          <label><span className="sr-only">password</span><input type="password" name="password" autoComplete="new-password" placeholder="password" minLength={12} required /></label>
          <label><span className="sr-only">workspace</span><input name="workspace_name" placeholder="workspace" maxLength={120} /></label>
          <label className="newsletter-opt-in"><input type="checkbox" name="newsletter_opt_in" /> <span>send me the raffael newsletter</span></label>
          <button className="login-submit" type="submit" disabled={busy}>{busy ? "Creating…" : "Create account"}</button>
        </form>
        {error ? <p className="login-note" role="alert">{error}</p> : null}
        <a className="back-link" href="#/login">Already have an account? Sign in</a>
      </section>
    </main>
  );
}

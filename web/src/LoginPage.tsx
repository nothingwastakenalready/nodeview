import { FormEvent, useState } from "react";
import { Logo } from "./Logo";

interface LoginPageProps { onAuthenticated: () => void; register?: boolean; }

export function LoginPage({ onAuthenticated, register = false }: LoginPageProps) {
  const [step, setStep] = useState<"email" | "password">("email");
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

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
      const response = await fetch("/auth/register", { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" }, body: JSON.stringify({ email: form.get("email"), password: form.get("password"), workspace_name: form.get("workspace_name") || "default" }) });
      if (!response.ok) throw new Error("Account could not be created.");
      onAuthenticated();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Account could not be created."); }
    finally { setBusy(false); }
  }

  if (!register) return (
    <main className="minimal-login-shell">
      <section className="login-art" aria-label="Raffael mark">
        <Logo light className="login-large-logo" />
      </section>
      <section className="minimal-login-card" aria-labelledby="login-title">
        <a className="create-link" href="#/register">Create account</a>
        <form onSubmit={submitLogin}>
          <label><span className="sr-only">Email</span><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" placeholder="Email" required autoFocus /></label>
          {step === "password" ? <label><span className="sr-only">Password</span><input type="password" name="password" autoComplete="current-password" placeholder="Password" minLength={12} required autoFocus /></label> : null}
          <button className="sr-only" type="submit">Submit</button>
        </form>
        {error ? <p className="login-note" role="alert">{error}</p> : null}
        {step === "password" ? <button className="login-back-step" type="button" onClick={() => setStep("email")}>Use a different email</button> : null}
        <a className="back-link" href="#/register">Create a new account</a>
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
          <button className="login-submit" type="submit" disabled={busy}>{busy ? "Creating…" : "Create account"}</button>
        </form>
        {error ? <p className="login-note" role="alert">{error}</p> : null}
        <a className="back-link" href="#/login">Already have an account? Sign in</a>
      </section>
    </main>
  );
}

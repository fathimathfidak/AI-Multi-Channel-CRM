"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8001";

function EyeIcon({ isVisible }: { isVisible: boolean }) {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="eye-icon">
      {isVisible ? <path d="m4 4 16 16M10.6 10.6a2 2 0 0 0 2.8 2.8M9.9 5.3A10.8 10.8 0 0 1 12 5c5 0 8.5 5 8.5 5a15 15 0 0 1-3.1 3.3M6.3 7.1C4.5 8.5 3.5 10 3.5 10S7 15 12 15c.7 0 1.3-.1 1.9-.2" /> : <><path d="M3.5 12S7 7 12 7s8.5 5 8.5 5-3.5 5-8.5 5-8.5-5-8.5-5Z" /><circle cx="12" cy="12" r="2" /></>}
      {isVisible ? <><path d="M3.5 12S7 7 12 7s8.5 5 8.5 5-3.5 5-8.5 5-8.5-5-8.5-5Z" /><circle cx="12" cy="12" r="2" /></> : <path d="m4 4 16 16M10.6 10.6a2 2 0 0 0 2.8 2.8M9.9 5.3A10.8 10.8 0 0 1 12 5c5 0 8.5 5 8.5 5a15 15 0 0 1 3.1 3.3M6.3 7.1C4.5 8.5 3.5 10 3.5 10S7 15 12 15c.7 0 1.3-.1 1.9-.2" />}
    </svg>
  );
}

export default function NewSalesPerson() {
  const router = useRouter();
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    password: "",
    confirm_password: "",
    status: "1",
  });
  const [error, setError] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const [confirmIsVisible, setConfirmIsVisible] = useState(false);

  function updateField(field: keyof typeof form, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function createSalesPerson(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (!form.first_name.trim()) { setError("First name is required."); return; }
    if (!form.email.trim() || !form.email.includes("@") || form.email.startsWith("@") || form.email.endsWith("@")) {
      setError("Enter a valid email address.");
      return;
    }
    if (!form.password) { setError("Password is required."); return; }
    if (form.password !== form.confirm_password) { setError("Passwords do not match."); return; }

    setIsSaving(true);
    try {
      const response = await fetch(`${apiUrl}/admin/sales-persons`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${sessionStorage.getItem("access_token")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          first_name: form.first_name.trim(),
          last_name: form.last_name.trim() || null,
          email: form.email.trim(),
          phone: form.phone.trim() || null,
          password: form.password,
          confirm_password: form.confirm_password,
          status: Number(form.status),
        }),
      });
      const body = await response.json().catch(() => ({}));
      if (response.status === 401) {
        sessionStorage.removeItem("access_token");
        router.replace("/");
        return;
      }
      if (!response.ok) throw new Error(body.detail || "Unable to create sales person");
      router.push("/admin/sales-persons");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to create sales person");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="leads-content sales-person-form-page">
      <div className="leads-header">
        <div>
          <p className="eyebrow">Admin workspace</p>
          <h1>Add Sales Person</h1>
          <p className="intro">Create a new member of your sales team.</p>
        </div>
      </div>
      <form className="edit-modal sales-person-form" onSubmit={createSalesPerson}>
        <div className="edit-grid">
          <label>First Name *<input value={form.first_name} onChange={(event) => updateField("first_name", event.target.value)} /></label>
          <label>Last Name<input value={form.last_name} onChange={(event) => updateField("last_name", event.target.value)} /></label>
          <label>Email *<input type="email" value={form.email} onChange={(event) => updateField("email", event.target.value)} /></label>
          <label>Phone<input value={form.phone} onChange={(event) => updateField("phone", event.target.value)} /></label>
          <label>Password *<div className="input-wrap"><input type={isVisible ? "text" : "password"} autoComplete="new-password" value={form.password} onChange={(event) => updateField("password", event.target.value)} /><button className="visibility-button" type="button" aria-label={isVisible ? "Hide password" : "Show password"} onClick={() => setIsVisible((prev) => !prev)}><EyeIcon isVisible={isVisible} /></button></div></label>
          <label>Confirm Password *<div className="input-wrap"><input type={confirmIsVisible ? "text" : "password"} autoComplete="new-password" value={form.confirm_password} onChange={(event) => updateField("confirm_password", event.target.value)} /><button className="visibility-button" type="button" aria-label={confirmIsVisible ? "Hide confirm password" : "Show confirm password"} onClick={() => setConfirmIsVisible((prev) => !prev)}><EyeIcon isVisible={confirmIsVisible} /></button></div></label>
          <label>Status *<select value={form.status} onChange={(event) => updateField("status", event.target.value)}><option value="1">ACTIVE</option><option value="2">INACTIVE</option></select></label>
        </div>
        {error && <p className="form-error" role="alert">{error}</p>}
        <div className="modal-actions">
          <Link className="modal-cancel" href="/admin/sales-persons">Cancel</Link>
          <button className="submit-button" type="submit" disabled={isSaving}>{isSaving ? "Creating..." : "Create"}</button>
        </div>
      </form>
    </section>
  );
}
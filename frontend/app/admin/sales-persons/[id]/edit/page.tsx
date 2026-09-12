"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8001";

type SalesPerson = {
  user_id: number;
  first_name: string;
  last_name: string | null;
  email: string;
  phone: string | null;
  status: number;
  created_at: string;
};

function formatDate(value: string) {
  const timestamp = /(?:Z|[+-]\d{2}:\d{2})$/.test(value) ? value : `${value}Z`;
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Kolkata",
  }).format(new Date(timestamp));
}

export default function EditSalesPerson() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const [form, setForm] = useState({ first_name: "", last_name: "", email: "", phone: "", status: "1" });
  const [salesPerson, setSalesPerson] = useState<SalesPerson | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = sessionStorage.getItem("access_token");
    if (!token) { router.replace("/"); return; }
    fetch(`${apiUrl}/admin/sales-persons/${params.id}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (response) => {
        const body = await response.json().catch(() => ({}));
        if (response.status === 401) { sessionStorage.removeItem("access_token"); router.replace("/"); return; }
        if (!response.ok) throw new Error(body.detail || "Unable to load sales person");
        const salesPerson: SalesPerson = body.sales_person;
        setSalesPerson(salesPerson);
        setForm({ first_name: salesPerson.first_name, last_name: salesPerson.last_name || "", email: salesPerson.email, phone: salesPerson.phone || "", status: String(salesPerson.status) });
      })
      .catch((requestError) => setError(requestError instanceof Error ? requestError.message : "Unable to load sales person"))
      .finally(() => setIsLoading(false));
  }, [params.id, router]);

  function updateField(field: keyof typeof form, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function updateSalesPerson(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (!form.first_name.trim()) { setError("First name is required."); return; }
    if (!form.email.trim() || !form.email.includes("@") || form.email.startsWith("@") || form.email.endsWith("@")) { setError("Enter a valid email address."); return; }
    setIsSaving(true);
    try {
      const response = await fetch(`${apiUrl}/admin/sales-persons/${params.id}`, {
        method: "PATCH",
        headers: { Authorization: `Bearer ${sessionStorage.getItem("access_token")}`, "Content-Type": "application/json" },
        body: JSON.stringify({ first_name: form.first_name.trim(), last_name: form.last_name.trim() || null, email: form.email.trim(), phone: form.phone.trim() || null, status: Number(form.status) }),
      });
      const body = await response.json().catch(() => ({}));
      if (response.status === 401) { sessionStorage.removeItem("access_token"); router.replace("/"); return; }
      if (!response.ok) throw new Error(body.detail || "Unable to update sales person");
      router.push("/admin/sales-persons");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to update sales person");
    } finally { setIsSaving(false); }
  }

  if (isLoading) return <main className="loading-screen">Loading sales person...</main>;

  return (
    <section className="leads-content sales-person-form-page">
      <div className="leads-header"><div><p className="eyebrow">Admin workspace</p><h1>Edit Sales Person</h1><p className="intro">Update this member of your sales team.</p></div></div>
      {error && !form.email && <p className="form-error" role="alert">{error}</p>}
      {form.email && salesPerson && <form className="edit-modal sales-person-form" onSubmit={updateSalesPerson}>
        <div className="edit-grid">
          <label>First Name *<input value={form.first_name} onChange={(event) => updateField("first_name", event.target.value)} /></label>
          <label>Last Name<input value={form.last_name} onChange={(event) => updateField("last_name", event.target.value)} /></label>
          <label>Email *<input type="email" value={form.email} onChange={(event) => updateField("email", event.target.value)} /></label>
          <label>Phone<input value={form.phone} onChange={(event) => updateField("phone", event.target.value)} /></label>
          <label>Status *<select value={form.status} onChange={(event) => updateField("status", event.target.value)}><option value="1">ACTIVE</option><option value="2">INACTIVE</option></select></label>
          <label>User ID<input readOnly value={salesPerson.user_id} /></label>
        </div>
        {error && <p className="form-error" role="alert">{error}</p>}
        <div className="modal-actions"><Link className="modal-cancel" href="/admin/sales-persons">Cancel</Link><button className="submit-button" type="submit" disabled={isSaving}>{isSaving ? "Updating..." : "Update"}</button></div>
      </form>}
    </section>
  );
}
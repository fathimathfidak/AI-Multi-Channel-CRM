"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8001";
const pageSize = 50;

type User = {
  first_name: string;
  last_name?: string | null;
  email: string;
};

type Lead = {
  lead_id: number;
  company: string | null;
  name: string | null;
  email: string | null;
  phone: string | null;
  source: string | null;
  market_source_id: number | null;
  message: string | null;
  campaign_id: string | null;
  location: string | null;
  priority_id: number | null;
  priority: string | null;
  created_at: string;
  updated_at: string;
};

type LeadsResponse = {
  leads: Lead[];
  current_page: number;
  page_size: number;
  total_count: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
};

type LookupOption = { id: number; name: string };

type EditValues = {
  lead_id: number;
  name: string;
  company: string;
  email: string;
  phone: string;
  market_source_id: string;
  message: string;
  campaign_id: string;
  location: string;
  priority_id: string;
};

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default function AdminLeads() {
  const router = useRouter();
  const [result, setResult] = useState<LeadsResponse | null>(null);
  const [page, setPage] = useState(1);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [editingLead, setEditingLead] = useState<EditValues | null>(null);
  const [marketSources, setMarketSources] = useState<LookupOption[]>([]);
  const [priorities, setPriorities] = useState<LookupOption[]>([]);
  const [saveError, setSaveError] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");

  useEffect(() => {
    const token = sessionStorage.getItem("access_token");
    if (!token) {
      router.replace("/");
      return;
    }

    let cancelled = false;
    setIsLoading(true);
    Promise.all([
      fetch(`${apiUrl}/admin/leads?page=${page}&page_size=${pageSize}`, { headers: { Authorization: `Bearer ${token}` } }),
      fetch(`${apiUrl}/admin/lead-options`, { headers: { Authorization: `Bearer ${token}` } }),
    ])
      .then(async ([leadsResponse, optionsResponse]) => {
        if (!leadsResponse.ok || !optionsResponse.ok) throw new Error("Unable to load leads");
        const leadsResult = await leadsResponse.json();
        const optionsResult = await optionsResponse.json();
        if (!cancelled) {
          setResult(leadsResult);
          setMarketSources(optionsResult.market_sources.map((item: { market_source_id: number; name: string }) => ({ id: item.market_source_id, name: item.name })));
          setPriorities(optionsResult.priorities.map((item: { priority_id: number; name: string }) => ({ id: item.priority_id, name: item.name })));
          setError("");
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError("The leads could not be loaded. Please try again.");
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [page, router]);

  function openEditor(lead: Lead) {
    setSaveError("");
    setSuccessMessage("");
    setEditingLead({
      lead_id: lead.lead_id,
      name: lead.name || "",
      company: lead.company || "",
      email: lead.email || "",
      phone: lead.phone || "",
      market_source_id: lead.market_source_id?.toString() || "",
      message: lead.message || "",
      campaign_id: lead.campaign_id || "",
      location: lead.location || "",
      priority_id: lead.priority_id?.toString() || "",
    });
  }

  function updateField(field: keyof EditValues, value: string) {
    setEditingLead((current) => current ? { ...current, [field]: value } : current);
  }

  async function saveLead(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editingLead) return;
    setIsSaving(true);
    setSaveError("");
    const token = sessionStorage.getItem("access_token");
    try {
      const response = await fetch(`${apiUrl}/admin/leads/${editingLead.lead_id}`, {
        method: "PATCH",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({
          name: editingLead.name || null,
          company: editingLead.company || null,
          email: editingLead.email || null,
          phone: editingLead.phone || null,
          market_source_id: editingLead.market_source_id ? Number(editingLead.market_source_id) : null,
          message: editingLead.message || null,
          campaign_id: editingLead.campaign_id || null,
          location: editingLead.location || null,
          priority_id: editingLead.priority_id ? Number(editingLead.priority_id) : null,
        }),
      });
      if (!response.ok) throw new Error("Unable to save lead");
      setEditingLead(null);
      setSuccessMessage("Lead updated successfully.");
      setResult((current) => current ? {
        ...current,
        leads: current.leads.map((lead) => lead.lead_id === editingLead.lead_id ? {
          ...lead,
          name: editingLead.name || null,
          company: editingLead.company || null,
          email: editingLead.email || null,
          phone: editingLead.phone || null,
          market_source_id: editingLead.market_source_id ? Number(editingLead.market_source_id) : null,
          source: marketSources.find((item) => item.id === Number(editingLead.market_source_id))?.name || null,
          message: editingLead.message || null,
          campaign_id: editingLead.campaign_id || null,
          location: editingLead.location || null,
          priority_id: editingLead.priority_id ? Number(editingLead.priority_id) : null,
          priority: priorities.find((item) => item.id === Number(editingLead.priority_id))?.name || null,
        } : lead),
      } : current);
    } catch {
      setSaveError("The lead could not be saved. Please try again.");
    } finally {
      setIsSaving(false);
    }
  }

  async function deleteLead(lead: Lead) {
    if (!window.confirm(`Delete ${lead.name || "this lead"}?`)) return;
    const token = sessionStorage.getItem("access_token");
    try {
      const response = await fetch(`${apiUrl}/admin/leads/${lead.lead_id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Unable to delete lead");
      setSuccessMessage("Lead deleted successfully.");
      if (result?.leads.length === 1 && page > 1) {
        setPage((current) => current - 1);
      } else {
        setResult((current) => current ? {
          ...current,
          leads: current.leads.filter((item) => item.lead_id !== lead.lead_id),
          total_count: current.total_count - 1,
          total_pages: Math.ceil((current.total_count - 1) / current.page_size),
        } : current);
      }
    } catch {
      setError("The lead could not be deleted. Please try again.");
    }
  }

  if (isLoading && !result) return <main className="loading-screen">Loading leads...</main>;
  const firstLead = result && result.total_count > 0 ? (result.current_page - 1) * result.page_size + 1 : 0;
  const lastLead = result ? Math.min(result.current_page * result.page_size, result.total_count) : 0;

  return (
    <>
    <section className="leads-content">
        <div className="leads-header">
          <div>
            <p className="eyebrow">Admin workspace</p>
            <h1>Leads</h1>
          </div>
          {result && <p className="lead-count">{result.total_count} {result.total_count === 1 ? "lead" : "leads"}</p>}
        </div>
        {error && <p className="form-error" role="alert">{error}</p>}
        {successMessage && <p className="success-message" role="status">{successMessage}</p>}
        <div className="leads-table-wrap">
          <table className="leads-table">
            <thead>
              <tr><th>Lead ID</th><th>Name</th><th>Company</th><th>Email</th><th>Phone</th><th>Source</th><th>Message</th><th>Campaign ID</th><th>Location</th><th>Priority</th><th>Created At</th><th>Updated At</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {result?.leads.length === 0 ? (
                <tr><td colSpan={13}>No data available</td></tr>
              ) : result?.leads.map((lead) => (
                <tr key={lead.lead_id}>
                  <td>{lead.lead_id}</td>
                  <td className="lead-name">{lead.name || "Unnamed lead"}</td>
                  <td>{lead.company || "-"}</td>
                  <td>{lead.email || "-"}</td>
                  <td>{lead.phone || "-"}</td>
                  <td>{lead.source || "-"}</td>
                  <td className="lead-message">{lead.message || "-"}</td>
                  <td>{lead.campaign_id || "-"}</td>
                  <td>{lead.location || "-"}</td>
                  <td><span className={`priority priority-${lead.priority?.toLowerCase() || "unknown"}`}>{lead.priority || "-"}</span></td>
                  <td>{formatDate(lead.created_at)}</td>
                  <td>{formatDate(lead.updated_at)}</td>
                  <td className="lead-actions">
                    <button className="table-action" type="button" onClick={() => openEditor(lead)}>Edit</button>
                    <button className="table-action table-action-danger" type="button" onClick={() => deleteLead(lead)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="pagination" aria-label="Lead pagination">
          <span>{firstLead}-{lastLead} of {result?.total_count ?? 0}</span>
          <div className="pagination-controls">
            <button type="button" disabled={!result?.has_previous || isLoading} onClick={() => setPage((current) => current - 1)}>Previous</button>
            <span>Page {result?.current_page ?? page}</span>
            <button type="button" disabled={!result?.has_next || isLoading} onClick={() => setPage((current) => current + 1)}>Next</button>
          </div>
        </div>
      </section>
      {editingLead && (
        <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget && !isSaving) setEditingLead(null); }}>
          <form className="edit-modal" onSubmit={saveLead}>
            <div className="modal-heading">
              <div><p className="eyebrow">Lead details</p><h2>Edit lead</h2></div>
              <span className="read-only-id">ID {editingLead.lead_id}</span>
            </div>
            <div className="edit-grid">
              <label>Name<input value={editingLead.name} onChange={(event) => updateField("name", event.target.value)} /></label>
              <label>Company<input value={editingLead.company} onChange={(event) => updateField("company", event.target.value)} /></label>
              <label>Email<input type="email" value={editingLead.email} onChange={(event) => updateField("email", event.target.value)} /></label>
              <label>Phone<input value={editingLead.phone} onChange={(event) => updateField("phone", event.target.value)} /></label>
              <label>Source<select value={editingLead.market_source_id} onChange={(event) => updateField("market_source_id", event.target.value)}><option value="">No source</option>{marketSources.map((option) => <option key={option.id} value={option.id}>{option.name}</option>)}</select></label>
              <label>Priority<select value={editingLead.priority_id} onChange={(event) => updateField("priority_id", event.target.value)}><option value="">No priority</option>{priorities.map((option) => <option key={option.id} value={option.id}>{option.name}</option>)}</select></label>
              <label>Campaign ID<input value={editingLead.campaign_id} onChange={(event) => updateField("campaign_id", event.target.value)} /></label>
              <label>Location<input value={editingLead.location} onChange={(event) => updateField("location", event.target.value)} /></label>
              <label className="edit-message">Message<textarea value={editingLead.message} onChange={(event) => updateField("message", event.target.value)} /></label>
            </div>
            {saveError && <p className="form-error" role="alert">{saveError}</p>}
            <div className="modal-actions"><button className="modal-cancel" type="button" disabled={isSaving} onClick={() => setEditingLead(null)}>Cancel</button><button className="submit-button" type="submit" disabled={isSaving}>{isSaving ? "Saving..." : "Save changes"}</button></div>
          </form>
        </div>
      )}
    </>
  );
}
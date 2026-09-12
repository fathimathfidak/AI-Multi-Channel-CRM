"use client";

import { FormEvent, useEffect, useState } from "react";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8001";

type Profile = {
  user_id: number;
  first_name: string;
  last_name: string | null;
  email: string;
  phone: string | null;
};

type FormState = {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
};

const emptyForm: FormState = {
  first_name: "",
  last_name: "",
  email: "",
  phone: "",
};

export default function AdminSettings() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    async function loadProfile() {
      try {
        const response = await fetch(`${apiUrl}/admin/settings/profile`, {
          headers: { Authorization: `Bearer ${sessionStorage.getItem("access_token")}` },
        });
        const body = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(body.detail || "Unable to load your profile.");
        setProfile(body.profile);
        setForm({
          first_name: body.profile.first_name,
          last_name: body.profile.last_name ?? "",
          email: body.profile.email,
          phone: body.profile.phone ?? "",
        });
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "Unable to load your profile.");
      } finally {
        setIsLoading(false);
      }
    }
    void loadProfile();
  }, []);

  function updateField(field: keyof FormState, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
    setMessage("");
    setError("");
  }

  async function updateProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    setError("");
    setIsSaving(true);
    try {
      const response = await fetch(`${apiUrl}/admin/settings/profile`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${sessionStorage.getItem("access_token")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          first_name: form.first_name.trim(),
          last_name: form.last_name.trim() || null,
          email: form.email.trim(),
          phone: form.phone.trim() || null,
        }),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body.detail || "Unable to update your profile.");
      setProfile(body.profile);
      setForm({
        first_name: body.profile.first_name,
        last_name: body.profile.last_name ?? "",
        email: body.profile.email,
        phone: body.profile.phone ?? "",
      });
      setMessage("Your profile was updated successfully.");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to update your profile.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="dashboard-content settings-page">
      <p className="eyebrow">Admin workspace</p>
      <h1>Settings</h1>
      <p className="intro">Manage your administrator profile.</p>
      <div className="settings-section-heading">
        <div>
          <h2>Profile</h2>
          <p>Update the contact details for your administrator account.</p>
        </div>
      </div>
      {isLoading ? <p className="settings-loading">Loading profile...</p> : (
        <form className="edit-modal settings-form" onSubmit={updateProfile}>
          <div className="edit-grid">
            <label>User ID<input value={profile?.user_id ?? ""} readOnly /></label>
            <label>First Name *<input value={form.first_name} onChange={(event) => updateField("first_name", event.target.value)} /></label>
            <label>Last Name<input value={form.last_name} onChange={(event) => updateField("last_name", event.target.value)} /></label>
            <label>Email *<input type="email" value={form.email} onChange={(event) => updateField("email", event.target.value)} /></label>
            <label>Phone<input value={form.phone} onChange={(event) => updateField("phone", event.target.value)} /></label>
          </div>
          {error && <p className="form-error" role="alert">{error}</p>}
          {message && <p className="success-message" role="status">{message}</p>}
          <div className="modal-actions">
            <button className="submit-button" type="submit" disabled={isSaving}>{isSaving ? "Updating..." : "Update"}</button>
          </div>
        </form>
      )}
    </section>
  );
}
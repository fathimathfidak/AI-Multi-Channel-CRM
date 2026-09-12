"use client";

import { FormEvent, useState } from "react";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8001";

type PasswordField = "current_password" | "new_password" | "confirm_password";

type PasswordForm = Record<PasswordField, string>;

const emptyForm: PasswordForm = {
  current_password: "",
  new_password: "",
  confirm_password: "",
};

function EyeIcon({ isVisible }: { isVisible: boolean }) {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="eye-icon">
      {isVisible ? (
        <>
          <path d="M3.5 12S7 7 12 7s8.5 5 8.5 5-3.5 5-8.5 5-8.5-5-8.5-5Z" />
          <circle cx="12" cy="12" r="2" />
        </>
      ) : (
        <path d="m4 4 16 16M10.6 10.6a2 2 0 0 0 2.8 2.8M9.9 5.3A10.8 10.8 0 0 1 12 5c5 0 8.5 5 8.5 5a15 15 0 0 1-3.1 3.3M6.3 7.1C4.5 8.5 3.5 10 3.5 10S7 15 12 15c.7 0 1.3-.1 1.9-.2" />
      )}
    </svg>
  );
}

export default function ChangePassword() {
  const [form, setForm] = useState<PasswordForm>(emptyForm);
  const [isVisible, setIsVisible] = useState<Record<PasswordField, boolean>>({
    current_password: false,
    new_password: false,
    confirm_password: false,
  });
  const [error, setError] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  function updateField(field: PasswordField, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
    setError("");
  }

  function toggleVisibility(field: PasswordField) {
    setIsVisible((current) => ({ ...current, [field]: !current[field] }));
  }

  async function changePassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (!form.current_password) {
      setError("Current password is required.");
      return;
    }
    if (!form.new_password) {
      setError("New password is required.");
      return;
    }
    if (!form.confirm_password) {
      setError("Confirm password is required.");
      return;
    }
    if (form.new_password !== form.confirm_password) {
      setError("New password and confirm password do not match.");
      return;
    }

    setIsSaving(true);
    try {
      const response = await fetch(`${apiUrl}/admin/settings/change-password`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${sessionStorage.getItem("access_token")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(form),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body.detail || "Unable to change your password.");
      setShowSuccess(true);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to change your password.");
    } finally {
      setIsSaving(false);
    }
  }

  function closeSuccess() {
    setShowSuccess(false);
    setForm(emptyForm);
    setIsVisible({
      current_password: false,
      new_password: false,
      confirm_password: false,
    });
  }

  const fields: Array<{ key: PasswordField; label: string }> = [
    { key: "current_password", label: "Current Password" },
    { key: "new_password", label: "New Password" },
    { key: "confirm_password", label: "Confirm Password" },
  ];

  return (
    <section className="dashboard-content password-page">
      <p className="eyebrow">Admin workspace</p>
      <h1>Change Password</h1>
      <p className="intro">Update the password for your administrator account.</p>
      <form className="edit-modal password-form" onSubmit={changePassword}>
        <div className="password-fields">
          {fields.map(({ key, label }) => (
            <label key={key}>
              {label}
              <div className="input-wrap">
                <input
                  type={isVisible[key] ? "text" : "password"}
                  autoComplete={key === "current_password" ? "current-password" : "new-password"}
                  value={form[key]}
                  onChange={(event) => updateField(key, event.target.value)}
                />
                <button
                  className="visibility-button"
                  type="button"
                  aria-label={isVisible[key] ? `Hide ${label.toLowerCase()}` : `Show ${label.toLowerCase()}`}
                  title={isVisible[key] ? `Hide ${label.toLowerCase()}` : `Show ${label.toLowerCase()}`}
                  onClick={() => toggleVisibility(key)}
                >
                  <EyeIcon isVisible={isVisible[key]} />
                </button>
              </div>
            </label>
          ))}
        </div>
        {error && <p className="form-error" role="alert">{error}</p>}
        <div className="modal-actions">
          <button className="submit-button" type="submit" disabled={isSaving}>
            {isSaving ? "Changing..." : "Change Password"}
          </button>
        </div>
      </form>
      {showSuccess && (
        <div className="modal-backdrop" role="presentation">
          <section className="success-modal" role="dialog" aria-modal="true" aria-labelledby="password-success-title">
            <p className="eyebrow">Admin workspace</p>
            <h2 id="password-success-title">Password successfully changed.</h2>
            <p>Your password has been updated.</p>
            <button className="submit-button" type="button" onClick={closeSuccess}>Done</button>
          </section>
        </div>
      )}
    </section>
  );
}

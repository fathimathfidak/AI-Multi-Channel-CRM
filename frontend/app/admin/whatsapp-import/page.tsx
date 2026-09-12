"use client";

import { ChangeEvent, useState } from "react";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8001";

export default function WhatsAppLeadImport() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  function selectFile(event: ChangeEvent<HTMLInputElement>) {
    setSelectedFile(event.target.files?.[0] ?? null);
    setSuccessMessage("");
    setErrorMessage("");
  }

  async function importLead() {
    if (!selectedFile) {
      setErrorMessage("Select a JSON file to import.");
      return;
    }
    setIsImporting(true);
    setSuccessMessage("");
    setErrorMessage("");
    try {
      let payload: unknown;
      try {
        payload = JSON.parse(await selectedFile.text());
      } catch {
        throw new Error("The selected file contains invalid JSON.");
      }
      const response = await fetch(`${apiUrl}/admin/whatsapp/import`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${sessionStorage.getItem("access_token")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body.detail || "Unable to import the lead.");
      if (body.status === "duplicate") {
        setSuccessMessage("This WhatsApp lead was already imported.");
      } else {
        setSuccessMessage(body.message || "WhatsApp lead imported successfully.");
      }
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Unable to import the lead.");
    } finally {
      setIsImporting(false);
    }
  }

  return (
    <section className="dashboard-content whatsapp-import-page">
      <p className="eyebrow">Admin workspace</p>
      <h1>WhatsApp Lead Import</h1>
      <p className="intro">Import a mock WhatsApp lead response into the CRM.</p>
      <div className="edit-modal whatsapp-import-form">
        <label className="whatsapp-file-label" htmlFor="whatsapp-lead-file">
          JSON file
          <input id="whatsapp-lead-file" type="file" accept=".json,application/json" onChange={selectFile} />
        </label>
        {selectedFile && <p className="whatsapp-selected-file">Selected: {selectedFile.name}</p>}
        {errorMessage && <p className="form-error" role="alert">{errorMessage}</p>}
        {successMessage && <p className="success-message" role="status">{successMessage}</p>}
        <button className="submit-button" type="button" onClick={importLead} disabled={isImporting}>
          {isImporting ? "Importing..." : "Import"}
        </button>
      </div>
    </section>
  );
}
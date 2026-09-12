"use client";

import { FormEvent, useMemo, useState } from "react";

const saleStatuses = [
  { value: "1", label: "Draft" },
  { value: "2", label: "Confirmed" },
  { value: "3", label: "Completed" },
  { value: "4", label: "Cancelled" },
];

const paymentStatuses = [
  { value: "1", label: "Pending" },
  { value: "2", label: "Partial" },
  { value: "3", label: "Paid" },
  { value: "4", label: "Refunded" },
  { value: "5", label: "Failed" },
];

type Sale = {
  sale_id: number;
  product_id: string;
  lead_id: string;
  invoice_id: string;
  sale_price: string;
  sale_paid: string;
  sale_due: string;
  sale_tax: string;
  sale_status: string;
  payment_status: string;
  payment_method: string;
  description: string;
  created_at: string;
  created_by: string;
};

type SaleForm = Omit<Sale, "sale_id" | "created_at" | "created_by">;

const blankForm: SaleForm = {
  product_id: "",
  lead_id: "",
  invoice_id: "",
  sale_price: "",
  sale_paid: "",
  sale_due: "",
  sale_tax: "",
  sale_status: "1",
  payment_status: "1",
  payment_method: "",
  description: "",
};

const initialSales: Sale[] = [
  {
    sale_id: 1042,
    product_id: "PRD-204",
    lead_id: "LEAD-8821",
    invoice_id: "INV-2026-1042",
    sale_price: "2400.00",
    sale_paid: "2400.00",
    sale_due: "0.00",
    sale_tax: "192.00",
    sale_status: "3",
    payment_status: "3",
    payment_method: "Bank transfer",
    description: "Annual growth package",
    created_at: "2026-09-06T10:30:00",
    created_by: "Admin User",
  },
  {
    sale_id: 1041,
    product_id: "PRD-118",
    lead_id: "LEAD-8814",
    invoice_id: "INV-2026-1041",
    sale_price: "875.00",
    sale_paid: "400.00",
    sale_due: "475.00",
    sale_tax: "70.00",
    sale_status: "2",
    payment_status: "2",
    payment_method: "Card",
    description: "Initial implementation deposit",
    created_at: "2026-09-05T14:15:00",
    created_by: "Admin User",
  },
];

function statusLabel(value: string, options: { value: string; label: string }[]) {
  return options.find((option) => option.value === value)?.label ?? value;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function money(value: string) {
  return value ? Number(value).toLocaleString("en-US", { minimumFractionDigits: 2 }) : "-";
}

export default function AdminSales() {
  const [sales, setSales] = useState(initialSales);
  const [form, setForm] = useState<SaleForm>(blankForm);
  const [editingSaleId, setEditingSaleId] = useState<number | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [saleStatus, setSaleStatus] = useState("");
  const [paymentStatus, setPaymentStatus] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("");
  const [notice, setNotice] = useState("");

  const filteredSales = useMemo(() => {
    const search = query.trim().toLowerCase();
    return sales.filter((sale) => {
      const matchesSearch = !search || Object.values(sale).some((value) => String(value).toLowerCase().includes(search));
      return matchesSearch
        && (!saleStatus || sale.sale_status === saleStatus)
        && (!paymentStatus || sale.payment_status === paymentStatus)
        && (!paymentMethod || sale.payment_method === paymentMethod);
    });
  }, [paymentMethod, paymentStatus, query, saleStatus, sales]);

  const paymentMethods = Array.from(new Set(sales.map((sale) => sale.payment_method).filter(Boolean)));

  function openCreate() {
    setEditingSaleId(null);
    setForm({ ...blankForm });
    setNotice("");
    setIsFormOpen(true);
  }

  function openEdit(sale: Sale) {
    const { sale_id: _saleId, created_at: _createdAt, created_by: _createdBy, ...values } = sale;
    setEditingSaleId(sale.sale_id);
    setForm(values);
    setNotice("");
    setIsFormOpen(true);
  }

  function updateField(field: keyof SaleForm, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function saveSale(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const saleId = editingSaleId ?? Math.max(0, ...sales.map((sale) => sale.sale_id)) + 1;
    const sale: Sale = {
      ...form,
      sale_id: saleId,
      created_at: editingSaleId ? sales.find((item) => item.sale_id === editingSaleId)?.created_at ?? new Date().toISOString() : new Date().toISOString(),
      created_by: editingSaleId ? sales.find((item) => item.sale_id === editingSaleId)?.created_by ?? "Admin User" : "Admin User",
    };
    setSales((current) => editingSaleId ? current.map((item) => item.sale_id === editingSaleId ? sale : item) : [sale, ...current]);
    setNotice(editingSaleId ? "Sale updated in this view." : "Sale added to this view.");
    setIsFormOpen(false);
  }

  function deleteSale(sale: Sale) {
    if (!window.confirm(`Delete sale ${sale.sale_id}?`)) return;
    setSales((current) => current.filter((item) => item.sale_id !== sale.sale_id));
    setNotice("Sale removed from this view.");
  }

  return (
    <section className="leads-content sales-content">
      <div className="leads-header sales-page-header">
        <div>
          <p className="eyebrow">Admin workspace / Revenue</p>
          <h1>Sales</h1>
          <p className="intro">Track completed transactions, payment progress, and customer revenue in one place.</p>
        </div>
        <button className="submit-button" type="button" onClick={openCreate}>+ Add Sale</button>
      </div>

      {notice && <p className="success-message" role="status">{notice}</p>}

      <div className="sales-filter-bar" aria-label="Sales filters">
        <label className="sales-search">Search<input value={query} placeholder="Search sales, invoices, leads..." onChange={(event) => setQuery(event.target.value)} /></label>
        <label>Sale Status<select value={saleStatus} onChange={(event) => setSaleStatus(event.target.value)}><option value="">All statuses</option>{saleStatuses.map((status) => <option key={status.value} value={status.value}>{status.label}</option>)}</select></label>
        <label>Payment Status<select value={paymentStatus} onChange={(event) => setPaymentStatus(event.target.value)}><option value="">All statuses</option>{paymentStatuses.map((status) => <option key={status.value} value={status.value}>{status.label}</option>)}</select></label>
        <label>Payment Method<select value={paymentMethod} onChange={(event) => setPaymentMethod(event.target.value)}><option value="">All methods</option>{paymentMethods.map((method) => <option key={method} value={method}>{method}</option>)}</select></label>
      </div>

      <div className="sales-table-heading"><span>{filteredSales.length} {filteredSales.length === 1 ? "sale" : "sales"}</span><span className="sales-ui-note">Local preview</span></div>
      <div className="leads-table-wrap sales-table-wrap">
        <table className="leads-table sales-table">
          <thead><tr><th>SALE ID</th><th>PRODUCT ID</th><th>LEAD ID</th><th>INVOICE ID</th><th>SALE PRICE</th><th>SALE PAID</th><th>SALE DUE</th><th>SALE TAX</th><th>SALE STATUS</th><th>PAYMENT STATUS</th><th>PAYMENT METHOD</th><th>DESCRIPTION</th><th>CREATED AT</th><th>CREATED BY</th><th>ACTIONS</th></tr></thead>
          <tbody>
            {filteredSales.length === 0 ? <tr><td className="sales-empty" colSpan={15}>No data available</td></tr> : filteredSales.map((sale) => (
              <tr key={sale.sale_id}>
                <td className="sales-id">{sale.sale_id}</td><td>{sale.product_id || "-"}</td><td>{sale.lead_id || "-"}</td><td>{sale.invoice_id || "-"}</td><td>{money(sale.sale_price)}</td><td>{money(sale.sale_paid)}</td><td>{money(sale.sale_due)}</td><td>{money(sale.sale_tax)}</td>
                <td><span className={`sales-badge sale-status-${sale.sale_status}`}>{statusLabel(sale.sale_status, saleStatuses)}</span></td><td><span className={`sales-badge payment-status-${sale.payment_status}`}>{statusLabel(sale.payment_status, paymentStatuses)}</span></td><td>{sale.payment_method || "-"}</td><td className="sales-description">{sale.description || "-"}</td><td>{formatDate(sale.created_at)}</td><td>{sale.created_by || "-"}</td>
                <td className="lead-actions"><button className="table-action" type="button" onClick={() => openEdit(sale)}>Edit</button><button className="table-action table-action-danger" type="button" onClick={() => deleteSale(sale)}>Delete</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {isFormOpen && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setIsFormOpen(false); }}>
        <form className="edit-modal sales-form" onSubmit={saveSale}>
          <div className="modal-heading"><div><p className="eyebrow">Revenue workspace</p><h2>{editingSaleId ? "Edit sale" : "Add sale"}</h2></div><span className="read-only-id">UI preview</span></div>
          <div className="edit-grid">
            <label>Product<input value={form.product_id} placeholder="Product ID" onChange={(event) => updateField("product_id", event.target.value)} /></label>
            <label>Lead<input value={form.lead_id} placeholder="Lead ID" onChange={(event) => updateField("lead_id", event.target.value)} /></label>
            <label>Invoice ID<input value={form.invoice_id} onChange={(event) => updateField("invoice_id", event.target.value)} /></label>
            <label>Sale Price<input type="number" min="0" step="0.01" value={form.sale_price} onChange={(event) => updateField("sale_price", event.target.value)} /></label>
            <label>Sale Paid<input type="number" min="0" step="0.01" value={form.sale_paid} onChange={(event) => updateField("sale_paid", event.target.value)} /></label>
            <label>Sale Due<input type="number" min="0" step="0.01" value={form.sale_due} onChange={(event) => updateField("sale_due", event.target.value)} /></label>
            <label>Sale Tax<input type="number" min="0" step="0.01" value={form.sale_tax} onChange={(event) => updateField("sale_tax", event.target.value)} /></label>
            <label>Sale Status<select value={form.sale_status} onChange={(event) => updateField("sale_status", event.target.value)}>{saleStatuses.map((status) => <option key={status.value} value={status.value}>{status.label}</option>)}</select></label>
            <label>Payment Status<select value={form.payment_status} onChange={(event) => updateField("payment_status", event.target.value)}>{paymentStatuses.map((status) => <option key={status.value} value={status.value}>{status.label}</option>)}</select></label>
            <label>Payment Method<input value={form.payment_method} placeholder="Card, cash, transfer..." onChange={(event) => updateField("payment_method", event.target.value)} /></label>
            <label className="edit-message">Description<textarea value={form.description} placeholder="Add a short description" onChange={(event) => updateField("description", event.target.value)} /></label>
          </div>
          <div className="modal-actions"><button className="modal-cancel" type="button" onClick={() => setIsFormOpen(false)}>Cancel</button><button className="submit-button" type="submit">{editingSaleId ? "Save changes" : "Add Sale"}</button></div>
        </form>
      </div>}
    </section>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8001";

type SalesPerson = {
  user_id: number;
  first_name: string;
  last_name: string | null;
  email: string;
  phone: string | null;
  status: number;
};

type SalesPersonsResponse = {
  sales_persons: SalesPerson[];
  current_page: number;
  page_size: number;
  total_count: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
};

export default function AdminSalesPersons() {
  const router = useRouter();
  const [salesPersons, setSalesPersons] = useState<SalesPerson[] | null>(null);
  const [result, setResult] = useState<SalesPersonsResponse | null>(null);
  const [page, setPage] = useState(1);
  const [error, setError] = useState("");

  async function deleteSalesPerson(salesPerson: SalesPerson) {
    if (!window.confirm(`Delete ${salesPerson.first_name} ${salesPerson.last_name || "this sales person"}?`)) return;
    const response = await fetch(`${apiUrl}/admin/sales-persons/${salesPerson.user_id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${sessionStorage.getItem("access_token")}` },
    });
    if (response.status === 401) {
      sessionStorage.removeItem("access_token");
      router.replace("/");
      return;
    }
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      setError(body.detail || "The sales person could not be deleted. Please try again.");
      return;
    }
    setSalesPersons((current) => current?.filter((item) => item.user_id !== salesPerson.user_id) ?? []);
  }

  useEffect(() => {
    const token = sessionStorage.getItem("access_token");
    if (!token) {
      router.replace("/");
      return;
    }

    fetch(`${apiUrl}/admin/sales-persons?page=${page}&page_size=50`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (response) => {
        if (response.status === 401) {
          sessionStorage.removeItem("access_token");
          router.replace("/");
          return;
        }
        if (!response.ok) throw new Error("Unable to load sales persons");
        const responseBody: SalesPersonsResponse = await response.json();
        setResult(responseBody);
        setSalesPersons(responseBody.sales_persons);
      })
      .catch(() => setError("The sales persons could not be loaded. Please try again."));
  }, [page, router]);

  if (salesPersons === null && !error) {
    return <main className="loading-screen">Loading sales persons...</main>;
  }

  return (
    <section className="leads-content">
        <div className="leads-header">
          <div>
            <p className="eyebrow">Admin workspace</p>
            <h1>Sales Persons</h1>
          </div>
          <Link className="submit-button add-customer-button" href="/admin/sales-persons/new">+ Add Sales Person</Link>
        </div>
        {error && <p className="form-error" role="alert">{error}</p>}
        <div className="leads-table-wrap">
          <table className="leads-table sales-persons-table">
            <thead>
              <tr>
                <th>USER ID</th>
                <th>FIRST NAME</th>
                <th>LAST NAME</th>
                <th>EMAIL</th>
                <th>PHONE</th>
                <th>STATUS</th>
                <th>ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {salesPersons?.length === 0 ? (
                <tr><td colSpan={7}>No sales persons available</td></tr>
              ) : salesPersons?.map((salesPerson) => (
                <tr key={salesPerson.user_id}>
                  <td>{salesPerson.user_id}</td>
                  <td>{salesPerson.first_name}</td>
                  <td>{salesPerson.last_name || "-"}</td>
                  <td>{salesPerson.email}</td>
                  <td>{salesPerson.phone || "-"}</td>
                  <td><span className={`customer-status customer-status-${salesPerson.status}`}>{salesPerson.status === 1 ? "ACTIVE" : "INACTIVE"}</span></td>
                  <td className="lead-actions"><Link className="table-action" href={`/admin/sales-persons/${salesPerson.user_id}/edit`}>Edit</Link><button className="table-action table-action-danger" type="button" onClick={() => deleteSalesPerson(salesPerson)}>Delete</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="pagination" aria-label="Sales Person pagination">
          <span>{result && result.total_count > 0 ? (result.current_page - 1) * result.page_size + 1 : 0}-{result ? Math.min(result.current_page * result.page_size, result.total_count) : 0} of {result?.total_count ?? 0}</span>
          <div className="pagination-controls">
            <button type="button" disabled={!result?.has_previous} onClick={() => setPage((current) => current - 1)}>Previous</button>
            <span>Page {result?.current_page ?? page}</span>
            <button type="button" disabled={!result?.has_next} onClick={() => setPage((current) => current + 1)}>Next</button>
          </div>
        </div>
      </section>
  );
}

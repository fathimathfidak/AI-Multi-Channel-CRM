"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8001";

function NavIcon({ name }: { name: "grid" | "leads" | "people" | "sales" | "payments" | "products" | "reports" | "settings" }) {
  if (name === "grid") return <svg aria-hidden="true" viewBox="0 0 24 24"><rect x="4" y="4" width="6" height="6" rx="1" /><rect x="14" y="4" width="6" height="6" rx="1" /><rect x="4" y="14" width="6" height="6" rx="1" /><rect x="14" y="14" width="6" height="6" rx="1" /></svg>;
  if (name === "leads") return <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M5 5h14v14H5z" /><path d="M8 9h8M8 13h5M8 17h3" /></svg>;
  if (name === "people") return <svg aria-hidden="true" viewBox="0 0 24 24"><circle cx="9" cy="8" r="3" /><path d="M3.5 19c.5-3 2.2-4.5 5.5-4.5s5 1.5 5.5 4.5M16 6.5a2.5 2.5 0 0 1 0 5M16 14.5c2.7.2 4.1 1.7 4.5 4.5" /></svg>;
  if (name === "sales") return <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M5 19V9M12 19V5M19 19v-7" /><path d="M3 19h18" /></svg>;
  if (name === "payments") return <svg aria-hidden="true" viewBox="0 0 24 24"><rect x="3" y="6" width="18" height="12" rx="2" /><path d="M3 10h18M7 14h3" /></svg>;
  if (name === "products") return <svg aria-hidden="true" viewBox="0 0 24 24"><path d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Z" /><path d="m4 7.5 8 4.5 8-4.5M12 12v9" /></svg>;
  if (name === "reports") return <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M5 20V10M12 20V4M19 20v-7" /><path d="M3 20h18" /></svg>;
  return <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M12 4.5a2 2 0 0 1 2 2v.3a5.8 5.8 0 0 1 1.8 1l.3-.2a2 2 0 1 1 2 3.5l-.3.2a6 6 0 0 1 0 2.1l.3.2a2 2 0 1 1-2 3.5l-.3-.2a5.8 5.8 0 0 1-1.8 1v.3a2 2 0 1 1-4 0v-.3a5.8 5.8 0 0 1-1.8-1l-.3.2a2 2 0 1 1-2-3.5l.3-.2a6 6 0 0 1 0-2.1l-.3-.2a2 2 0 1 1 2-3.5l.3.2a5.8 5.8 0 0 1 1.8-1v-.3a2 2 0 0 1 2-2Z" /><circle cx="12" cy="12" r="2.2" /></svg>;
}

export default function AdminLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const pathname = usePathname();
  const router = useRouter();
  const [checking, setChecking] = useState(true);
  const [authorized, setAuthorized] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const settingsActive = pathname.startsWith("/admin/settings");

  useEffect(() => {
    const token = sessionStorage.getItem("access_token");
    if (!token) {
      router.replace("/");
      return;
    }
    fetch(`${apiUrl}/admin/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((response) => {
        if (!response.ok) throw new Error("Unauthorized");
        setAuthorized(true);
      })
      .catch(() => {
        sessionStorage.removeItem("access_token");
        router.replace("/");
      })
      .finally(() => setChecking(false));
  }, [router]);

  useEffect(() => {
    setSettingsOpen(settingsActive);
  }, [settingsActive]);

  function signOut() {
    sessionStorage.removeItem("access_token");
    setAuthorized(false);
    router.replace("/");
  }

  if (checking || !authorized) return <main className="loading-screen">Checking access...</main>;

  return (
    <main className="admin-shell">
      <aside className="sidebar">
        <div className="admin-brand">
          <div className="brand-mark" aria-hidden="true"><span /><span /><span /></div>
          <div><strong>AI Multi-Channel</strong><span>CRM workspace</span></div>
        </div>
        <nav aria-label="Admin navigation">
          <p className="nav-label">Workspace</p>
          <a className={pathname === "/admin/dashboard" ? "nav-active" : undefined} href="/admin/dashboard"><NavIcon name="grid" /><span>Dashboard</span></a>
          <a className={pathname === "/admin/leads" ? "nav-active" : undefined} href="/admin/leads"><NavIcon name="leads" /><span>Leads</span></a>
          <a className={pathname === "/admin/sales-persons" ? "nav-active" : undefined} href="/admin/sales-persons"><NavIcon name="people" /><span>Sales Persons</span></a>
          <a className={pathname === "/admin/sales" ? "nav-active" : undefined} href="/admin/sales"><NavIcon name="sales" /><span>Sales</span></a>
          <a className={pathname === "/admin/payments" ? "nav-active" : undefined} href="/admin/payments"><NavIcon name="payments" /><span>Payments</span></a>
          <a className={pathname === "/admin/products" ? "nav-active" : undefined} href="/admin/products"><NavIcon name="products" /><span>Products</span></a>
          <a className={pathname === "/admin/company-reports" ? "nav-active" : undefined} href="/admin/company-reports"><NavIcon name="reports" /><span>Company Reports</span></a>
          <a
            className={settingsActive ? "nav-active" : undefined}
            href="/admin/settings"
            aria-expanded={settingsOpen}
            onClick={() => setSettingsOpen(true)}
          >
            <NavIcon name="settings" /><span>Settings</span>
          </a>
          {settingsOpen && (
            <div className="settings-nav-submenu">
              <a className={pathname === "/admin/settings" ? "nav-active" : undefined} href="/admin/settings"><span>Profile</span></a>
              <a className={pathname === "/admin/settings/change-password" ? "nav-active" : undefined} href="/admin/settings/change-password"><span>Change Password</span></a>
            </div>
          )}
          <button className="sidebar-logout" type="button" onClick={signOut}><span>Logout</span></button>
        </nav>
        <div className="admin-profile" style={{ marginTop: "auto" }}>
          <span className="profile-avatar">A</span>
          <div>
            <strong>Admin workspace</strong>
            <span>Administrator</span>
          </div>
        </div>
      </aside>
      <div className="admin-main-content">{children}</div>
    </main>
  );
}

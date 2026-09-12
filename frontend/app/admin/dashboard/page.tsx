"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8001";

type User = {
  first_name: string;
  last_name?: string | null;
  email: string;
};

export default function AdminDashboard() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const token = sessionStorage.getItem("access_token");
    if (!token) {
      router.replace("/");
      return;
    }
    fetch(`${apiUrl}/admin/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (response) => {
        if (!response.ok) throw new Error("Unauthorized");
        const result = await response.json();
        setUser(result.user);
      })
      .catch(() => {
        sessionStorage.removeItem("access_token");
        router.replace("/");
      })
      .finally(() => setChecking(false));
  }, [router]);

  if (checking || !user) return <main className="loading-screen">Checking access...</main>;

  return (
    <section className="dashboard-content">
        <p className="eyebrow">Overview</p>
        <h1>Good to see you, {user.first_name}.</h1>
        <p className="intro">Your administrative workspace is ready for the next CRM module.</p>
        <div className="dashboard-grid">
          <article><span>Workspace</span><strong>Admin dashboard</strong></article>
          <article><span>Signed in as</span><strong>{user.email}</strong></article>
          <article><span>Lead pipeline</span><strong>Preparing</strong></article>
        </div>
    </section>
  );
}
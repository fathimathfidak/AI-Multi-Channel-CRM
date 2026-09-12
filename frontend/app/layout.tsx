import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Multi-Channel CRM",
  description: "Sign in to your account",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
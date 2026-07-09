import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ICU Smart Monitoring",
  description: "Plateforme IA de surveillance intelligente pour unités de réanimation",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body className="bg-bg-primary text-txt antialiased">{children}</body>
    </html>
  );
}

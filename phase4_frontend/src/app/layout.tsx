import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Groww AI Fact Engine",
  description: "Factual RAG for Groww Mutual Funds built with Next.js and FastAPI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}

import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ArcheCode - AI Code Archaeology Platform",
  description:
    "Understand any codebase in 10 minutes. AI-powered code analysis, architecture visualization, and documentation generation.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background font-sans antialiased">
        {children}
      </body>
    </html>
  );
}

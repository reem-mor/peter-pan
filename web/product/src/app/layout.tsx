import type { Metadata } from "next";
import { IBM_Plex_Mono, Source_Sans_3 } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const sans = Source_Sans_3({
  variable: "--font-sans",
  subsets: ["latin"],
});

const mono = IBM_Plex_Mono({
  variable: "--font-mono",
  weight: ["400", "600"],
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "PETER PAN — From Alert to Insight, Faster",
  description:
    "AI observability intelligence: alert enrichment, prediction, retrieval, incident stories, and PETER PAN OS.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${sans.variable} ${mono.variable} min-h-screen bg-slate-950 text-slate-100 antialiased`}>
        <header className="border-b border-slate-800 bg-slate-950/90">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
            <Link href="/" className="font-[family-name:var(--font-mono)] text-sm font-semibold tracking-[0.18em] uppercase">
              PETER PAN
            </Link>
            <nav className="flex gap-6 font-[family-name:var(--font-mono)] text-xs tracking-wide uppercase text-slate-400">
              <Link href="/app" className="hover:text-teal-300">
                App
              </Link>
              <Link href="/os" className="hover:text-teal-300">
                OS
              </Link>
            </nav>
          </div>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}

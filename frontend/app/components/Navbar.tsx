"use client";

import Image from "next/image";
import Link from "next/link";
import { Menu, X } from "lucide-react";
import { useState } from "react";
import ThemeToggle from "@/components/theme-toggle";

const navItems = [
  { href: "#features", label: "Features" },
  { href: "#about", label: "About" },
  { href: "#how-it-works", label: "How It Works" }
];

export default function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <nav className="fixed inset-x-0 top-0 z-50 px-4 pt-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl rounded-2xl border border-zinc-300/80 bg-white/80 px-4 shadow-[0_14px_36px_rgba(0,0,0,0.08)] backdrop-blur-xl dark:border-zinc-700 dark:bg-zinc-900/80">
        <div className="flex h-16 items-center justify-between">
          <Link href="/" className="flex items-center gap-3">
            <span className="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-zinc-200 bg-white p-1 shadow-sm dark:border-zinc-700 dark:bg-zinc-100">
              <Image
                src="/LOGO.png"
                alt="RAG AI logo"
                width={28}
                height={28}
                className="h-7 w-7 object-contain"
              />
            </span>

            <span className="leading-tight">
              <span className="block text-sm font-semibold tracking-[0.14em] text-zinc-900 dark:text-zinc-100">
                RAG AI
              </span>
              <span className="block text-[10px] font-medium uppercase tracking-[0.16em] text-zinc-500 dark:text-zinc-400">
                Smart PDF Intelligence
              </span>
            </span>
          </Link>

          <div className="hidden items-center gap-8 md:flex">
            {navItems.map(({ href, label }) => (
              <a
                key={href}
                href={href}
                className="text-sm font-medium text-zinc-600 transition-colors hover:text-zinc-950 dark:text-zinc-300 dark:hover:text-zinc-100"
              >
                {label}
              </a>
            ))}
          </div>

          <div className="hidden items-center gap-3 md:flex">
            <ThemeToggle />
            <Link
              href="/login"
              className="rounded-lg px-4 py-2 text-sm font-medium text-zinc-700 transition-colors hover:text-zinc-950 dark:text-zinc-300 dark:hover:text-zinc-100"
            >
              Log in
            </Link>
            <Link
              href="/login"
              className="inline-flex items-center justify-center rounded-lg bg-linear-to-b from-white via-white/95 to-white/70 px-5 py-2.5 text-sm font-semibold text-zinc-950 shadow-[0_12px_25px_rgba(0,0,0,0.08)] transition-transform hover:-translate-y-0.5 dark:from-zinc-100 dark:via-zinc-50 dark:to-zinc-200"
            >
              Get Started
            </Link>
          </div>

          <div className="flex items-center gap-2 md:hidden">
            <ThemeToggle />
            <button
              type="button"
              className="rounded-lg p-2 text-zinc-600 transition-colors hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {mobileMenuOpen && (
          <div className="space-y-3 border-t border-zinc-200 py-4 dark:border-zinc-800 md:hidden">
            {navItems.map(({ href, label }) => (
              <a
                key={href}
                href={href}
                className="block rounded-md px-2 py-1.5 text-sm font-medium text-zinc-600 transition-colors hover:bg-zinc-100 hover:text-zinc-950 dark:text-zinc-300 dark:hover:bg-zinc-800 dark:hover:text-zinc-100"
              >
                {label}
              </a>
            ))}

            <div className="flex flex-col gap-2 border-t border-zinc-200 pt-3 dark:border-zinc-800">
              <Link href="/login" className="rounded-md px-2 py-1.5 text-sm font-medium text-zinc-700 dark:text-zinc-300">
                Log in
              </Link>
              <Link
                href="/login"
                className="rounded-lg bg-linear-to-b from-white via-white/95 to-white/70 px-4 py-2.5 text-center text-sm font-semibold text-zinc-950 shadow-[0_10px_22px_rgba(0,0,0,0.08)] dark:from-zinc-100 dark:via-zinc-50 dark:to-zinc-200"
              >
                Get Started
              </Link>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}

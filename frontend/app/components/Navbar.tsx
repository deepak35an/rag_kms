"use client";

import Link from "next/link";
import { useState } from "react";

export default function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-linear-to-br from-blue-600 to-indigo-700 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">R</span>
            </div>
            <span className="text-xl font-bold text-gray-900">
              RAG<span className="text-blue-600">4</span>GOV
            </span>
          </Link>

          {/* Desktop Nav Links */}
          <div className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
              Features
            </a>
            <a href="#about" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
              About
            </a>
            <a href="#how-it-works" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
              How It Works
            </a>
          </div>

          {/* Auth Buttons */}
          <div className="hidden md:flex items-center gap-3">
            <Link
              href="/login"
              className="text-sm font-medium text-gray-700 hover:text-gray-900 px-4 py-2 transition-colors"
            >
              Log in
            </Link>
            <Link
              href="/login"
              className="text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 px-5 py-2.5 rounded-lg transition-colors shadow-sm"
            >
              Get Started
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {mobileMenuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-gray-100 py-4 space-y-3">
            <a href="#features" className="block text-sm font-medium text-gray-600 hover:text-gray-900 px-2 py-1.5">
              Features
            </a>
            <a href="#about" className="block text-sm font-medium text-gray-600 hover:text-gray-900 px-2 py-1.5">
              About
            </a>
            <a href="#how-it-works" className="block text-sm font-medium text-gray-600 hover:text-gray-900 px-2 py-1.5">
              How It Works
            </a>
            <div className="pt-3 border-t border-gray-100 flex flex-col gap-2">
              <Link href="/login" className="text-sm font-medium text-gray-700 px-2 py-1.5">
                Log in
              </Link>
              <Link
                href="/login"
                className="text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 px-4 py-2.5 rounded-lg text-center"
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

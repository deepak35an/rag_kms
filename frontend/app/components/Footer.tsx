import Image from "next/image";
import Link from "next/link";

export default function Footer() {
  return (
    <footer className="bg-white text-gray-500 py-16 px-4 sm:px-6 lg:px-8 border-t border-gray-200 dark:bg-zinc-950 dark:text-zinc-400 dark:border-zinc-800">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 mb-12">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-zinc-200 bg-white p-1 shadow-sm dark:border-zinc-700 dark:bg-zinc-100">
                <Image
                  src="/LOGO.png"
                  alt="lafleur IQ logo"
                  width={24}
                  height={24}
                  className="h-6 w-6 object-contain"
                />
              </div>
              <span className="text-xl font-bold text-gray-900 dark:text-white">
                lafleur <span className="text-blue-400">IQ</span>
              </span>
            </div>
            <p className="text-sm leading-relaxed">
              AI-powered document intelligence — ask questions, get cited answers from any knowledge base.
            </p>
          </div>

          {/* Navigation */}
          <div>
            <h4 className="text-gray-900 dark:text-white font-semibold mb-4 text-sm uppercase tracking-wide">
              Navigation
            </h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="#features" className="hover:text-gray-900 dark:hover:text-white transition-colors">
                  Features
                </a>
              </li>
              <li>
                <a href="#about" className="hover:text-gray-900 dark:hover:text-white transition-colors">
                  About
                </a>
              </li>
              <li>
                <a href="#how-it-works" className="hover:text-gray-900 dark:hover:text-white transition-colors">
                  How It Works
                </a>
              </li>
              <li>
                <Link href="/login" className="hover:text-gray-900 dark:hover:text-white transition-colors">
                  Login
                </Link>
              </li>
            </ul>
          </div>

          {/* Tech Stack */}
          <div>
            <h4 className="text-gray-900 dark:text-white font-semibold mb-4 text-sm uppercase tracking-wide">
              Built With
            </h4>
            <ul className="space-y-2 text-sm">
              <li>Next.js + TypeScript</li>
              <li>FastAPI + Uvicorn</li>
              <li>Qdrant Vector Store</li>
              <li>Ollama (Local LLM)</li>
              <li>Sentence Transformers</li>
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="border-t border-gray-200 dark:border-zinc-800 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-sm">
            &copy; {new Date().getFullYear()} lafleur IQ. All rights reserved.
          </p>
          <p className="text-sm">
            Built for intelligent document search & answers.
          </p>
        </div>
      </div>
    </footer>
  );
}

export default function About() {
  return (
    <section id="about" className="py-24 px-4 sm:px-6 lg:px-8 bg-white">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          {/* Left: Text Content */}
          <div>
            <p className="text-sm font-semibold text-blue-600 uppercase tracking-wide mb-3">
              About
            </p>
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 leading-tight">
              Built for Intelligent Document Q&A
            </h2>
            <p className="mt-5 text-lg text-gray-600 leading-relaxed">
              ContextIQ is an AI system designed to make dense documents —
              brochures, guides, manuals, reports — instantly searchable and
              understandable through natural conversation.
            </p>
            <p className="mt-4 text-gray-600 leading-relaxed">
              Instead of manually scanning pages, simply ask a question. The system 
              retrieves the most relevant sections from your document library and 
              generates a concise, accurate answer — complete with source citations.
            </p>

            {/* Highlights */}
            <ul className="mt-8 space-y-4">
              {[
                "No hallucinations — every answer is grounded in real document content",
                "Works with PDFs, Markdown, and scanned documents via OCR",
                "Fully local — your documents never leave your server",
              ].map((point, i) => (
                <li key={i} className="flex items-start gap-3">
                  <span className="mt-1 shrink-0 w-5 h-5 bg-blue-100 rounded-full flex items-center justify-center">
                    <svg className="w-3 h-3 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M16.707 5.293a1 1 0 00-1.414 0L8 12.586l-3.293-3.293a1 1 0 00-1.414 1.414l4 4a1 1 0 001.414 0l8-8a1 1 0 000-1.414z" />
                    </svg>
                  </span>
                  <span className="text-gray-700">{point}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Right: Visual Card */}
          <div className="relative">
            <div className="bg-gray-50 border border-gray-200 rounded-2xl p-8 space-y-4">
              {/* Mock chat bubble */}
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center shrink-0 text-xs font-bold text-gray-500">
                  U
                </div>
                <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-none px-4 py-3 text-sm text-gray-700 shadow-sm">
                  What are the participating institutes in JAC 2025?
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center shrink-0 text-xs font-bold text-white">
                  AI
                </div>
                <div className="bg-blue-50 border border-blue-100 rounded-2xl rounded-tl-none px-4 py-3 text-sm text-gray-700 shadow-sm">
                  JAC Chandigarh 2025 includes <span className="font-semibold text-blue-700">PEC, UIET, CCET</span> and several other institutes across Chandigarh and Punjab...
                  <div className="mt-3 flex flex-wrap gap-2">
                    <span className="text-xs bg-white border border-blue-200 text-blue-600 rounded-full px-3 py-1 font-medium">
                      jac_brochure_2025 (p.3)
                    </span>
                    <span className="text-xs bg-white border border-blue-200 text-blue-600 rounded-full px-3 py-1 font-medium">
                      jac_brochure_2025 (p.7)
                    </span>
                  </div>
                </div>
              </div>

              {/* Typing indicator */}
              <div className="flex items-center gap-2 pl-11">
                <span className="text-xs text-gray-400">Sources retrieved from 12 document chunks</span>
              </div>
            </div>

            {/* Decorative blob */}
            <div className="absolute -bottom-6 -right-6 -z-10 w-48 h-48 bg-indigo-50 rounded-full blur-2xl" />
          </div>
        </div>
      </div>
    </section>
  );
}

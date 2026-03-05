import Link from "next/link";

export default function Hero() {
  return (
    <section className="relative pt-32 pb-20 px-4 sm:px-6 lg:px-8 overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-20 left-1/2 -translate-x-1/2 w-200 h-200 bg-blue-50 rounded-full blur-3xl opacity-60" />
        <div className="absolute top-40 right-0 w-100 h-100 bg-indigo-50 rounded-full blur-3xl opacity-40" />
      </div>

      <div className="max-w-7xl mx-auto text-center">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 bg-blue-50 border border-blue-100 rounded-full px-4 py-1.5 mb-8">
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span className="text-sm font-medium text-blue-700">AI-Powered Document Intelligence</span>
        </div>

        {/* Main Heading */}
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 leading-tight tracking-tight max-w-4xl mx-auto">
          Get Instant Answers from{" "}
          <span className="text-transparent bg-clip-text bg-linear-to-r from-blue-600 to-indigo-600">
            Government Documents
          </span>
        </h1>

        {/* Subtitle */}
        <p className="mt-6 text-lg sm:text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
          RAG4GOV uses advanced Retrieval-Augmented Generation to search, retrieve, and 
          answer questions from official documents — accurately and instantly.
        </p>

        {/* CTA Buttons */}
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="/login"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-3.5 rounded-xl transition-all shadow-lg shadow-blue-600/25 hover:shadow-xl hover:shadow-blue-600/30"
          >
            Start Asking Questions
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </Link>
          <a
            href="#how-it-works"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-white hover:bg-gray-50 text-gray-700 font-semibold px-8 py-3.5 rounded-xl border border-gray-200 transition-all"
          >
            See How It Works
          </a>
        </div>

        {/* Stats */}
        <div className="mt-16 grid grid-cols-3 gap-8 max-w-lg mx-auto">
          <div>
            <div className="text-2xl sm:text-3xl font-bold text-gray-900">Fast</div>
            <div className="text-sm text-gray-500 mt-1">Retrieval</div>
          </div>
          <div>
            <div className="text-2xl sm:text-3xl font-bold text-gray-900">Accurate</div>
            <div className="text-sm text-gray-500 mt-1">Answers</div>
          </div>
          <div>
            <div className="text-2xl sm:text-3xl font-bold text-gray-900">Cited</div>
            <div className="text-sm text-gray-500 mt-1">Sources</div>
          </div>
        </div>
      </div>
    </section>
  );
}

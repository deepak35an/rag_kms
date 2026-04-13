const steps = [
  {
    number: "01",
    title: "Upload Your Documents",
    description:
      "Add PDFs, Markdown files, or scanned documents to the backend. The system processes and chunks them automatically.",
  },
  {
    number: "02",
    title: "Ask a Question",
    description:
      "Type any question in plain English. No need to know which document contains the answer.",
  },
  {
    number: "03",
    title: "Hybrid Retrieval",
    description:
      "The system runs both vector similarity search and BM25 keyword search to find the most relevant chunks.",
  },
  {
    number: "04",
    title: "AI Generates the Answer",
    description:
      "A local LLM reads the retrieved chunks and generates a concise, accurate answer grounded in your documents.",
  },
  {
    number: "05",
    title: "Get Cited Results",
    description:
      "Every answer includes source citations — document name and page number — so you can verify and trust the response.",
  },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="py-24 px-4 sm:px-6 lg:px-8 bg-gray-50 dark:bg-zinc-950">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="text-center max-w-2xl mx-auto mb-16">
          <p className="text-sm font-semibold text-blue-600 uppercase tracking-wide mb-3">
            How It Works
          </p>
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900">
            From question to cited answer in seconds
          </h2>
          <p className="mt-4 text-lg text-gray-600">
            A five-step pipeline that turns your document library into an intelligent knowledge base.
          </p>
        </div>

        {/* Steps */}
        <div className="relative">
          {/* Vertical line connector (desktop) */}
          <div className="hidden lg:block absolute left-1/2 -translate-x-1/2 top-0 bottom-0 w-px bg-gray-200" />

          <div className="space-y-12">
            {steps.map((step, index) => {
              const isEven = index % 2 === 0;
              return (
                <div
                  key={step.number}
                  className={`relative flex flex-col lg:flex-row items-center gap-8 ${
                    isEven ? "lg:flex-row" : "lg:flex-row-reverse"
                  }`}
                >
                  {/* Text Card */}
                  <div className="w-full lg:w-5/12">
                    <div className="bg-white border border-gray-100 rounded-2xl p-8 shadow-sm hover:shadow-md transition-shadow dark:bg-zinc-900 dark:border-zinc-800">
                      <span className="text-4xl font-black text-blue-100 select-none">
                        {step.number}
                      </span>
                      <h3 className="mt-2 text-xl font-semibold text-gray-900">
                        {step.title}
                      </h3>
                      <p className="mt-2 text-gray-600 leading-relaxed">
                        {step.description}
                      </p>
                    </div>
                  </div>

                  {/* Center dot (desktop) */}
                  <div className="hidden lg:flex w-2/12 justify-center">
                    <div className="w-5 h-5 rounded-full bg-blue-600 border-4 border-white shadow-md z-10" />
                  </div>

                  {/* Spacer for alternating layout */}
                  <div className="hidden lg:block w-5/12" />
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}

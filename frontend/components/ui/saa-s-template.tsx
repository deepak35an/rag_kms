import Link from "next/link";
import { ArrowRight, Database, FileSearch, MessageSquareQuote, Sparkles } from "lucide-react";
import CardSwap, { Card } from "@/components/CardSwap";

const ragCards = [
  {
    icon: FileSearch,
    title: "Hybrid Retrieval",
    description:
      "Blend semantic and keyword search to surface the strongest evidence chunks.",
    tag: "Retrieve"
  },
  {
    icon: Database,
    title: "Grounded Context",
    description:
      "Answers are built from your documents, reducing hallucinations and boosting trust.",
    tag: "Ground"
  },
  {
    icon: MessageSquareQuote,
    title: "Polished Generation",
    description:
      "Turn retrieved passages into concise responses with clear citations and confidence.",
    tag: "Generate"
  }
];

export default function SaaSTemplateHero() {
  return (
    <section className="relative min-h-screen overflow-hidden px-4 pb-20 pt-28 sm:px-6 lg:px-8 lg:pt-36">
      <div className="absolute inset-0 -z-30 bg-[radial-gradient(circle_at_center,#f6f6f6_0%,#ececec_100%)] dark:bg-[radial-gradient(circle_at_center,#0f0f12_0%,#060608_100%)]" />
      <div className="absolute inset-0 -z-20 bg-[linear-gradient(transparent_0,rgba(0,0,0,0.02)_100%)] dark:bg-[linear-gradient(transparent_0,rgba(255,255,255,0.03)_100%)]" />
      <div className="absolute inset-0 -z-10 opacity-50 bg-[radial-gradient(circle_at_15%_20%,rgba(183,154,82,0.18),transparent_38%),radial-gradient(circle_at_85%_16%,rgba(183,154,82,0.12),transparent_30%)] dark:opacity-70" />

      <div className="mx-auto flex max-w-6xl flex-col items-center text-center">
        <aside className="mb-8 inline-flex flex-wrap items-center justify-center gap-2 rounded-full border border-zinc-300/80 bg-white/80 px-4 py-2 text-xs font-medium text-zinc-600 shadow-sm backdrop-blur dark:border-zinc-700 dark:bg-zinc-900/70 dark:text-zinc-300">
          <Sparkles className="h-3.5 w-3.5 text-[#b79a52]" />
          SaaS template styling adapted for lafleur IQ
        </aside>

        <h1 className="max-w-4xl px-4 text-4xl font-semibold leading-tight tracking-tight sm:text-5xl lg:text-6xl">
          <span className="bg-linear-to-b from-zinc-950 via-zinc-800 to-zinc-500 bg-clip-text text-transparent dark:from-white dark:via-zinc-100 dark:to-zinc-500">
            Give your knowledge base
          </span>
          <br />
          <span className="bg-linear-to-r from-[#b79a52] via-[#c6ac69] to-[#e0cd95] bg-clip-text text-transparent">
            the premium RAG interface it deserves
          </span>
        </h1>

        <p className="mt-6 max-w-3xl px-4 text-base leading-7 text-zinc-600 sm:text-lg dark:text-zinc-300">
          lafleur IQ combines retrieval, reranking, and generation to deliver fast,
          cited answers from your documents — built to feel like a polished SaaS product
          from first interaction.
        </p>

        <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row">
          <Link
            href="/login"
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-linear-to-b from-white via-white/95 to-white/70 px-6 py-3 text-sm font-semibold text-zinc-950 shadow-[0_12px_30px_rgba(0,0,0,0.08)] transition-transform hover:-translate-y-0.5 dark:from-zinc-100 dark:via-zinc-50 dark:to-zinc-200"
          >
            Get started
            <ArrowRight className="h-4 w-4" />
          </Link>

          <a
            href="#how-it-works"
            className="inline-flex items-center justify-center rounded-lg border border-zinc-300/80 bg-white/70 px-6 py-3 text-sm font-semibold text-zinc-700 transition-colors hover:bg-white dark:border-zinc-700 dark:bg-zinc-900/65 dark:text-zinc-200 dark:hover:bg-zinc-900"
          >
            Explore pipeline
          </a>
        </div>

        <div className="relative mt-14 w-full max-w-6xl rounded-2xl border border-zinc-300/80 bg-white/65 p-4 shadow-[0_30px_80px_rgba(0,0,0,0.12)] backdrop-blur-xl dark:border-zinc-700 dark:bg-zinc-900/65 sm:p-6">
          <div className="pointer-events-none absolute inset-x-6 top-0 h-px bg-linear-to-r from-transparent via-[#c6ac69] to-transparent" />

          <div className="mb-4 flex items-center justify-between px-2 text-xs uppercase tracking-[0.2em] text-zinc-500 dark:text-zinc-400">
            <span>RAG runtime preview</span>
            <span className="rounded-full border border-zinc-300 px-2 py-1 text-[10px] tracking-[0.16em] dark:border-zinc-700">
              Live cards
            </span>
          </div>

          <div className="relative min-h-130 overflow-visible sm:min-h-140">
            <CardSwap
              width={520}
              height={390}
              delay={4300}
              pauseOnHover
              skewAmount={4}
              cardDistance={56}
              verticalDistance={62}
              easing="elastic"
            >
              {ragCards.map((item, index) => {
                const Icon = item.icon;

                return (
                  <Card
                    key={item.title}
                    customClass="flex h-full w-full flex-col justify-between bg-white/95 p-6 text-left ring-1 ring-zinc-200/80 dark:bg-zinc-900/95 dark:ring-zinc-700/80"
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="rounded-full bg-zinc-100 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-zinc-500 dark:bg-zinc-800 dark:text-zinc-300">
                          0{index + 1}
                        </span>
                        <Icon className="h-5 w-5 text-[#b79a52]" />
                      </div>

                      <p className="mt-4 text-xs font-semibold uppercase tracking-[0.24em] text-[#b79a52]">
                        {item.tag}
                      </p>
                      <h3 className="mt-3 text-2xl font-semibold text-zinc-950 dark:text-zinc-100">
                        {item.title}
                      </h3>
                      <p className="mt-3 text-sm leading-6 text-zinc-600 dark:text-zinc-300">
                        {item.description}
                      </p>
                    </div>

                    <div className="mt-7 rounded-2xl bg-zinc-100 p-4 dark:bg-zinc-800/80">
                      <p className="text-xs font-medium uppercase tracking-[0.2em] text-zinc-400">Signal</p>
                      <p className="mt-2 text-base font-semibold text-zinc-700 dark:text-zinc-200">
                        {index === 0
                          ? "Top chunks ranked"
                          : index === 1
                          ? "Evidence grounded"
                          : "Answer generated"}
                      </p>
                    </div>
                  </Card>
                );
              })}
            </CardSwap>
          </div>
        </div>
      </div>
    </section>
  );
}
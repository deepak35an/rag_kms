import Link from "next/link";
import { ArrowLeft, BadgeCheck, Sparkles } from "lucide-react";
import CardSwap, { Card } from "@/components/CardSwap";
import ThemeToggle from "@/components/theme-toggle";

const cards = [
  {
    title: "Instant retrieval",
    description: "Surface the right context from your knowledge base in seconds.",
    stat: "98%",
    detail: "of searches stay within the top 3 sources"
  },
  {
    title: "Cited answers",
    description: "Every response stays grounded with direct source references.",
    stat: "100%",
    detail: "answer traceability for audit-friendly workflows"
  },
  {
    title: "Hybrid search",
    description: "Blend semantic and keyword retrieval for stronger recall.",
    stat: "2x",
    detail: "better relevance on messy document sets"
  },
  {
    title: "Fast iteration",
    description: "Test prompts and retrieval settings without leaving the page.",
    stat: "Live",
    detail: "tuning for product and operations teams"
  }
];

export default function OkPage() {
  return (
    <main className="min-h-screen overflow-hidden bg-[radial-gradient(circle_at_top,#eff6ff_0%,#ffffff_42%,#f8fafc_100%)] text-slate-900 dark:bg-[radial-gradient(circle_at_top,#121217_0%,#09090b_45%,#060608_100%)] dark:text-zinc-100">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col px-6 py-6 lg:px-8">
        <div className="flex items-center justify-between">
          <Link
            href="/"
            className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/80 px-4 py-2 text-sm font-medium text-slate-600 shadow-sm backdrop-blur transition hover:border-slate-300 hover:text-slate-900"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to home
          </Link>

          <div className="flex items-center gap-3">
            <ThemeToggle />
            <div className="hidden items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-medium text-emerald-700 dark:border-emerald-900/70 dark:bg-emerald-950/40 dark:text-emerald-300 sm:inline-flex">
              <BadgeCheck className="h-4 w-4" />
              Theme-ready preview
            </div>
          </div>
        </div>

        <section className="grid flex-1 items-center gap-16 py-10 lg:grid-cols-[1.05fr_0.95fr] lg:py-16">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700">
              <Sparkles className="h-4 w-4" />
              /ok route demo
            </div>

            <h1 className="mt-6 text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl lg:text-6xl">
              A clean, light canvas for the card swap animation.
            </h1>

            <p className="mt-6 max-w-xl text-lg leading-8 text-slate-600">
              This route showcases the `CardSwap` component with a bright UI, soft shadows,
              and source-friendly content that feels at home in the rest of the app.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <span className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600 shadow-sm">
                Light theme
              </span>
              <span className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600 shadow-sm">
                Interactive cards
              </span>
              <span className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600 shadow-sm">
                GSAP motion
              </span>
            </div>

            <div className="mt-10 grid gap-4 sm:grid-cols-3">
              {[
                ["Fast", "retrieval"],
                ["Cited", "answers"],
                ["Polished", "UI"]
              ].map(([value, label]) => (
                <div key={value} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                  <div className="text-2xl font-semibold text-slate-950">{value}</div>
                  <div className="mt-1 text-sm text-slate-500">{label}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="relative min-h-130 overflow-visible rounded-[2rem] border border-slate-200 bg-white/60 p-4 shadow-2xl shadow-slate-200/70 backdrop-blur-sm sm:min-h-140">
            <div className="pointer-events-none absolute inset-0 rounded-[2rem] bg-[linear-gradient(135deg,rgba(59,130,246,0.09),rgba(255,255,255,0.35),rgba(15,23,42,0.02))]" />

            <div className="relative h-full min-h-130 w-full sm:min-h-140">
              <CardSwap
                width={520}
                height={420}
                delay={4200}
                pauseOnHover
                skewAmount={4}
                cardDistance={58}
                verticalDistance={68}
                easing="elastic"
              >
                {cards.map((card, index) => (
                  <Card
                    key={card.title}
                    customClass="flex h-full w-full flex-col justify-between bg-white/95 p-6 text-left ring-1 ring-slate-200/80"
                  >
                    <div>
                      <div className="inline-flex rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                        0{index + 1}
                      </div>
                      <h2 className="mt-4 text-2xl font-semibold text-slate-950">{card.title}</h2>
                      <p className="mt-3 text-sm leading-6 text-slate-600">{card.description}</p>
                    </div>

                    <div className="mt-8 rounded-2xl bg-slate-50 p-4">
                      <div className="text-4xl font-semibold tracking-tight text-slate-950">
                        {card.stat}
                      </div>
                      <p className="mt-2 text-sm leading-6 text-slate-500">{card.detail}</p>
                    </div>
                  </Card>
                ))}
              </CardSwap>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

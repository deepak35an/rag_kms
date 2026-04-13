"use client";
import { TimelineContent } from "@/components/ui/about/timeline-animation";
import Link from "next/link";
import { ArrowUpRight, FileSearch2, ShieldCheck, Sparkles } from "lucide-react";
import { useRef } from "react";

export default function AboutSection2() {
  const heroRef = useRef<HTMLDivElement>(null);
  const revealVariants = {
    visible: (i: number) => ({
      y: 0,
      opacity: 1,
      filter: "blur(0px)",
      transition: {
        delay: i * 0.12,
        duration: 0.6,
      },
    }),
    hidden: {
      filter: "blur(10px)",
      y: 24,
      opacity: 0,
    },
  };
  const textVariants = {
    visible: (i: number) => ({
      filter: "blur(0px)",
      opacity: 1,
      transition: {
        delay: i * 0.08,
        duration: 0.55,
      },
    }),
    hidden: {
      filter: "blur(10px)",
      opacity: 0,
    },
  };

  const pillars = [
    {
      icon: FileSearch2,
      title: "Grounded retrieval",
      description:
        "Hybrid search finds the most relevant chunks before generation, so answers stay tied to real source context.",
    },
    {
      icon: Sparkles,
      title: "Clear, cited responses",
      description:
        "Users get concise answers with traceable citations, making validation fast for teams and stakeholders.",
    },
    {
      icon: ShieldCheck,
      title: "Private by design",
      description:
        "Run fully on your infrastructure with local models and storage — your knowledge base stays in your control.",
    },
  ];

  return (
    <section id="about" className="bg-gray-50 px-4 py-24 sm:px-6 lg:px-8 dark:bg-zinc-950">
      <div className="mx-auto max-w-7xl" ref={heroRef}>
        <div className="rounded-3xl border border-gray-200 bg-white/80 p-8 shadow-sm backdrop-blur-sm dark:border-zinc-800 dark:bg-zinc-900/70 sm:p-10 lg:p-14">
          <div className="grid gap-10 lg:grid-cols-[1.2fr_0.8fr] lg:items-start">
            <div>
            <TimelineContent
              as="p"
              animationNum={0}
              timelineRef={heroRef}
              customVariants={revealVariants}
              className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-600"
            >
              About
              </TimelineContent>

              <TimelineContent
                as="h2"
                animationNum={1}
                timelineRef={heroRef}
                customVariants={revealVariants}
                className="mt-4 text-3xl font-semibold leading-tight text-gray-900 sm:text-4xl lg:text-5xl"
              >
                We built a{" "}
              <TimelineContent
                as="span"
                animationNum={2}
                timelineRef={heroRef}
                customVariants={textVariants}
                className="inline-block rounded-md border border-dashed border-blue-200 px-2 text-blue-600"
              >
                document-first
              </TimelineContent>{" "}
              RAG system that keeps answers{" "}
              <TimelineContent
                as="span"
                animationNum={3}
                timelineRef={heroRef}
                customVariants={textVariants}
                className="inline-block rounded-md border border-dashed border-blue-200 px-2 text-blue-600"
              >
                grounded
              </TimelineContent>{" "}
              and your data{" "}
              <TimelineContent
                as="span"
                animationNum={4}
                timelineRef={heroRef}
                customVariants={textVariants}
                className="inline-block rounded-md border border-dashed border-blue-200 px-2 text-blue-600"
              >
                private.
              </TimelineContent>
              </TimelineContent>

              <TimelineContent
                as="p"
                animationNum={5}
                timelineRef={heroRef}
                customVariants={textVariants}
                className="mt-6 max-w-2xl text-base leading-relaxed text-gray-600 sm:text-lg"
              >
                From brochures and policy docs to manuals and reports, RAG AI helps your team ask natural-language
                questions and get fast, citation-backed answers without manually searching page by page.
              </TimelineContent>

              <TimelineContent
                as="div"
                animationNum={6}
                timelineRef={heroRef}
                customVariants={textVariants}
                className="mt-8 flex flex-wrap items-center gap-3"
              >
                <Link
                  href="/login"
                  className="inline-flex items-center gap-2 rounded-full bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-[0_10px_24px_rgba(183,154,82,0.32)] transition-transform hover:-translate-y-0.5"
                >
                  Open dashboard
                  <ArrowUpRight className="h-4 w-4" />
                </Link>

                <a
                  href="#how-it-works"
                  className="inline-flex items-center rounded-full border border-gray-200 px-5 py-2.5 text-sm font-semibold text-gray-700 transition-colors hover:border-blue-200 hover:text-gray-900 dark:border-zinc-700 dark:text-zinc-300 dark:hover:border-zinc-500 dark:hover:text-zinc-100"
                >
                  See workflow
                </a>
              </TimelineContent>
            </div>

            <TimelineContent
              as="div"
              animationNum={7}
              timelineRef={heroRef}
              customVariants={textVariants}
              className="space-y-4"
            >
              {pillars.map(({ icon: Icon, title, description }, index) => (
                <div
                  key={title}
                  className="rounded-2xl border border-gray-200 bg-white p-5 transition-all duration-300 will-change-transform hover:-translate-y-1.5 hover:border-blue-200 hover:shadow-[0_16px_34px_rgba(17,24,39,0.10)] dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-700 dark:hover:shadow-[0_16px_34px_rgba(0,0,0,0.45)]"
                >
                  <div className="mb-3 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="text-base font-semibold text-gray-900 sm:text-lg">{title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-gray-600 sm:text-[0.95rem]">{description}</p>
                  {index < pillars.length - 1 && <div className="mt-4 border-b border-gray-100 dark:border-zinc-800" />}
                </div>
              ))}
            </TimelineContent>
          </div>
        </div>
      </div>
    </section>
  );
}
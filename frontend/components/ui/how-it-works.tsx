"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import {
  BrainCircuit,
  Database,
  FileSearch2,
  ScanSearch,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import type React from "react";

// The main props for the HowItWorks component
type HowItWorksProps = React.HTMLAttributes<HTMLElement>;

// The props for a single step card
interface StepCardProps {
  step: number;
  icon: React.ReactNode;
  title: string;
  description: string;
  benefits: string[];
  className?: string;
}

/**
 * A single step card within the "How It Works" section.
 * It displays an icon, title, description, and a list of benefits.
 */
const StepCard: React.FC<StepCardProps> = ({
  step,
  icon,
  title,
  description,
  benefits,
  className,
}) => (
  <Card
    className={cn(
      "h-full rounded-2xl border-gray-200 bg-white/90 transition-all duration-300 ease-out will-change-transform",
      "hover:-translate-y-1.5 hover:border-blue-200 hover:shadow-[0_18px_34px_rgba(17,24,39,0.10)]",
      "dark:border-zinc-800 dark:bg-zinc-900/90 dark:hover:border-zinc-700 dark:hover:shadow-[0_18px_34px_rgba(0,0,0,0.42)]",
      className,
    )}
  >
    <CardHeader className="space-y-4 p-6">
      <div className="flex items-center justify-between">
        <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
          {icon}
        </div>
        <span className="text-sm font-semibold tracking-[0.12em] text-blue-600">
          {String(step).padStart(2, "0")}
        </span>
      </div>

      <CardTitle className="text-xl leading-tight text-gray-900 dark:text-zinc-100">
        {title}
      </CardTitle>

      <CardDescription className="text-base leading-relaxed text-gray-600 dark:text-zinc-300">
        {description}
      </CardDescription>
    </CardHeader>

    <CardContent className="px-6 pb-6 pt-0">
      <ul className="space-y-3">
        {benefits.map((benefit, index) => (
          <li key={index} className="flex items-start gap-3">
            <div className="mt-1 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-blue-100">
              <div className="h-1.5 w-1.5 rounded-full bg-blue-600"></div>
            </div>
            <span className="text-sm text-gray-600 dark:text-zinc-300">{benefit}</span>
          </li>
        ))}
      </ul>
    </CardContent>
  </Card>
);

/**
 * A responsive "How It Works" section that displays a 3-step process.
 * It is styled with shadcn/ui theme variables to support light and dark modes.
 */
export const HowItWorks: React.FC<HowItWorksProps> = ({
  className,
  ...props
}) => {
  const stepsData = [
    {
      icon: <Database className="h-6 w-6" />,
      title: "Ingest your documents",
      description:
        "Upload PDFs, markdown files, and scanned docs to create a centralized knowledge base.",
      benefits: [
        "Supports mixed file formats",
        "OCR-friendly ingestion pipeline",
        "Fully local document storage",
      ],
    },
    {
      icon: <ScanSearch className="h-6 w-6" />,
      title: "Parse and chunk smartly",
      description:
        "The pipeline structures content into retrieval-ready chunks while preserving context and source metadata.",
      benefits: [
        "Semantic and recursive chunking",
        "Source-aware segmentation",
        "Chunk-level traceability",
      ],
    },
    {
      icon: <BrainCircuit className="h-6 w-6" />,
      title: "Embed and index",
      description:
        "Chunks are converted into embeddings and indexed for fast similarity search over your corpus.",
      benefits: [
        "High-recall vector retrieval",
        "Optimized for local inference",
        "Low-latency indexing",
      ],
    },
    {
      icon: <FileSearch2 className="h-6 w-6" />,
      title: "Retrieve with hybrid search",
      description:
        "For each question, the system combines BM25 and semantic retrieval to surface the strongest evidence.",
      benefits: [
        "Keyword + vector blending",
        "Relevance-focused chunk ranking",
        "Higher precision on dense docs",
      ],
    },
    {
      icon: <Sparkles className="h-6 w-6" />,
      title: "Generate grounded answers",
      description:
        "A local LLM generates concise responses using only retrieved context from your knowledge base.",
      benefits: [
        "Conversation-aware responses",
        "Reduced hallucination risk",
        "Readable markdown-safe output",
      ],
    },
    {
      icon: <ShieldCheck className="h-6 w-6" />,
      title: "Verify with citations",
      description:
        "Each response links back to source chunks so teams can validate results before taking action.",
      benefits: [
        "Document and page-level citation",
        "Audit-friendly answer trail",
        "Trustable decisions at speed",
      ],
    },
  ];

  return (
    <section
      id="how-it-works"
      className={cn("w-full bg-gray-50 py-24 dark:bg-zinc-950", className)}
      {...props}
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="mx-auto mb-16 max-w-3xl text-center">
          <p className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-blue-600">
            How It Works
          </p>
          <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            From upload to cited answers
          </h2>
          <p className="mt-4 text-lg text-gray-600 dark:text-zinc-300">
            A modern, end-to-end RAG workflow that transforms static files into
            fast, explainable and trustworthy answers.
          </p>
        </div>

        {/* Steps Grid */}
        <div className="relative">
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-x-12 top-1/2 hidden h-px -translate-y-1/2 bg-linear-to-r from-transparent via-gray-200 to-transparent lg:block dark:via-zinc-800"
          />

          <div className="grid grid-cols-1 gap-7 md:grid-cols-2 lg:grid-cols-3">
          {stepsData.map((step, index) => (
            <StepCard
              key={index}
              step={index + 1}
              icon={step.icon}
              title={step.title}
              description={step.description}
              benefits={step.benefits}
              className={cn(index % 2 === 0 ? "lg:-translate-y-4" : "lg:translate-y-6")}
            />
          ))}
          </div>
        </div>
      </div>
    </section>
  );
};

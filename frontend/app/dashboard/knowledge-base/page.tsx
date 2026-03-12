"use client";

import { useState, useEffect } from "react";

interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  docCount: number;
  updatedAt: string;
}

const STORAGE_KEY = "rag_knowledge_bases";

const DEFAULT_KBS: KnowledgeBase[] = [
  {
    id: "kb-1",
    name: "Company Policies",
    description: "Employee handbook, HR policies, and company guidelines",
    docCount: 2,
    updatedAt: "2026-02-15",
  },
  {
    id: "kb-2",
    name: "Technical Documentation",
    description: "API references, product docs, and technical guides",
    docCount: 1,
    updatedAt: "2026-02-20",
  },
];

export default function KnowledgeBasePage() {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // Load from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed: KnowledgeBase[] = JSON.parse(stored);
      setKnowledgeBases(parsed);
      if (parsed.length > 0) setSelectedId(parsed[0].id);
    } else {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_KBS));
      setKnowledgeBases(DEFAULT_KBS);
      setSelectedId(DEFAULT_KBS[0].id);
    }
  }, []);

  const handleDelete = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const updated = knowledgeBases.filter((kb) => kb.id !== id);
    setKnowledgeBases(updated);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    if (selectedId === id) setSelectedId(updated[0]?.id ?? null);
  };

  const selectedKB = knowledgeBases.find((kb) => kb.id === selectedId);

  return (
    <div className="max-w-5xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Knowledge Base</h1>
          <p className="text-gray-500 mt-1 text-sm">
            Create and manage multiple knowledge bases for your RAG chatbot
          </p>
        </div>
        <button
          onClick={() => {
            const name = prompt("Knowledge base name:");
            if (!name?.trim()) return;
            const desc = prompt("Short description:") ?? "";
            const newKB: KnowledgeBase = {
              id: `kb-${Date.now()}`,
              name: name.trim(),
              description: desc.trim(),
              docCount: 0,
              updatedAt: new Date().toISOString().split("T")[0],
            };
            const updated = [...knowledgeBases, newKB];
            setKnowledgeBases(updated);
            localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
            setSelectedId(newKB.id);
          }}
          className="flex items-center gap-2 bg-gray-900 hover:bg-gray-800 text-white text-sm font-medium px-4 py-2.5 rounded-lg transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Knowledge Base
        </button>
      </div>

      {/* KB Cards Grid */}
      {knowledgeBases.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          <svg className="w-12 h-12 mx-auto mb-3 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.331 0 4.467.89 6.064 2.346m0-14.304a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.346m0-14.304v14.304" />
          </svg>
          <p className="font-medium">No knowledge bases yet</p>
          <p className="text-sm mt-1">Click &quot;+ New Knowledge Base&quot; to create one</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
          {knowledgeBases.map((kb) => {
            const isSelected = kb.id === selectedId;
            return (
              <div
                key={kb.id}
                onClick={() => setSelectedId(kb.id)}
                className={`relative cursor-pointer rounded-xl border-2 p-5 transition-all ${
                  isSelected
                    ? "border-blue-500 bg-white shadow-md"
                    : "border-gray-200 bg-white hover:border-blue-200 hover:shadow-sm"
                }`}
              >
                {/* Delete button */}
                <button
                  onClick={(e) => handleDelete(kb.id, e)}
                  className="absolute top-4 right-4 p-1.5 text-gray-400 hover:text-red-500 rounded-lg hover:bg-red-50 transition-colors"
                  title="Delete knowledge base"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                  </svg>
                </button>

                <div className="flex items-center gap-3 mb-3 pr-8">
                  <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${isSelected ? "bg-blue-100" : "bg-gray-100"}`}>
                    <svg className={`w-5 h-5 ${isSelected ? "text-blue-600" : "text-gray-500"}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                    </svg>
                  </div>
                  <h3 className="font-semibold text-gray-900 text-sm">{kb.name}</h3>
                </div>
                <p className="text-xs text-gray-500 mb-4 pr-8 leading-relaxed">{kb.description}</p>
                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span>{kb.docCount} document{kb.docCount !== 1 ? "s" : ""}</span>
                  <span>{kb.updatedAt}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Selected KB info */}
      {selectedKB && (
        <div className="mt-2 p-4 bg-blue-50 border border-blue-100 rounded-lg text-sm text-blue-700">
          <span className="font-medium">Selected:</span> {selectedKB.name} — upload section and documents will appear below (Steps 3 &amp; 4).
        </div>
      )}
    </div>
  );
}

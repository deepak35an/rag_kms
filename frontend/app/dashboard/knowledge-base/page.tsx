"use client";

import { useState, useEffect, useRef } from "react";

interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  docCount: number;
  updatedAt: string;
}

interface Document {
  id: string;
  name: string;
  uploadDate: string;
  size: string;
  status: "processed" | "processing" | "failed";
  kbId: string;
}

const STORAGE_KEY = "rag_knowledge_bases";
const DOCS_STORAGE_KEY = "rag_documents";

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

const DEFAULT_DOCS: Document[] = [
  {
    id: "doc-1",
    name: "Company Handbook 2026.pdf",
    uploadDate: "2026-03-01",
    size: "2.4 MB",
    status: "processed",
    kbId: "kb-1",
  },
  {
    id: "doc-2",
    name: "HR Policies.pdf",
    uploadDate: "2026-03-02",
    size: "1.8 MB",
    status: "processed",
    kbId: "kb-1",
  },
  {
    id: "doc-3",
    name: "API Documentation.pdf",
    uploadDate: "2026-02-20",
    size: "3.2 MB",
    status: "processed",
    kbId: "kb-2",
  },
];

export default function KnowledgeBasePage() {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newKBName, setNewKBName] = useState("");
  const [newKBDesc, setNewKBDesc] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    const storedDocs = localStorage.getItem(DOCS_STORAGE_KEY);
    
    if (stored) {
      const parsed: KnowledgeBase[] = JSON.parse(stored);
      setKnowledgeBases(parsed);
      if (parsed.length > 0) setSelectedId(parsed[0].id);
    } else {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_KBS));
      setKnowledgeBases(DEFAULT_KBS);
      setSelectedId(DEFAULT_KBS[0].id);
    }

    if (storedDocs) {
      setDocuments(JSON.parse(storedDocs));
    } else {
      localStorage.setItem(DOCS_STORAGE_KEY, JSON.stringify(DEFAULT_DOCS));
      setDocuments(DEFAULT_DOCS);
    }
  }, []);

  const handleDelete = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const updated = knowledgeBases.filter((kb) => kb.id !== id);
    setKnowledgeBases(updated);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    if (selectedId === id) setSelectedId(updated[0]?.id ?? null);
  };

  const handleCreateKB = () => {
    if (!newKBName.trim()) return;
    
    const newKB: KnowledgeBase = {
      id: `kb-${Date.now()}`,
      name: newKBName.trim(),
      description: newKBDesc.trim(),
      docCount: 0,
      updatedAt: new Date().toISOString().split("T")[0],
    };
    const updated = [...knowledgeBases, newKB];
    setKnowledgeBases(updated);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    setSelectedId(newKB.id);
    
    // Reset modal
    setShowCreateModal(false);
    setNewKBName("");
    setNewKBDesc("");
  };

  const handleFileUpload = (files: FileList | null) => {
    if (!files || !selectedId) return;
    
    const newDocs: Document[] = Array.from(files).map((file) => ({
      id: `doc-${Date.now()}-${Math.random()}`,
      name: file.name,
      uploadDate: new Date().toISOString().split("T")[0],
      size: `${(file.size / 1024 / 1024).toFixed(1)} MB`,
      status: "processed" as const,
      kbId: selectedId,
    }));

    const updatedDocs = [...documents, ...newDocs];
    setDocuments(updatedDocs);
    localStorage.setItem(DOCS_STORAGE_KEY, JSON.stringify(updatedDocs));

    // Update doc count in KB
    const updatedKBs = knowledgeBases.map((kb) =>
      kb.id === selectedId
        ? { ...kb, docCount: kb.docCount + newDocs.length, updatedAt: new Date().toISOString().split("T")[0] }
        : kb
    );
    setKnowledgeBases(updatedKBs);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedKBs));
  };

  const handleDeleteDoc = (docId: string) => {
    const doc = documents.find((d) => d.id === docId);
    if (!doc) return;

    const updatedDocs = documents.filter((d) => d.id !== docId);
    setDocuments(updatedDocs);
    localStorage.setItem(DOCS_STORAGE_KEY, JSON.stringify(updatedDocs));

    // Update doc count in KB
    const updatedKBs = knowledgeBases.map((kb) =>
      kb.id === doc.kbId ? { ...kb, docCount: Math.max(0, kb.docCount - 1) } : kb
    );
    setKnowledgeBases(updatedKBs);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedKBs));
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFileUpload(e.dataTransfer.files);
  };

  const selectedKB = knowledgeBases.find((kb) => kb.id === selectedId);
  const selectedDocs = documents.filter((doc) => doc.kbId === selectedId);

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
          onClick={() => setShowCreateModal(true)}
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
        <div className="mt-8 space-y-6">
          {/* Upload Section */}
          <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
            <div className="flex items-start gap-3 mb-4">
              <svg className="w-5 h-5 text-blue-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <div>
                <h3 className="font-semibold text-gray-900 text-sm">
                  Upload Documents to &quot;{selectedKB.name}&quot;
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  Add PDF documents to this knowledge base for retrieval
                </p>
              </div>
            </div>

            {/* Drag and Drop Area */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all ${
                isDragging
                  ? "border-blue-500 bg-blue-50"
                  : "border-gray-300 hover:border-blue-400 hover:bg-gray-100"
              }`}
            >
              <svg className="w-10 h-10 mx-auto mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p className="text-sm font-medium text-gray-900 mb-1">
                Drop files here or click to upload
              </p>
              <p className="text-xs text-gray-500">
                Supports PDF, DOC, DOCX, and TXT files
              </p>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.doc,.docx,.txt"
              onChange={(e) => handleFileUpload(e.target.files)}
              className="hidden"
            />
          </div>

          {/* Documents List */}
          {selectedDocs.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="font-semibold text-gray-900 text-sm">
                  Documents in &quot;{selectedKB.name}&quot;
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  {selectedDocs.length} document{selectedDocs.length !== 1 ? "s" : ""} in this knowledge base
                </p>
              </div>

              {/* Table Header */}
              <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
                <div className="grid grid-cols-12 gap-4 text-xs font-medium text-gray-500 uppercase">
                  <div className="col-span-5">Document Name</div>
                  <div className="col-span-2">Upload Date</div>
                  <div className="col-span-2">Size</div>
                  <div className="col-span-2">Status</div>
                  <div className="col-span-1">Actions</div>
                </div>
              </div>

              {/* Table Body */}
              <div className="divide-y divide-gray-100">
                {selectedDocs.map((doc) => (
                  <div key={doc.id} className="px-6 py-4 hover:bg-gray-50 transition-colors">
                    <div className="grid grid-cols-12 gap-4 items-center text-sm">
                      <div className="col-span-5 flex items-center gap-2">
                        <svg className="w-4 h-4 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                        </svg>
                        <span className="text-gray-900 truncate">{doc.name}</span>
                      </div>
                      <div className="col-span-2 text-gray-500">{doc.uploadDate}</div>
                      <div className="col-span-2 text-gray-500">{doc.size}</div>
                      <div className="col-span-2">
                        <span className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium ${
                          doc.status === "processed"
                            ? "bg-green-100 text-green-700"
                            : doc.status === "processing"
                            ? "bg-yellow-100 text-yellow-700"
                            : "bg-red-100 text-red-700"
                        }`}>
                          {doc.status === "processed" ? "Processed" : doc.status === "processing" ? "Processing" : "Failed"}
                        </span>
                      </div>
                      <div className="col-span-1 flex items-center gap-2">
                        <button
                          onClick={() => handleDeleteDoc(doc.id)}
                          className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                          title="Delete document"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Create Knowledge Base Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-lg font-semibold text-gray-900">
                Create Knowledge Base
              </h3>
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setNewKBName("");
                  setNewKBDesc("");
                }}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={newKBName}
                  onChange={(e) => setNewKBName(e.target.value)}
                  placeholder="e.g., Company Policies"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Description
                </label>
                <textarea
                  value={newKBDesc}
                  onChange={(e) => setNewKBDesc(e.target.value)}
                  placeholder="Brief description of this knowledge base..."
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                />
              </div>
            </div>

            <div className="flex items-center gap-3 mt-6">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setNewKBName("");
                  setNewKBDesc("");
                }}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateKB}
                disabled={!newKBName.trim()}
                className="flex-1 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

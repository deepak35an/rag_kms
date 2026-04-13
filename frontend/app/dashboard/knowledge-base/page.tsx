"use client";

import { useEffect, useState, useRef } from "react";
import {
  uploadDocuments,
  ingestDocuments,
  listKBs,
  listDocs,
  createKB,
  deleteKB,
  deleteDoc,
} from "@/app/lib/api";

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
  serverFilename?: string;
  uploadDate: string;
  size: string;
  status: "processed" | "processing" | "failed";
  kbId: string;
}

interface ToastState {
  type: "success" | "error";
  message: string;
}

const STORAGE_KEY = "rag_knowledge_bases";
const DOCS_STORAGE_KEY = "rag_documents";

const DEFAULT_KBS: KnowledgeBase[] = [
  
];

const DEFAULT_DOCS: Document[] = [
  
];

function readJSON<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback;
  const raw = localStorage.getItem(key);
  if (!raw) return fallback;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function bootstrapKnowledgeBaseState() {
  if (typeof window === "undefined") {
    return {
      knowledgeBases: DEFAULT_KBS,
      documents: DEFAULT_DOCS,
      selectedId: DEFAULT_KBS[0]?.id ?? null,
    };
  }

  const knowledgeBases = readJSON<KnowledgeBase[]>(STORAGE_KEY, DEFAULT_KBS);
  const documents = readJSON<Document[]>(DOCS_STORAGE_KEY, DEFAULT_DOCS);

  const docCountByKb = documents.reduce<Record<string, number>>((acc, doc) => {
    acc[doc.kbId] = (acc[doc.kbId] ?? 0) + 1;
    return acc;
  }, {});

  const normalizedKbs = knowledgeBases.map((kb) => ({
    ...kb,
    docCount: docCountByKb[kb.id] ?? 0,
  }));

  localStorage.setItem(STORAGE_KEY, JSON.stringify(normalizedKbs));
  localStorage.setItem(DOCS_STORAGE_KEY, JSON.stringify(documents));

  return {
    knowledgeBases: normalizedKbs,
    documents,
    selectedId: normalizedKbs[0]?.id ?? null,
  };
}

function mapIngestStatusToUiStatus(status?: string): Document["status"] {
  if (status === "ingested") return "processed";
  if (status === "failed") return "failed";
  return "processing";
}

export default function KnowledgeBasePage() {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>(DEFAULT_KBS);
  const [documents, setDocuments] = useState<Document[]>(DEFAULT_DOCS);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newKBName, setNewKBName] = useState("");
  const [newKBDesc, setNewKBDesc] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [toast, setToast] = useState<ToastState | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const showToast = (message: string, type: ToastState["type"] = "success") => {
    setToast({ message, type });
    window.setTimeout(() => setToast(null), 2400);
  };

  const removeDocFromState = (docId: string, kbId: string) => {
    const updatedDocs = documents.filter((d) => d.id !== docId);
    setDocuments(updatedDocs);
    localStorage.setItem(DOCS_STORAGE_KEY, JSON.stringify(updatedDocs));

    const updatedKBs = knowledgeBases.map((kb) =>
      kb.id === kbId ? { ...kb, docCount: Math.max(0, kb.docCount - 1) } : kb
    );
    setKnowledgeBases(updatedKBs);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedKBs));
  };

  useEffect(() => {
    const boot = bootstrapKnowledgeBaseState();
    setKnowledgeBases(boot.knowledgeBases);
    setDocuments(boot.documents);
    setSelectedId(boot.selectedId);
  }, []);

  useEffect(() => {
    let cancelled = false;

    const loadKnowledgeBases = async () => {
      try {
        const response = await listKBs();

        if (response.status !== "success") {
          throw new Error(response.message || "Failed to load knowledge bases");
        }

        const serverKBs: KnowledgeBase[] = (response.knowledge_bases ?? []).map((kb) => ({
          id: kb.id,
          name: kb.name,
          description: kb.description || "",
          docCount: kb.doc_count ?? 0,
          updatedAt: kb.created_at?.split("T")[0] || new Date().toISOString().split("T")[0],
        }));

        if (cancelled) return;

        setKnowledgeBases(serverKBs);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(serverKBs));

        setSelectedId((prev) => {
          if (prev && serverKBs.some((kb) => kb.id === prev)) return prev;
          return serverKBs[0]?.id ?? null;
        });
      } catch (error) {
        if (cancelled) return;
        showToast(
          error instanceof Error ? error.message : "Failed to load knowledge bases",
          "error"
        );
      }
    };

    void loadKnowledgeBases();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!selectedId) return;

    let cancelled = false;

    const loadDocumentsForKb = async () => {
      try {
        const response = await listDocs(selectedId);
        if (response.status !== "success") {
          throw new Error(response.message || "Failed to load documents");
        }

        const serverDocs: Document[] = (response.documents ?? []).map((doc, index) => ({
          id: `${selectedId}-${doc.filename}-${index}`,
          name: doc.filename,
          serverFilename: doc.filename,
          uploadDate: doc.uploaded_at?.split("T")[0] || "-",
          size: `${(doc.size_bytes / 1024 / 1024).toFixed(1)} MB`,
          status: mapIngestStatusToUiStatus(doc.ingest_status),
          kbId: selectedId,
        }));

        if (cancelled) return;

        setDocuments((prev) => {
          const merged = [...prev.filter((doc) => doc.kbId !== selectedId), ...serverDocs];
          localStorage.setItem(DOCS_STORAGE_KEY, JSON.stringify(merged));
          return merged;
        });

        setKnowledgeBases((prev) => {
          const updated = prev.map((kb) =>
            kb.id === selectedId ? { ...kb, docCount: serverDocs.length } : kb
          );
          localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
          return updated;
        });
      } catch (error) {
        if (cancelled) return;
        showToast(
          error instanceof Error ? error.message : "Failed to load documents",
          "error"
        );
      }
    };

    void loadDocumentsForKb();

    return () => {
      cancelled = true;
    };
  }, [selectedId]);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();

    try {
      const response = await deleteKB(id);
      if (response.status !== "success") {
        throw new Error(response.message || "Failed to delete knowledge base");
      }

      const updated = knowledgeBases.filter((kb) => kb.id !== id);
      setKnowledgeBases(updated);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));

      const updatedDocs = documents.filter((doc) => doc.kbId !== id);
      setDocuments(updatedDocs);
      localStorage.setItem(DOCS_STORAGE_KEY, JSON.stringify(updatedDocs));

      if (selectedId === id) setSelectedId(updated[0]?.id ?? null);
      showToast("Knowledge base deleted");
    } catch (error) {
      showToast(
        error instanceof Error ? error.message : "Failed to delete knowledge base",
        "error"
      );
    }
  };

  const handleCreateKB = async () => {
    if (!newKBName.trim()) return;

    const tempId = `kb-${Date.now()}`;

    try {
      const response = await createKB(tempId, newKBName.trim(), newKBDesc.trim());

      if (response.status !== "success" || !response.id) {
        throw new Error(response.message || "Failed to create knowledge base");
      }

      const newKB: KnowledgeBase = {
        id: response.id,
        name: response.name || newKBName.trim(),
        description: response.description || newKBDesc.trim(),
        docCount: 0,
        updatedAt: response.created_at?.split("T")[0] || new Date().toISOString().split("T")[0],
      };

      const updated = [...knowledgeBases, newKB];
      setKnowledgeBases(updated);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      setSelectedId(newKB.id);

      // Reset modal
      setShowCreateModal(false);
      setNewKBName("");
      setNewKBDesc("");
      showToast("Knowledge base created");
    } catch (error) {
      showToast(
        error instanceof Error ? error.message : "Failed to create knowledge base",
        "error"
      );
    }
  };

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || !selectedId) return;
    const selectedFiles = Array.from(files);

    try {
      // Step 1: Upload files to backend
      const result = await uploadDocuments(selectedId, selectedFiles);
      if (result.status !== "success") {
        showToast(result.message || "Upload failed", "error");
        return;
      }

      const uploadedFiles = result.files ?? [];
      const newDocs: Document[] = uploadedFiles.map((file) => ({
        id: `doc-${Date.now()}-${Math.random()}`,
        name: file.original_filename || file.filename,
        serverFilename: file.filename,
        uploadDate: new Date().toISOString().split("T")[0],
        size: `${(file.size_bytes / 1024 / 1024).toFixed(1)} MB`,
        status: "processing" as const, // Start with processing status
        kbId: selectedId,
      }));

      if (newDocs.length === 0) {
        showToast("No files were uploaded", "error");
        return;
      }

      // Update documents with processing status
      const updatedDocs = [...documents, ...newDocs];
      setDocuments(updatedDocs);
      localStorage.setItem(DOCS_STORAGE_KEY, JSON.stringify(updatedDocs));

      showToast(`${newDocs.length} document${newDocs.length > 1 ? "s" : ""} uploading...`);

      // Step 2: Ingest documents (embed and store in vector DB)
      try {
        const ingestResult = await ingestDocuments(selectedId);
        
        if (ingestResult.status === "success") {
          // Update document status to processed
          const processedDocs = updatedDocs.map((doc) =>
            doc.kbId === selectedId && newDocs.some((nd) => nd.id === doc.id)
              ? { ...doc, status: "processed" as const }
              : doc
          );
          setDocuments(processedDocs);
          localStorage.setItem(DOCS_STORAGE_KEY, JSON.stringify(processedDocs));

          showToast(
            `Successfully ingested ${ingestResult.chunks_created || 0} chunks from documents`,
            "success"
          );
        } else {
          showToast(ingestResult.message || "Ingestion failed", "error");
          // Keep documents but mark as failed
          const failedDocs = updatedDocs.map((doc) =>
            doc.kbId === selectedId && newDocs.some((nd) => nd.id === doc.id)
              ? { ...doc, status: "failed" as const }
              : doc
          );
          setDocuments(failedDocs);
          localStorage.setItem(DOCS_STORAGE_KEY, JSON.stringify(failedDocs));
        }
      } catch (ingestError) {
        showToast(
          ingestError instanceof Error ? ingestError.message : "Ingestion failed",
          "error"
        );
        // Mark documents as failed
        const failedDocs = updatedDocs.map((doc) =>
          doc.kbId === selectedId && newDocs.some((nd) => nd.id === doc.id)
            ? { ...doc, status: "failed" as const }
            : doc
        );
        setDocuments(failedDocs);
        localStorage.setItem(DOCS_STORAGE_KEY, JSON.stringify(failedDocs));
      }

      // Update doc count in KB
      const updatedKBs = knowledgeBases.map((kb) =>
        kb.id === selectedId
          ? {
              ...kb,
              docCount: kb.docCount + newDocs.length,
              updatedAt: new Date().toISOString().split("T")[0],
            }
          : kb
      );
      setKnowledgeBases(updatedKBs);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedKBs));
    } catch (error) {
      showToast(
        error instanceof Error ? error.message : "Upload failed",
        "error"
      );
    }
  };

  const handleDeleteDoc = async (docId: string) => {
    const doc = documents.find((d) => d.id === docId);
    if (!doc) return;

    try {
      const filenameToDelete = doc.serverFilename || doc.name;
      const response = await deleteDoc(doc.kbId, filenameToDelete);

      if (response.status !== "success") {
        const message = response.message || "Failed to delete document";

        if (message.toLowerCase().includes("not found")) {
          // Local state is stale compared to server; remove row and sync UI.
          removeDocFromState(docId, doc.kbId);
          showToast("Document was already removed on server. Synced list.");
          return;
        }

        throw new Error(message);
      }

      removeDocFromState(docId, doc.kbId);
      showToast("Document deleted");
    } catch (error) {
      showToast(
        error instanceof Error ? error.message : "Failed to delete document",
        "error"
      );
    }
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
    <div className="w-full max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-10">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Knowledge Base</h1>
          <p className="text-gray-500 mt-2 text-base">
            Create and manage multiple knowledge bases for your RAG chatbot
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 bg-gray-900 hover:bg-gray-800 text-white text-base font-medium px-5 py-3 rounded-xl transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Knowledge Base
        </button>
      </div>

      {/* KB Cards Grid */}
      {knowledgeBases.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          <svg className="w-12 h-12 mx-auto mb-3 opacity-40 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.331 0 4.467.89 6.064 2.346m0-14.304a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.346m0-14.304v14.304" />
          </svg>
          <p className="font-medium">No knowledge bases yet</p>
          <p className="text-base mt-2">Click &quot;+ New Knowledge Base&quot; to create one</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
          {knowledgeBases.map((kb) => {
            const isSelected = kb.id === selectedId;
            return (
              <div
                key={kb.id}
                onClick={() => setSelectedId(kb.id)}
                className={`relative cursor-pointer rounded-2xl border-2 p-6 transition-all ${
                  isSelected
                    ? "border-[#c3a968] bg-white shadow-md"
                    : "border-gray-200 bg-white hover:border-[#d8c183] hover:shadow-sm"
                }`}
              >
                {/* Delete button */}
                <button
                  onClick={(e) => handleDelete(kb.id, e)}
                  className="absolute top-5 right-5 p-2 text-gray-400 hover:text-red-500 rounded-lg hover:bg-red-50 transition-colors"
                  title="Delete knowledge base"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                  </svg>
                </button>

                <div className="flex items-center gap-4 mb-4 pr-10">
                  <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${isSelected ? "bg-[#f6f0df]" : "bg-gray-100"}`}>
                    <svg className={`w-6 h-6 ${isSelected ? "text-[#a48745]" : "text-gray-500"}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                    </svg>
                  </div>
                  <h3 className="font-semibold text-gray-900 text-base">{kb.name}</h3>
                </div>
                <p className="text-base text-gray-600 mb-5 pr-10 leading-relaxed">{kb.description}</p>
                <div className="flex items-center justify-between text-sm text-gray-500 font-medium">
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
          <div className="bg-white rounded-xl p-8 border border-gray-200">
            <div className="flex items-start gap-4 mb-6">
              <svg className="w-6 h-6 text-[#a48745] mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <div>
                <h3 className="font-semibold text-gray-900 text-lg">
                  Upload Documents to &quot;{selectedKB.name}&quot;
                </h3>
                <p className="text-base text-gray-500 mt-2">
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
              className={`border-2 border-dashed rounded-xl p-16 text-center cursor-pointer transition-all ${
                isDragging
                  ? "border-[#c3a968] bg-[#f6f0df]"
                  : "border-gray-300 hover:border-[#b79a52] hover:bg-gray-50"
              }`}
            >
              <svg className="w-12 h-12 mx-auto mb-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
              </svg>
              <p className="text-lg font-semibold text-gray-900 mb-2">
                Drop files here or click to upload
              </p>
              <p className="text-base text-gray-500">
                Supports PDF, DOC, DOCX, and TXT files
              </p>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              onChange={(e) => handleFileUpload(e.target.files)}
              className="hidden"
            />
          </div>

          {/* Documents List */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="px-8 py-6 border-b border-gray-200">
                <h3 className="font-semibold text-gray-900 text-lg">
                  Documents in &quot;{selectedKB.name}&quot;
                </h3>
                <p className="text-base text-gray-500 mt-2">
                  {selectedDocs.length} document{selectedDocs.length !== 1 ? "s" : ""} in this knowledge base
                </p>
              </div>

              {selectedDocs.length > 0 ? (
                <div className="overflow-x-auto">
                  {/* Table Header */}
                  <div className="min-w-190 px-8 py-4 bg-gray-50 border-b border-gray-200">
                    <div className="grid grid-cols-12 gap-4 text-sm font-medium text-gray-500 uppercase">
                      <div className="col-span-5">Document Name</div>
                      <div className="col-span-2">Upload Date</div>
                      <div className="col-span-2">Size</div>
                      <div className="col-span-2">Status</div>
                      <div className="col-span-1">Actions</div>
                    </div>
                  </div>

                  {/* Table Body */}
                  <div className="min-w-190 divide-y divide-gray-100">
                    {selectedDocs.map((doc) => (
                      <div key={doc.id} className="px-8 py-5 hover:bg-gray-50 transition-colors">
                        <div className="grid grid-cols-12 gap-4 items-center text-base">
                          <div className="col-span-5 flex items-center gap-3">
                            <svg className="w-5 h-5 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                            </svg>
                            <span className="text-gray-900 truncate">{doc.name}</span>
                          </div>
                          <div className="col-span-2 text-gray-500">{doc.uploadDate}</div>
                          <div className="col-span-2 text-gray-500">{doc.size}</div>
                          <div className="col-span-2">
                            <span className={`inline-flex items-center px-2.5 py-1.5 rounded-md text-sm font-medium ${
                              doc.status === "processed"
                                ? "bg-green-100 text-green-700"
                                : doc.status === "processing"
                                ? "bg-yellow-100 text-yellow-700"
                                : "bg-red-100 text-red-700"
                            }`}>
                              {doc.status === "processed" ? "Processed" : doc.status === "processing" ? "Processing" : "Failed"}
                            </span>
                          </div>
                          <div className="col-span-1 flex items-center gap-3">
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
              ) : (
                <div className="px-6 py-16 text-center text-gray-400">
                  <svg className="w-10 h-10 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                  </svg>
                  <p className="font-medium text-gray-500">No documents uploaded yet</p>
                  <p className="text-sm mt-1">Upload your first document to get started</p>
                </div>
              )}
            </div>
        </div>
      )}

      {/* Create Knowledge Base Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-xl font-semibold text-gray-900">
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
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-5">
              <div>
                <label className="block text-base font-medium text-gray-700 mb-2">
                  Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={newKBName}
                  onChange={(e) => setNewKBName(e.target.value)}
                  placeholder="e.g., Company Policies"
                  className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl text-base text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#b79a52]/30 focus:border-transparent transition-all"
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-base font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={newKBDesc}
                  onChange={(e) => setNewKBDesc(e.target.value)}
                  placeholder="Brief description of this knowledge base..."
                  rows={3}
                  className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl text-base text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#b79a52]/30 focus:border-transparent resize-none transition-all"
                />
              </div>
            </div>

            <div className="flex items-center gap-4 mt-8">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setNewKBName("");
                  setNewKBDesc("");
                }}
                className="flex-1 px-4 py-2.5 border border-gray-300 text-gray-700 text-base font-medium rounded-xl hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateKB}
                disabled={!newKBName.trim()}
                className="flex-1 px-4 py-2.5 bg-[#b79a52] text-white text-base font-medium rounded-xl hover:bg-[#a48745] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}

      {toast && (
        <div className="fixed right-6 bottom-6 z-50">
          <div
            className={`px-5 py-4 rounded-xl border text-base shadow-lg ${
              toast.type === "success"
                ? "bg-white border-green-200 text-gray-800"
                : "bg-white border-red-200 text-gray-800"
            }`}
          >
            <div className="flex items-center gap-3">
              <span
                className={`w-3 h-3 rounded-full ${
                  toast.type === "success" ? "bg-green-500" : "bg-red-500"
                }`}
              />
              {toast.message}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

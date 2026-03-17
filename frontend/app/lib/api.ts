const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// --- Types ---

export interface HealthResponse {
  status: string;
  vectorstore_loaded: boolean;
  generator_loaded: boolean;
}

export interface SessionResponse {
  session_id: string;
}

export interface AskResponse {
  answer: string;
  sources: string[];
  retrieved_chunks?: { content: string; score: number }[];
  error?: string;
}

export interface UploadedFileInfo {
  filename: string;
  original_filename: string;
  size_bytes: number;
  saved_path: string;
  relative_path: string;
}

export interface UploadResponse {
  status: "success" | "error";
  kb_id?: string;
  upload_dir?: string;
  files?: UploadedFileInfo[];
  message?: string;
}

// --- API Functions ---

export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error("Backend unreachable");
  return res.json();
}

export async function createSession(): Promise<SessionResponse> {
  const res = await fetch(`${API_BASE}/create_session`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error("Failed to create session");
  return res.json();
}

export async function askQuestion(
  question: string,
  sessionId: string
): Promise<AskResponse> {
  const res = await fetch(`${API_BASE}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, session_id: sessionId }),
  });
  if (!res.ok) throw new Error("Failed to get answer");
  return res.json();
}

export async function uploadDocuments(
  kbId: string,
  files: File[]
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("kb_id", kbId);
  files.forEach((file) => formData.append("files", file));

  const res = await fetch(`${API_BASE}/upload_documents`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) throw new Error("Failed to upload documents");
  return res.json();
}

export async function saveChatHistory(
  conversationId: string,
  conversationMeta: Record<string, unknown>,
  messages: Record<string, unknown>[]
): Promise<{ status: string; file_path?: string; message?: string }> {
  const res = await fetch(`${API_BASE}/save_chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      conversation_id: conversationId,
      conversation_meta: conversationMeta,
      messages: messages,
    }),
  });
  
  if (!res.ok) throw new Error("Failed to save chat history to backend");
  return res.json();
}


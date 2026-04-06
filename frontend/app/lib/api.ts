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
  session_id?: string;
  question?: string;
  answer: string;
  sources: string[];
  retrieved_chunks?: { content: string; score: number }[];
  error?: string;
}

// Knowledge Base
export interface KBInfo {
  id: string;
  name: string;
  description: string;
  doc_count: number;
  created_at: string;
}

export interface ListKBsResponse {
  status: "success" | "error";
  knowledge_bases?: KBInfo[];
  message?: string;
}

export interface CreateKBResponse {
  status: "success" | "error";
  id?: string;
  name?: string;
  description?: string;
  created_at?: string;
  message?: string;
}

// Documents
export interface DocInfo {
  filename: string;
  size_bytes: number;
  ingest_status: string;
  chunks_created: number;
  uploaded_at: string;
}

export interface ListDocsResponse {
  status: "success" | "error";
  kb_id?: string;
  documents?: DocInfo[];
  message?: string;
}

// Chat History
export interface ChatSummary {
  id: string;
  title: string;
  preview: string;
  message_count: number;
  kb_id: string;
  kb_name: string;
  updated_at: string;
  status: string;
}

export interface ListChatsResponse {
  status: "success" | "error";
  conversations?: ChatSummary[];
  message?: string;
}

export interface GetChatResponse {
  status: "success" | "error";
  conversation_id?: string;
  meta?: Record<string, unknown>;
  messages?: Record<string, unknown>[];
  message?: string;
}

// Decoupled RAG flow: retrieve -> generate
export interface ChunkMetadata {
  source: string;
  page: number | string;
  relevance_score: number;
  kb_id: string;
  [key: string]: unknown;
}

export interface ChunkInfo {
  id: string;
  content: string;
  metadata: ChunkMetadata;
}

export interface RetrieveRequest {
  question: string;
  session_id: string;
  kb_id: string;
}

export interface RetrieveResponse {
  session_id: string;
  original_question: string;
  standalone_question: string;
  chunks: ChunkInfo[];
}

export interface GenerateRequest {
  question: string;
  session_id: string;
  selected_chunks: Array<Pick<ChunkInfo, "content" | "metadata">>;
}

export interface GenerateResponse {
  session_id: string;
  question: string;
  answer: string;
  sources: string[];
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

export interface IngestResponse {
  status: "success" | "error";
  kb_id?: string;
  files_ingested?: number;
  pages_extracted?: number;
  chunks_created?: number;
  message?: string;
}

export interface OperationResponse {
  status: "success" | "error";
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

/**
 * @deprecated Use retrieveChunks() and generateAnswer() for the two-step flow.
 */
export async function askQuestion(
  question: string,
  sessionId: string,
  kbId?: string
): Promise<AskResponse> {
  const payload = {
    question,
    session_id: sessionId,
    ...(kbId ? { kb_id: kbId } : {}),
  };

  const res = await fetch(`${API_BASE}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to get answer");
  return res.json();
}

export async function listKBs(): Promise<ListKBsResponse> {
  const res = await fetch(`${API_BASE}/list_kbs`);
  if (!res.ok) throw new Error("Failed to list knowledge bases");
  return res.json();
}

export async function createKB(
  id: string,
  name: string,
  description = ""
): Promise<CreateKBResponse> {
  const res = await fetch(`${API_BASE}/create_kb`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id, name, description }),
  });
  if (!res.ok) throw new Error("Failed to create knowledge base");
  return res.json();
}

export async function deleteKB(kbId: string): Promise<OperationResponse> {
  const safeKbId = encodeURIComponent(kbId);
  const res = await fetch(`${API_BASE}/delete_kb/${safeKbId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete knowledge base");
  return res.json();
}

export async function listDocs(kbId: string): Promise<ListDocsResponse> {
  const safeKbId = encodeURIComponent(kbId);
  const res = await fetch(`${API_BASE}/list_docs/${safeKbId}`);
  if (!res.ok) throw new Error("Failed to list documents");
  return res.json();
}

export async function deleteDoc(
  kbId: string,
  filename: string
): Promise<OperationResponse> {
  const safeKbId = encodeURIComponent(kbId);
  const safeFilename = encodeURIComponent(filename);
  const res = await fetch(`${API_BASE}/delete_doc/${safeKbId}/${safeFilename}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete document");
  return res.json();
}

export async function listChats(): Promise<ListChatsResponse> {
  const res = await fetch(`${API_BASE}/list_chats`);
  if (!res.ok) throw new Error("Failed to list chats");
  return res.json();
}

export async function getChat(
  conversationId: string
): Promise<GetChatResponse> {
  const safeConversationId = encodeURIComponent(conversationId);
  const res = await fetch(`${API_BASE}/get_chat/${safeConversationId}`);
  if (!res.ok) throw new Error("Failed to fetch chat");
  return res.json();
}

export async function deleteChat(
  conversationId: string
): Promise<OperationResponse> {
  const safeConversationId = encodeURIComponent(conversationId);
  const res = await fetch(`${API_BASE}/delete_chat/${safeConversationId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete chat");
  return res.json();
}

export async function retrieveChunks(
  question: string,
  sessionId: string,
  kbId: string
): Promise<RetrieveResponse> {
  const payload: RetrieveRequest = {
    question,
    session_id: sessionId,
    kb_id: kbId,
  };

  const res = await fetch(`${API_BASE}/retrieve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) throw new Error("Failed to retrieve chunks");
  return res.json();
}

export async function generateAnswer(
  question: string,
  sessionId: string,
  selectedChunks: GenerateRequest["selected_chunks"]
): Promise<GenerateResponse> {
  const payload: GenerateRequest = {
    question,
    session_id: sessionId,
    selected_chunks: selectedChunks,
  };

  const res = await fetch(`${API_BASE}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) throw new Error("Failed to generate answer");
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

export async function ingestDocuments(
  kbId: string
): Promise<IngestResponse> {
  const res = await fetch(`${API_BASE}/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ kb_id: kbId }),
  });

  if (!res.ok) throw new Error("Failed to ingest documents");
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


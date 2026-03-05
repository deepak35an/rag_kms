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

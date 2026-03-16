"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { askQuestion, createSession } from "@/app/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

interface KnowledgeBase {
  id: string;
  name: string;
  docCount: number;
}

interface Conversation {
  id: string;
  title: string;
  preview: string;
  messageCount: number;
  status: "active" | "archived";
  kbId: string;
  kbName: string;
  updatedAt: string;
  sessionId?: string;
}

const KB_STORAGE_KEY = "rag_knowledge_bases";
const CONVERSATIONS_KEY = "rag_conversations";
const ACTIVE_CONVERSATION_KEY = "rag_active_conversation_id";
const MSG_PREFIX = "rag_messages_";

function nowIso() {
  return new Date().toISOString();
}

function timeString() {
  return new Date().toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function welcomeMessage(): Message {
  return {
    id: `welcome-${Date.now()}`,
    role: "assistant",
    content:
      "Hello! I'm your AI assistant. Select a knowledge base and ask me anything about your uploaded documents.",
    timestamp: timeString(),
  };
}

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

function writeJSON<T>(key: string, value: T) {
  localStorage.setItem(key, JSON.stringify(value));
}

function initChatState() {
  const knowledgeBases = readJSON<KnowledgeBase[]>(KB_STORAGE_KEY, []);
  let conversations = readJSON<Conversation[]>(CONVERSATIONS_KEY, []);

  if (conversations.length === 0) {
    const defaultKb = knowledgeBases[0];
    const conv: Conversation = {
      id: `conv-${Date.now()}`,
      title: "New Conversation",
      preview: "",
      messageCount: 1,
      status: "active",
      kbId: defaultKb?.id ?? "",
      kbName: defaultKb?.name ?? "",
      updatedAt: nowIso(),
    };
    conversations = [conv];
    writeJSON(CONVERSATIONS_KEY, conversations);
    writeJSON(`${MSG_PREFIX}${conv.id}`, [welcomeMessage()]);
    localStorage.setItem(ACTIVE_CONVERSATION_KEY, conv.id);
  }

  const activeFromStorage = localStorage.getItem(ACTIVE_CONVERSATION_KEY);
  const currentConversationId =
    activeFromStorage && conversations.some((c) => c.id === activeFromStorage)
      ? activeFromStorage
      : conversations[0].id;

  localStorage.setItem(ACTIVE_CONVERSATION_KEY, currentConversationId);

  const currentConversation =
    conversations.find((c) => c.id === currentConversationId) ?? conversations[0];

  const messages = readJSON<Message[]>(
    `${MSG_PREFIX}${currentConversation.id}`,
    [welcomeMessage()]
  );

  if (!localStorage.getItem(`${MSG_PREFIX}${currentConversation.id}`)) {
    writeJSON(`${MSG_PREFIX}${currentConversation.id}`, messages);
  }

  return {
    knowledgeBases,
    conversations,
    currentConversationId: currentConversation.id,
    selectedKB: currentConversation.kbId || knowledgeBases[0]?.id || "",
    messages,
  };
}

export default function ChatPage() {
  const [boot] = useState(() => {
    if (typeof window === "undefined") {
      return {
        knowledgeBases: [] as KnowledgeBase[],
        conversations: [] as Conversation[],
        currentConversationId: "",
        selectedKB: "",
        messages: [welcomeMessage()] as Message[],
      };
    }
    return initChatState();
  });

  const [knowledgeBases] = useState<KnowledgeBase[]>(
    boot.knowledgeBases
  );
  const [conversations, setConversations] = useState<Conversation[]>(
    boot.conversations
  );
  const [currentConversationId, setCurrentConversationId] = useState<string>(
    boot.currentConversationId
  );
  const [selectedKB, setSelectedKB] = useState<string>(
    boot.selectedKB
  );
  const [messages, setMessages] = useState<Message[]>(boot.messages);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorText, setErrorText] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const currentConversation =
    conversations.find((c) => c.id === currentConversationId) ?? null;

  const selectedKBName =
    knowledgeBases.find((kb) => kb.id === selectedKB)?.name || "";

  const persistConversations = (nextConversations: Conversation[]) => {
    setConversations(nextConversations);
    writeJSON(CONVERSATIONS_KEY, nextConversations);
  };

  const persistMessages = (conversationId: string, nextMessages: Message[]) => {
    setMessages(nextMessages);
    writeJSON(`${MSG_PREFIX}${conversationId}`, nextMessages);
  };

  const switchConversation = (conversationId: string) => {
    const target = conversations.find((c) => c.id === conversationId);
    if (!target) return;

    setCurrentConversationId(conversationId);
    setSelectedKB(target.kbId || knowledgeBases[0]?.id || "");
    localStorage.setItem(ACTIVE_CONVERSATION_KEY, conversationId);

    const nextMessages = readJSON<Message[]>(`${MSG_PREFIX}${conversationId}`, [
      welcomeMessage(),
    ]);
    setMessages(nextMessages);
  };

  const createNewConversation = () => {
    const defaultKb = knowledgeBases.find((kb) => kb.id === selectedKB) || knowledgeBases[0];
    const conv: Conversation = {
      id: `conv-${Date.now()}`,
      title: "New Conversation",
      preview: "",
      messageCount: 1,
      status: "active",
      kbId: defaultKb?.id ?? "",
      kbName: defaultKb?.name ?? "",
      updatedAt: nowIso(),
    };

    const nextConversations = [conv, ...conversations];
    persistConversations(nextConversations);

    const nextMessages = [welcomeMessage()];
    writeJSON(`${MSG_PREFIX}${conv.id}`, nextMessages);

    setCurrentConversationId(conv.id);
    setSelectedKB(conv.kbId);
    setMessages(nextMessages);
    setInputValue("");
    setErrorText("");
    localStorage.setItem(ACTIVE_CONVERSATION_KEY, conv.id);
  };

  const updateConversationMeta = (
    conversationId: string,
    updater: (conv: Conversation) => Conversation
  ) => {
    const nextConversations = conversations.map((conv) =>
      conv.id === conversationId ? updater(conv) : conv
    );
    persistConversations(nextConversations);
  };

  const handleSend = async () => {
    if (!inputValue.trim() || !selectedKB || !currentConversationId) return;

    setErrorText("");
    const question = inputValue.trim();

    const userMsg: Message = {
      id: `msg-${Date.now()}`,
      role: "user",
      content: question,
      timestamp: timeString(),
    };

    const afterUser = [...messages, userMsg];
    persistMessages(currentConversationId, afterUser);
    setInputValue("");
    setIsLoading(true);

    try {
      let sessionId = currentConversation?.sessionId;

      if (!sessionId) {
        const session = await createSession();
        sessionId = session.session_id;
        updateConversationMeta(currentConversationId, (conv) => ({
          ...conv,
          sessionId,
        }));
      }

      const response = await askQuestion(question, sessionId);

      const sourceText = response.sources?.length
        ? `\n\nSources:\n${response.sources.map((s) => `• ${s}`).join("\n")}`
        : "";

      const assistantMsg: Message = {
        id: `msg-${Date.now()}-ai`,
        role: "assistant",
        content: `${response.answer || "No answer returned."}${sourceText}`,
        timestamp: timeString(),
      };

      const finalMessages = [...afterUser, assistantMsg];
      persistMessages(currentConversationId, finalMessages);

      const kbName = knowledgeBases.find((kb) => kb.id === selectedKB)?.name || "";
      updateConversationMeta(currentConversationId, (conv) => ({
        ...conv,
        kbId: selectedKB,
        kbName,
        title:
          conv.title === "New Conversation"
            ? question.slice(0, 48)
            : conv.title,
        preview: question,
        messageCount: finalMessages.length,
        status: "active",
        updatedAt: nowIso(),
      }));
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Failed to fetch response from backend.";
      setErrorText(message);

      const assistantMsg: Message = {
        id: `msg-${Date.now()}-err`,
        role: "assistant",
        content: `Sorry, I couldn't get a response. ${message}`,
        timestamp: timeString(),
      };

      const finalMessages = [...afterUser, assistantMsg];
      persistMessages(currentConversationId, finalMessages);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="mb-6 flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Ask Questions</h1>
          <p className="text-gray-500 mt-1 text-sm">
            Chat with your AI assistant powered by your knowledge base
          </p>
        </div>
        <button
          onClick={createNewConversation}
          className="flex items-center gap-2 bg-gray-900 hover:bg-gray-800 text-white text-sm font-medium px-4 py-2.5 rounded-lg transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Chat
        </button>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        {conversations.slice(0, 6).map((conv) => (
          <button
            key={conv.id}
            onClick={() => switchConversation(conv.id)}
            className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
              conv.id === currentConversationId
                ? "border-blue-600 bg-blue-50 text-blue-700"
                : "border-gray-200 bg-white text-gray-600 hover:bg-gray-50"
            }`}
          >
            {conv.title || "Conversation"}
          </button>
        ))}
        <Link
          href="/dashboard/history"
          className="text-xs px-3 py-1.5 rounded-lg border border-gray-200 bg-white text-gray-600 hover:bg-gray-50"
        >
          View all history
        </Link>
      </div>

      <div className="flex-1 flex flex-col bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden min-h-0">
        <div className="px-6 py-3 border-b border-gray-200 bg-gray-50">
          <h2 className="text-sm font-semibold text-gray-900">Conversation</h2>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                  msg.role === "assistant"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-300 text-gray-700"
                }`}
              >
                {msg.role === "assistant" ? "AI" : "U"}
              </div>

              <div className={`flex-1 max-w-2xl ${msg.role === "user" ? "text-right" : ""}`}>
                <div
                  className={`inline-block rounded-xl px-4 py-3 text-sm whitespace-pre-wrap ${
                    msg.role === "assistant"
                      ? "bg-gray-100 text-gray-900"
                      : "bg-blue-600 text-white"
                  }`}
                >
                  {msg.content}
                </div>
                <div className="text-xs text-gray-400 mt-1 px-1">{msg.timestamp}</div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-blue-600 text-white grid place-items-center shrink-0">
                AI
              </div>
              <div className="bg-gray-100 rounded-xl px-4 py-3 text-sm text-gray-500">
                Thinking...
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center gap-2 mb-3">
            <label className="text-xs font-medium text-gray-700">Knowledge Base:</label>
            <select
              value={selectedKB}
              onChange={(e) => setSelectedKB(e.target.value)}
              className="flex-1 text-xs px-3 py-1.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              {knowledgeBases.length === 0 ? (
                <option value="">No knowledge bases available</option>
              ) : (
                knowledgeBases.map((kb) => (
                  <option key={kb.id} value={kb.id}>
                    {kb.name} ({kb.docCount} documents)
                  </option>
                ))
              )}
            </select>
            {selectedKBName && (
              <span className="text-xs text-gray-600 px-2 py-1 bg-white rounded-md border border-gray-200">
                {selectedKBName}
              </span>
            )}
          </div>

          {errorText && (
            <p className="text-xs text-red-600 mb-2 bg-red-50 border border-red-100 rounded-md px-2 py-1.5">
              {errorText}
            </p>
          )}

          <div className="flex items-center gap-2">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Ask a question about your documents..."
              disabled={!selectedKB || isLoading}
              className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            <button
              onClick={handleSend}
              disabled={!inputValue.trim() || !selectedKB || isLoading}
              className="p-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

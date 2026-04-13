"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  createSession,
  generateAnswer,
  retrieveChunks,
  listKBs,
  saveChatHistory,
  type ChunkInfo,
} from "@/app/lib/api";

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

function markdownToPlainText(markdown: string) {
  if (!markdown) return "";

  return markdown
    .replace(/\r/g, "")
    .replace(/```[\s\S]*?```/g, (codeBlock) =>
      codeBlock
        .replace(/```[a-zA-Z0-9_-]*\n?/g, "")
        .replace(/```/g, "")
        .trim()
    )
    .replace(/`([^`]+)`/g, "$1")
    .replace(/!\[([^\]]*)\]\([^)]+\)/g, "$1")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, "$1")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/^>\s?/gm, "")
    .replace(/^\s*[-*+]\s+/gm, "• ")
    .replace(/^\s*\d+\.\s+/gm, "")
    .replace(/^\|\s*[-:|\s]+\|$/gm, "")
    .replace(/^\|(.+)\|$/gm, (_, row: string) =>
      row
        .split("|")
        .map((cell) => cell.trim())
        .filter(Boolean)
        .join("  ")
    )
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/__(.*?)__/g, "$1")
    .replace(/~~(.*?)~~/g, "$1")
    .replace(/<[^>]+>/g, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

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

function mapKbFromServer(kb: {
  id: string;
  name: string;
  doc_count: number;
}): KnowledgeBase {
  return {
    id: kb.id,
    name: kb.name,
    docCount: kb.doc_count ?? 0,
  };
}

export default function ChatPage() {
  const router = useRouter();
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string>("");
  const [selectedKB, setSelectedKB] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorText, setErrorText] = useState("");

  const [candidateChunks, setCandidateChunks] = useState<ChunkInfo[]>([]);
  const [selectedChunkIds, setSelectedChunkIds] = useState<string[]>([]);
  const [isChunksPanelCollapsed, setIsChunksPanelCollapsed] = useState(false);
  const [pendingQuestion, setPendingQuestion] = useState("");
  const [pendingSessionId, setPendingSessionId] = useState("");
  const [isRetrieving, setIsRetrieving] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const streamIntervalRef = useRef<number | null>(null);
  const hydrationDoneRef = useRef(false);

  const isBusy = isLoading || isRetrieving || isGenerating;

  const toggleChunkSelection = (chunkId: string) => {
    setSelectedChunkIds((prev) =>
      prev.includes(chunkId)
        ? prev.filter((id) => id !== chunkId)
        : [...prev, chunkId]
    );
  };

  const selectAllChunks = () => {
    setSelectedChunkIds(candidateChunks.map((chunk) => chunk.id));
  };

  const clearChunkSelection = () => {
    setSelectedChunkIds([]);
  };

  const streamAssistantMessage = (
    conversationId: string,
    messageId: string,
    fullText: string,
    seedMessages: Message[]
  ) =>
    new Promise<Message[]>((resolve) => {
      const textToStream = fullText || "No answer returned.";
      const textLength = textToStream.length;

      if (textLength === 0) {
        resolve(seedMessages);
        return;
      }

      if (streamIntervalRef.current !== null) {
        window.clearInterval(streamIntervalRef.current);
        streamIntervalRef.current = null;
      }

      let cursor = 0;
      const step =
        textLength > 2800
          ? 20
          : textLength > 1600
          ? 14
          : textLength > 900
          ? 10
          : 6;

      const pushFrame = () => {
        cursor = Math.min(textLength, cursor + step);

        const streamedMessages = seedMessages.map((message) =>
          message.id === messageId
            ? { ...message, content: textToStream.slice(0, cursor) }
            : message
        );

        setMessages(streamedMessages);

        if (cursor >= textLength) {
          if (streamIntervalRef.current !== null) {
            window.clearInterval(streamIntervalRef.current);
            streamIntervalRef.current = null;
          }
          // Keep local cache in sync with final streamed content
          writeJSON(`${MSG_PREFIX}${conversationId}`, streamedMessages);
          resolve(streamedMessages);
        }
      };

      pushFrame();
      streamIntervalRef.current = window.setInterval(pushFrame, 18);
    });

  useEffect(() => {
    if (hydrationDoneRef.current) return;
    hydrationDoneRef.current = true;

    const state = initChatState();
    setKnowledgeBases(state.knowledgeBases);
    setConversations(state.conversations);
    setCurrentConversationId(state.currentConversationId);
    setSelectedKB(state.selectedKB);
    setMessages(state.messages);
  }, []);

  useEffect(() => {
    let cancelled = false;

    const loadKnowledgeBases = async () => {
      try {
        const response = await listKBs();
        if (response.status !== "success") return;

        const serverKBs = (response.knowledge_bases ?? []).map(mapKbFromServer);
        if (cancelled) return;

        setKnowledgeBases(serverKBs);
        writeJSON(KB_STORAGE_KEY, serverKBs);

        setSelectedKB((prev) => {
          if (prev && serverKBs.some((kb) => kb.id === prev)) return prev;
          return serverKBs[0]?.id || "";
        });
      } catch {
        // Keep local cache fallback
      }
    };

    void loadKnowledgeBases();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    return () => {
      if (streamIntervalRef.current !== null) {
        window.clearInterval(streamIntervalRef.current);
      }
    };
  }, []);

  const currentConversation =
    conversations.find((c) => c.id === currentConversationId) ?? null;

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
    setCandidateChunks([]);
    setSelectedChunkIds([]);
    setIsChunksPanelCollapsed(false);
    setPendingQuestion("");
    setPendingSessionId("");
    setIsRetrieving(false);
    setIsGenerating(false);
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
    setCandidateChunks([]);
    setSelectedChunkIds([]);
    setIsChunksPanelCollapsed(false);
    setPendingQuestion("");
    setPendingSessionId("");
    setIsRetrieving(false);
    setIsGenerating(false);
    setInputValue("");
    setErrorText("");
    localStorage.setItem(ACTIVE_CONVERSATION_KEY, conv.id);
  };

  const updateConversationMeta = (
    conversationId: string,
    updater: (conv: Conversation) => Conversation,
    msgsToSync?: Message[]
  ) => {
    const nextConversations = conversations.map((conv) =>
      conv.id === conversationId ? updater(conv) : conv
    );
    persistConversations(nextConversations);

    if (msgsToSync) {
      const meta = nextConversations.find((c) => c.id === conversationId);
      if (meta) {
        saveChatHistory(
          conversationId,
          meta as unknown as Record<string, unknown>,
          msgsToSync as unknown as Record<string, unknown>[]
        ).catch((e) => console.error("Failed to sync chat to backend:", e));
      }
    }
  };

  const handleSend = async () => {
    if (
      isLoading ||
      isRetrieving ||
      isGenerating ||
      !inputValue.trim() ||
      !selectedKB ||
      !currentConversationId
    ) {
      return;
    }

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
    setCandidateChunks([]);
    setSelectedChunkIds([]);
    setIsChunksPanelCollapsed(false);
    setPendingQuestion(question);
    setPendingSessionId("");
    setIsLoading(true);
    setIsRetrieving(true);

    const kbName = knowledgeBases.find((kb) => kb.id === selectedKB)?.name || "";
    updateConversationMeta(
      currentConversationId,
      (conv) => ({
        ...conv,
        kbId: selectedKB,
        kbName,
        title: conv.title === "New Conversation" ? question.slice(0, 48) : conv.title,
        preview: question,
        messageCount: afterUser.length,
        status: "active",
        updatedAt: nowIso(),
      }),
      afterUser
    );

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

      setPendingSessionId(sessionId);

      const response = await retrieveChunks(question, sessionId, selectedKB);
      const sortedChunks = [...(response.chunks ?? [])].sort(
        (a, b) =>
          (b.metadata?.relevance_score ?? 0) - (a.metadata?.relevance_score ?? 0)
      );

      if (sortedChunks.length === 0) {
        const noChunksMsg: Message = {
          id: `msg-${Date.now()}-no-chunks`,
          role: "assistant",
          content:
            "I could not find relevant chunks for that question in the selected knowledge base. Try rephrasing your question or switching the knowledge base.",
          timestamp: timeString(),
        };

        const finalMessages = [...afterUser, noChunksMsg];
        persistMessages(currentConversationId, finalMessages);

        updateConversationMeta(
          currentConversationId,
          (conv) => ({
            ...conv,
            kbId: selectedKB,
            kbName,
            title: conv.title === "New Conversation" ? question.slice(0, 48) : conv.title,
            preview: question,
            messageCount: finalMessages.length,
            status: "active",
            updatedAt: nowIso(),
          }),
          finalMessages
        );

        setCandidateChunks([]);
        setSelectedChunkIds([]);
        setIsChunksPanelCollapsed(false);
        setPendingQuestion("");
        setPendingSessionId("");
        return;
      }

      setCandidateChunks(sortedChunks);
      setIsChunksPanelCollapsed(false);

      const defaultSelection = sortedChunks
        .filter((chunk) => (chunk.metadata?.relevance_score ?? 0) >= 0.7)
        .map((chunk) => chunk.id);

      setSelectedChunkIds(
        defaultSelection.length > 0
          ? defaultSelection
          : sortedChunks.slice(0, Math.min(3, sortedChunks.length)).map((chunk) => chunk.id)
      );
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

      updateConversationMeta(
        currentConversationId,
        (conv) => ({
          ...conv,
          kbId: selectedKB,
          kbName,
          messageCount: finalMessages.length,
          updatedAt: nowIso(),
        }),
        finalMessages
      );
    } finally {
      setIsRetrieving(false);
      setIsLoading(false);
    }
  };

  const handleGenerateFromSelection = async () => {
    if (!pendingQuestion || !pendingSessionId || !currentConversationId || isGenerating) {
      return;
    }

    if (selectedChunkIds.length === 0) {
      setErrorText("Please select at least one chunk before generating an answer.");
      return;
    }

    setErrorText("");
    setIsGenerating(true);

    try {
      const selectedChunks = candidateChunks
        .filter((chunk) => selectedChunkIds.includes(chunk.id))
        .map((chunk) => ({
          content: chunk.content,
          metadata: chunk.metadata,
        }));

      if (selectedChunks.length === 0) {
        throw new Error("No valid chunk selection found. Please reselect chunks and try again.");
      }

      const response = await generateAnswer(
        pendingQuestion,
        pendingSessionId,
        selectedChunks
      );

      const plainAnswer = markdownToPlainText(
        response.answer || "No answer returned."
      );
      const plainSources = (response.sources ?? [])
        .map((source) => markdownToPlainText(String(source)))
        .filter((source) => source.length > 0);

      const sourceText = plainSources.length
        ? `\n\nSources:\n${plainSources.map((s) => `• ${s}`).join("\n")}`
        : "";

      const finalAssistantContent = `${plainAnswer}${sourceText}`.trim();

      const assistantMsgId = `msg-${Date.now()}-ai`;
      const assistantSeed: Message = {
        id: assistantMsgId,
        role: "assistant",
        content: "",
        timestamp: timeString(),
      };

      const seedMessages = [...messages, assistantSeed];
      setMessages(seedMessages);

      const finalMessages = await streamAssistantMessage(
        currentConversationId,
        assistantMsgId,
        finalAssistantContent,
        seedMessages
      );
      persistMessages(currentConversationId, finalMessages);

      const kbName = knowledgeBases.find((kb) => kb.id === selectedKB)?.name || "";
      updateConversationMeta(
        currentConversationId,
        (conv) => ({
          ...conv,
          kbId: selectedKB,
          kbName,
          title:
            conv.title === "New Conversation"
              ? pendingQuestion.slice(0, 48)
              : conv.title,
          preview: pendingQuestion,
          messageCount: finalMessages.length,
          status: "active",
          updatedAt: nowIso(),
        }),
        finalMessages
      );

      setCandidateChunks([]);
      setSelectedChunkIds([]);
      setIsChunksPanelCollapsed(false);
      setPendingQuestion("");
      setPendingSessionId("");
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Failed to generate answer from selected chunks.";
      setErrorText(message);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="flex flex-col h-full w-full max-w-7xl mx-auto">
      <div className="mb-6 flex items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Ask Questions</h1>
          <p className="text-gray-500 mt-2 text-base">
            Chat with your AI assistant powered by your knowledge base
          </p>
        </div>
        <button
          onClick={createNewConversation}
          className="flex items-center gap-2 bg-gray-900 hover:bg-gray-800 text-white text-base font-medium px-5 py-3 rounded-xl transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Chat
        </button>
      </div>

      <div className="mb-5 flex flex-wrap gap-3">
        {conversations.slice(0, 6).map((conv) => (
          <button
            key={conv.id}
            onClick={() => switchConversation(conv.id)}
            className={`text-sm px-4 py-2 rounded-xl border transition-colors ${
              conv.id === currentConversationId
                ? "border-[#d8c183] bg-[#f6f0df] text-[#816a35] dark:border-[#524123] dark:bg-[#3b3018]/70 dark:text-[#e6cf97]"
                : "border-gray-200 bg-white text-gray-600 hover:bg-gray-50"
            }`}
          >
            {conv.title || "Conversation"}
          </button>
        ))}
        <button
          onClick={() => router.push("/dashboard/history")}
          className="text-sm px-4 py-2 rounded-xl border border-gray-200 bg-white text-gray-600 hover:bg-gray-50 transition-colors"
        >
          View all history
        </button>
      </div>

      <div className="flex-1 flex flex-col bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden min-h-0">
        <div className="px-8 py-4 border-b border-gray-200 bg-gray-50">
          <h2 className="text-base font-semibold text-gray-900">Conversation</h2>
        </div>

        <div className="flex-1 overflow-y-auto p-8 space-y-6">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
            >
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${
                  msg.role === "assistant"
                    ? "bg-[#b79a52] text-white"
                    : "bg-gray-300 text-gray-700"
                }`}
              >
                {msg.role === "assistant" ? (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                  </svg>
                ) : (
                  <span className="font-medium text-base">U</span>
                )}
              </div>

              <div className={`flex-1 max-w-4xl ${msg.role === "user" ? "text-right" : ""}`}>
                <div
                  className={`inline-block rounded-2xl px-5 py-4 text-base whitespace-pre-wrap ${
                    msg.role === "assistant"
                      ? "bg-gray-100 text-gray-900"
                      : "bg-[#b79a52] text-white"
                  }`}
                >
                  {msg.content}
                </div>
                <div className="text-sm text-gray-400 mt-2 px-2">{msg.timestamp}</div>
              </div>
            </div>
          ))}

          {(isLoading || isRetrieving || isGenerating) && (
            <div className="flex gap-4">
              <div className="w-10 h-10 rounded-full bg-[#b79a52] text-white flex items-center justify-center shrink-0">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                </svg>
              </div>
              <div className="bg-gray-100 rounded-2xl px-5 py-4 text-base text-gray-500">
                {isGenerating
                  ? "Generating answer from selected chunks..."
                  : isRetrieving
                  ? "Retrieving relevant chunks..."
                  : "Thinking..."}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="p-6 border-t border-gray-100 bg-white">
          {candidateChunks.length > 0 && (
            <div className="mb-4 rounded-xl border border-[#dbc892] bg-white px-4 py-4 text-sm text-[#816a35] dark:border-[#524123] dark:bg-zinc-900 dark:text-[#e6cf97]">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="font-semibold">
                  Review retrieved chunks · {selectedChunkIds.length}/{candidateChunks.length} selected
                </p>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setIsChunksPanelCollapsed((prev) => !prev)}
                    aria-expanded={!isChunksPanelCollapsed}
                    className="inline-flex items-center gap-1.5 rounded-md border border-[#dbc892] bg-[#f6f0df] px-2.5 py-1 text-[#816a35] hover:bg-[#ebdfbf] dark:border-[#524123] dark:bg-[#3b3018]/60 dark:text-[#e6cf97] dark:hover:bg-[#3b3018]"
                  >
                    <svg
                      className={`w-4 h-4 transition-transform ${isChunksPanelCollapsed ? "rotate-180" : ""}`}
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path
                        fillRule="evenodd"
                        d="M5.23 12.21a.75.75 0 001.06.02L10 8.915l3.71 3.315a.75.75 0 101-1.12l-4.21-3.75a.75.75 0 00-1 0l-4.21 3.75a.75.75 0 00-.06 1.06z"
                        clipRule="evenodd"
                      />
                    </svg>
                    {isChunksPanelCollapsed ? "Expand" : "Collapse"}
                  </button>

                  {!isChunksPanelCollapsed && (
                    <>
                      <button
                        type="button"
                        onClick={selectAllChunks}
                        className="rounded-md border border-[#dbc892] bg-[#f6f0df] px-2.5 py-1 text-[#816a35] hover:bg-[#ebdfbf] dark:border-[#524123] dark:bg-[#3b3018]/60 dark:text-[#e6cf97] dark:hover:bg-[#3b3018]"
                      >
                        Select all
                      </button>
                      <button
                        type="button"
                        onClick={clearChunkSelection}
                        className="px-2.5 py-1 rounded-md border border-gray-200 text-gray-600 bg-white hover:bg-gray-50"
                      >
                        Clear
                      </button>
                    </>
                  )}
                </div>
              </div>

              {!isChunksPanelCollapsed && (
                <>
                  {pendingQuestion && <p className="mt-1 text-xs text-[#816a35] dark:text-[#d9bf84]">Question: {pendingQuestion}</p>}

                  <div className="mt-3 max-h-64 overflow-y-auto space-y-2.5 pr-1">
                    {candidateChunks.map((chunk) => {
                      const selected = selectedChunkIds.includes(chunk.id);
                      return (
                        <label
                          key={chunk.id}
                          className={`block rounded-lg border p-3 cursor-pointer transition-colors ${
                            selected
                              ? "border-[#c3a968] bg-[#f6f0df] dark:border-[#816a35] dark:bg-[#3b3018]/50"
                              : "border-gray-200 bg-white hover:border-[#d8c183] dark:border-zinc-700 dark:bg-zinc-900 dark:hover:border-[#816a35]"
                          }`}
                        >
                          <div className="flex items-start gap-3">
                            <input
                              type="checkbox"
                              checked={selected}
                              onChange={() => toggleChunkSelection(chunk.id)}
                              className="mt-0.5"
                            />

                            <div className="min-w-0 flex-1">
                              <div className="flex flex-wrap items-center gap-2 text-[11px] text-[#816a35] dark:text-[#e6cf97]">
                                <span className="rounded-full border border-[#dbc892] bg-white px-2 py-0.5 dark:border-[#524123] dark:bg-zinc-900">
                                  {chunk.metadata?.source || "Unknown source"}
                                </span>
                                <span className="rounded-full border border-[#dbc892] bg-white px-2 py-0.5 dark:border-[#524123] dark:bg-zinc-900">
                                  Page {chunk.metadata?.page ?? "?"}
                                </span>
                                <span className="rounded-full border border-[#dbc892] bg-white px-2 py-0.5 dark:border-[#524123] dark:bg-zinc-900">
                                  Score {(chunk.metadata?.relevance_score ?? 0).toFixed(3)}
                                </span>
                              </div>

                              <p className="mt-2 text-xs text-gray-800 line-clamp-3 leading-relaxed">
                                {chunk.content}
                              </p>
                            </div>
                          </div>
                        </label>
                      );
                    })}
                  </div>

                  <div className="mt-3 flex items-center justify-between gap-2">
                    {pendingSessionId ? (
                      <p className="text-xs text-gray-500 truncate">Session: {pendingSessionId}</p>
                    ) : (
                      <span />
                    )}
                    <button
                      onClick={handleGenerateFromSelection}
                      disabled={selectedChunkIds.length === 0 || isGenerating}
                      className="rounded-lg bg-[#b79a52] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[#a48745] disabled:cursor-not-allowed disabled:bg-gray-300 dark:disabled:bg-zinc-700"
                    >
                      {isGenerating
                        ? "Generating answer..."
                        : `Generate answer (${selectedChunkIds.length} chunk${
                            selectedChunkIds.length === 1 ? "" : "s"
                          })`}
                    </button>
                  </div>
                </>
              )}
            </div>
          )}

          <div className="flex items-center gap-3 mb-4 bg-gray-50 px-5 py-3 rounded-xl border border-gray-100">
            <svg className="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 01-.825-.242m9.345-8.334a2.126 2.126 0 00-.476-.095 48.64 48.64 0 00-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0011.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155" />
            </svg>
            <label className="text-base font-medium text-gray-700">Knowledge Base:</label>
            <select
              value={selectedKB}
              onChange={(e) => setSelectedKB(e.target.value)}
              className="flex-1 text-base bg-transparent border-0 focus:ring-0 text-gray-900 cursor-pointer font-medium"
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
          </div>

          {errorText && (
            <p className="text-sm text-red-600 mb-4 bg-red-50 border border-red-100 rounded-xl px-4 py-3">
              {errorText}
            </p>
          )}

          <div className="flex items-center gap-3 rounded-2xl border border-gray-300 bg-white p-3 shadow-sm transition-all focus-within:border-[#b79a52] focus-within:ring-2 focus-within:ring-[#b79a52]/30">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !isBusy) {
                  handleSend();
                }
              }}
              placeholder="Ask a question to retrieve candidate chunks..."
              disabled={!selectedKB}
              className="flex-1 px-5 py-3 bg-transparent text-lg focus:outline-none disabled:cursor-not-allowed text-gray-900 placeholder-gray-500"
            />
            <button
              onClick={handleSend}
              disabled={!inputValue.trim() || !selectedKB || isBusy}
              className="inline-flex items-center gap-2 rounded-xl bg-[#b79a52] px-4 py-3 text-white transition-colors hover:bg-[#a48745] disabled:cursor-not-allowed disabled:bg-gray-200 disabled:text-gray-400"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
              </svg>
              <span className="text-sm font-medium">
                {isRetrieving ? "Retrieving..." : "Retrieve chunks"}
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

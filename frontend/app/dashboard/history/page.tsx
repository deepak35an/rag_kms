"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

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

const CONVERSATIONS_KEY = "rag_conversations";
const ACTIVE_CONVERSATION_KEY = "rag_active_conversation_id";
const MSG_PREFIX = "rag_messages_";

function readConversations(): Conversation[] {
  if (typeof window === "undefined") return [];
  const raw = localStorage.getItem(CONVERSATIONS_KEY);
  if (!raw) return [];
  try {
    return JSON.parse(raw) as Conversation[];
  } catch {
    return [];
  }
}

function formatDate(iso?: string) {
  if (!iso) return "-";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export default function HistoryPage() {
  const [conversations, setConversations] = useState<Conversation[]>(() =>
    readConversations()
  );
  const [searchQuery, setSearchQuery] = useState("");
  const router = useRouter();

  const persist = (next: Conversation[]) => {
    setConversations(next);
    localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(next));
  };

  const handleDelete = (id: string) => {
    const next = conversations.filter((c) => c.id !== id);
    persist(next);
    localStorage.removeItem(`${MSG_PREFIX}${id}`);

    const active = localStorage.getItem(ACTIVE_CONVERSATION_KEY);
    if (active === id) {
      if (next[0]?.id) {
        localStorage.setItem(ACTIVE_CONVERSATION_KEY, next[0].id);
      } else {
        localStorage.removeItem(ACTIVE_CONVERSATION_KEY);
      }
    }
  };

  const openConversation = (id: string) => {
    localStorage.setItem(ACTIVE_CONVERSATION_KEY, id);
  };

  const filteredConversations = useMemo(() => {
    const needle = searchQuery.trim().toLowerCase();
    const base = [...conversations].sort((a, b) =>
      (b.updatedAt || "").localeCompare(a.updatedAt || "")
    );

    if (!needle) return base;

    return base.filter(
      (conv) =>
        conv.title.toLowerCase().includes(needle) ||
        conv.preview.toLowerCase().includes(needle) ||
        conv.kbName.toLowerCase().includes(needle)
    );
  }, [conversations, searchQuery]);

  return (
    <div className="w-full max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Chat History</h1>
          <p className="text-gray-500 mt-2 text-base">
            View and manage your previous conversations
          </p>
        </div>
        <Link
          href="/dashboard/chat"
          className="flex items-center gap-2 bg-gray-900 hover:bg-gray-800 text-white text-base font-medium px-5 py-3 rounded-xl transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Chat
        </Link>
      </div>

      <div className="mb-8">
        <div className="relative">
          <svg
            className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search conversations..."
            className="w-full pl-12 pr-5 py-4 bg-gray-50 border border-gray-200 rounded-xl text-base text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-colors"
          />
        </div>
      </div>

      <div className="mb-5">
        <h2 className="text-lg font-semibold text-gray-900">
          {filteredConversations.length} Conversation
          {filteredConversations.length !== 1 ? "s" : ""}
        </h2>
      </div>

      {filteredConversations.length === 0 ? (
        <div className="text-center py-20 text-gray-400 bg-white border border-gray-200 rounded-2xl">
          <svg
            className="w-14 h-14 mx-auto mb-4 opacity-40"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 01-.825-.242"
            />
          </svg>
          <p className="font-medium text-lg">No conversations found</p>
          <p className="text-base mt-2">
            {searchQuery
              ? "Try a different search"
              : "Start a new chat to create your first conversation"}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredConversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => {
                openConversation(conv.id);
                router.push("/dashboard/chat");
              }}
              className="bg-white rounded-2xl border border-gray-200 p-6 hover:shadow-md hover:border-blue-300 cursor-pointer transition-all flex items-start justify-between group"
            >
              <div className="flex items-start gap-5 flex-1 min-w-0 pr-5">
                <div className="w-14 h-14 bg-blue-50 rounded-xl flex items-center justify-center shrink-0 text-blue-600 group-hover:bg-blue-100 transition-colors">
                  <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 01-.825-.242m9.345-8.334a2.126 2.126 0 00-.476-.095 48.64 48.64 0 00-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0011.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155" />
                  </svg>
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-4 mb-2">
                    <h3 className="font-semibold text-gray-900 text-xl group-hover:text-blue-600 transition-colors">
                      {conv.title || "Conversation"}
                    </h3>
                    {conv.status === "active" && (
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-900 text-white">
                        active
                      </span>
                    )}
                  </div>
                  <p className="text-base text-gray-600 mb-4 line-clamp-1">
                    {conv.preview || "No preview available"}
                  </p>
                  <div className="flex items-center gap-5 text-sm text-gray-400">
                    <span className="flex items-center gap-1.5">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
                      {conv.messageCount} messages
                    </span>
                    <span className="flex items-center gap-1.5">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                      {formatDate(conv.updatedAt)}
                    </span>
                    {conv.kbName && (
                      <span className="px-3 py-1 rounded-md bg-gray-100 text-gray-600">
                        {conv.kbName}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4 shrink-0 self-center">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(conv.id);
                    }}
                    className="p-3 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100"
                    title="Delete conversation"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.5}
                        d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79"
                      />
                    </svg>
                  </button>
                </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

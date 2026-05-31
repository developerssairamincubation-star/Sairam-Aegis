"use client";

import { ArrowUp } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { createChat, deleteChat, listChats, listMessages, streamMessage } from "@/lib/api";
import { Conversation, Message, Source } from "@/types";

export default function ChatPage() {
  const [search, setSearch] = useState("");
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    listChats()
      .then(setConversations)
      .catch((err) => setError(err.message));
  }, []);

  const hasMessages = messages.length > 0;
  const recents = useMemo(() => conversations.slice(0, 12), [conversations]);

  function resetChat() {
    setActiveChatId(null);
    setMessages([]);
    setDraft("");
    setError("");
  }

  async function openChat(chatId: string) {
    setError("");
    setActiveChatId(chatId);
    try {
      const loaded = await listMessages(chatId);
      setMessages(loaded);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to open chat.");
    }
  }

  async function ensureChat() {
    if (activeChatId) return activeChatId;
    const conversation = await createChat({ title: "New chat" });
    setConversations((current) => [conversation, ...current]);
    setActiveChatId(conversation.id);
    return conversation.id;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const content = draft.trim();
    if (!content || isStreaming) return;

    setError("");
    setDraft("");
    setIsStreaming(true);

    const tempUserMessage: Message = {
      id: `user-${Date.now()}`,
      conversation_id: activeChatId || "pending",
      role: "user",
      content,
    };
    const tempAssistantMessage: Message = {
      id: `assistant-${Date.now()}`,
      conversation_id: activeChatId || "pending",
      role: "assistant",
      content: "",
      sources: [],
    };
    setMessages((current) => [...current, tempUserMessage, tempAssistantMessage]);

    try {
      const chatId = await ensureChat();
      let assistantContent = "";
      let assistantSources: Source[] = [];

      await streamMessage(chatId, content, {
        onToken: (token) => {
          assistantContent += token;
          setMessages((current) =>
            current.map((message) =>
              message.id === tempAssistantMessage.id
                ? { ...message, conversation_id: chatId, content: assistantContent }
                : message.id === tempUserMessage.id
                  ? { ...message, conversation_id: chatId }
                  : message,
            ),
          );
        },
        onSources: (sources) => {
          assistantSources = sources;
          setMessages((current) =>
            current.map((message) =>
              message.id === tempAssistantMessage.id ? { ...message, sources } : message,
            ),
          );
        },
        onDone: () => {
          setIsStreaming(false);
          setMessages((current) =>
            current.map((message) =>
              message.id === tempAssistantMessage.id
                ? { ...message, sources: assistantSources }
                : message,
            ),
          );
          listChats().then(setConversations).catch(() => undefined);
        },
        onError: (message) => {
          setIsStreaming(false);
          setError(message);
        },
      });
    } catch (err) {
      setIsStreaming(false);
      setError(err instanceof Error ? err.message : "Unable to send message.");
    }
  }

  async function handleDeleteChat(chatId: string) {
    setError("");
    try {
      await deleteChat(chatId);
      setConversations((current) => current.filter((chat) => chat.id !== chatId));
      if (activeChatId === chatId) {
        resetChat();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete chat.");
    }
  }

  return (
    <AppShell
      active="chat"
      recents={recents}
      search={search}
      onSearch={setSearch}
      onNewChat={resetChat}
      onOpenChat={openChat}
      onDeleteChat={handleDeleteChat}
    >
      <div className={`chat-page ${hasMessages ? "with-thread" : ""}`}>
        {!hasMessages ? (
          <section className="chat-empty" aria-label="New chat">
            <h1>Hello! Sairamite</h1>
            <p>Where should we begin?</p>
          </section>
        ) : (
          <section className="message-thread" aria-label="Conversation">
            {messages.map((message) => (
              <article key={message.id} className={`message-bubble ${message.role}`}>
                <p>{message.content || (message.role === "assistant" ? "Thinking..." : "")}</p>
                {message.role === "assistant" && message.sources?.length ? (
                  <div className="sources">
                    {message.sources.slice(0, 3).map((source) => (
                      <span key={source.chunk_id || source.source}>{source.source}</span>
                    ))}
                  </div>
                ) : null}
              </article>
            ))}
          </section>
        )}

        <form className="composer" onSubmit={handleSubmit}>
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                event.currentTarget.form?.requestSubmit();
              }
            }}
            placeholder="How can i help you today?"
            rows={3}
          />
          <div className="composer-actions">
            <button className="send-button" type="submit" aria-label="Send message" disabled={!draft.trim()}>
              <ArrowUp size={18} />
            </button>
          </div>
        </form>
        {error ? <p className="inline-error">{error}</p> : null}
      </div>
    </AppShell>
  );
}

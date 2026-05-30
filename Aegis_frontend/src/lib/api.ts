import { Conversation, Message, Project, Source } from "@/types";
import { getStoredUserId } from "@/lib/localAuth";
import { requiredEnv } from "@/lib/env";

const API_BASE_URL = requiredEnv(
  "NEXT_PUBLIC_API_BASE_URL",
  process.env.NEXT_PUBLIC_API_BASE_URL,
);
const PREVIEW_MODE = process.env.NEXT_PUBLIC_AUTH_PREVIEW_MODE === "true";

function requireUserId() {
  if (PREVIEW_MODE) return "preview-user";
  const userId = getStoredUserId();
  if (!userId) {
    throw new Error("You are not signed in.");
  }
  return userId;
}

function withUserId(path: string) {
  const userId = requireUserId();
  const url = new URL(`${API_BASE_URL}${path}`);
  url.searchParams.set("user_id", userId);
  return url.toString();
}

async function fetchJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(withUserId(path), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers || {}),
    },
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "Request failed.");
  }
  return response.json() as Promise<T>;
}

export function listProjects() {
  if (PREVIEW_MODE) return Promise.resolve<Project[]>([]);
  return fetchJson<Project[]>("/projects");
}

export function createProject(input: { name: string; description?: string }) {
  if (PREVIEW_MODE) {
    return Promise.resolve<Project>({
      id: crypto.randomUUID(),
      user_id: "preview-user",
      name: input.name,
      description: input.description,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });
  }
  return fetchJson<Project>("/projects", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function listChats() {
  if (PREVIEW_MODE) return Promise.resolve<Conversation[]>([]);
  return fetchJson<Conversation[]>("/chats");
}

export function createChat(input: { title?: string; project_id?: string | null }) {
  if (PREVIEW_MODE) {
    return Promise.resolve<Conversation>({
      id: crypto.randomUUID(),
      user_id: "preview-user",
      project_id: input.project_id,
      title: input.title || "New chat",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });
  }
  return fetchJson<Conversation>("/chats", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function listMessages(chatId: string) {
  if (PREVIEW_MODE) return Promise.resolve<Message[]>([]);
  return fetchJson<Message[]>(`/chats/${chatId}/messages`);
}

export async function deleteChat(chatId: string) {
  if (PREVIEW_MODE) return;
  const response = await fetch(withUserId(`/chats/${chatId}`), {
    method: "DELETE",
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "Request failed.");
  }
}

type StreamHandlers = {
  onToken: (token: string) => void;
  onSources: (sources: Source[]) => void;
  onDone: () => void;
  onError: (message: string) => void;
};

function parseEvent(raw: string) {
  const event = raw
    .split("\n")
    .find((line) => line.startsWith("event:"))
    ?.replace("event:", "")
    .trim();
  const data = raw
    .split("\n")
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.replace("data:", "").trim())
    .join("\n");
  return { event, data };
}

export async function streamMessage(chatId: string, content: string, handlers: StreamHandlers) {
  if (PREVIEW_MODE) {
    handlers.onSources([]);
    for (const token of [
      "Preview mode is ready. ",
      "Connect Supabase, LM Studio, and the backend to stream real RAG answers.",
    ]) {
      handlers.onToken(token);
      await new Promise((resolve) => window.setTimeout(resolve, 120));
    }
    handlers.onDone();
    return;
  }

  const response = await fetch(withUserId(`/chats/${chatId}/messages/stream`), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ content }),
  });

  if (!response.ok || !response.body) {
    handlers.onError(await response.text());
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() || "";

    for (const rawEvent of events) {
      const { event, data } = parseEvent(rawEvent);
      if (!event) continue;
      const parsed = data ? JSON.parse(data) : null;
      if (event === "token") handlers.onToken(parsed as string);
      if (event === "sources") handlers.onSources(parsed as Source[]);
      if (event === "done") handlers.onDone();
      if (event === "error") handlers.onError(parsed?.message || "Streaming failed.");
    }
  }
}

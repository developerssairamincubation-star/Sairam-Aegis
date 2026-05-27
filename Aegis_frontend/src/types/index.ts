export type Project = {
  id: string;
  user_id: string;
  name: string;
  description?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type Conversation = {
  id: string;
  user_id: string;
  project_id?: string | null;
  title: string;
  created_at?: string | null;
  updated_at?: string | null;
};

export type Message = {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  sources?: Source[];
  created_at?: string | null;
};

export type Source = {
  source?: string | null;
  title?: string | null;
  chunk_id?: string | null;
  score?: number | null;
};

"use client";

import {
  FolderOpen,
  MessageSquarePlus,
  Search,
  Settings,
  Trash2,
  UserCircle,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Conversation } from "@/types";
import { clearStoredUserId } from "@/lib/localAuth";

type SidebarProps = {
  active: "chat" | "projects";
  recents: Conversation[];
  search: string;
  onSearch: (value: string) => void;
  onNewChat?: () => void;
  onOpenChat?: (chatId: string) => void;
  onDeleteChat?: (chatId: string) => void;
};

export function Sidebar({
  active,
  recents,
  search,
  onSearch,
  onNewChat,
  onOpenChat,
  onDeleteChat,
}: SidebarProps) {
  const router = useRouter();
  const [showSettings, setShowSettings] = useState(false);

  function handleNewChat() {
    onNewChat?.();
    router.push("/chat");
  }

  function handleLogout() {
    clearStoredUserId();
    setShowSettings(false);
    router.push("/login");
  }

  function formatRecentTitle(title: string) {
    const words = title.trim().split(/\s+/).filter(Boolean);
    if (words.length <= 3) return title;
    return `${words.slice(0, 3).join(" ")}...`;
  }

  const filteredRecents = recents.filter((chat) =>
    chat.title.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark" aria-hidden="true">
          <span />
          <span />
          <span />
          <span />
        </div>
        <div>
          <p className="brand-name">Aegis</p>
          {/* <p className="brand-subtitle">Digital Study</p> */}
        </div>
      </div>

      <button className="new-chat-button" type="button" onClick={handleNewChat}>
        <MessageSquarePlus size={17} />
        New chat
      </button>

      <label className="sidebar-search">
        <Search size={18} />
        <input
          value={search}
          onChange={(event) => onSearch(event.target.value)}
          placeholder="Search"
          type="search"
        />
      </label>

      <Link className={`nav-row ${active === "projects" ? "active" : ""}`} href="/projects">
        <FolderOpen size={20} />
        Projects
      </Link>

      <div className="sidebar-divider" />

      <section className="recents">
        <h2>Recents</h2>
        <div className="recent-list">
          {filteredRecents.map((chat) => (
            <div key={chat.id} className="recent-row">
              <button
                className="recent-chat"
                type="button"
                onClick={() => onOpenChat?.(chat.id)}
              >
                {formatRecentTitle(chat.title)}
              </button>
              <button
                className="icon-button recent-delete"
                type="button"
                aria-label={`Delete ${chat.title}`}
                onClick={() => onDeleteChat?.(chat.id)}
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
      </section>

      <footer className="sidebar-footer">
        <div className="footer-user">
          <UserCircle size={22} />
          <span>User</span>
        </div>
        <button
          className="icon-button"
          type="button"
          aria-label="Settings"
          onClick={() => setShowSettings((current) => !current)}
        >
          <Settings size={18} />
        </button>
        {showSettings ? (
          <div className="settings-menu">
            <button className="settings-item" type="button" onClick={handleLogout}>
              Log out
            </button>
          </div>
        ) : null}
      </footer>
    </aside>
  );
}

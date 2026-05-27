"use client";

import { ReactNode } from "react";
import { Conversation } from "@/types";
import { AuthGuard } from "@/components/AuthGuard";
import { Sidebar } from "@/components/Sidebar";

type AppShellProps = {
  active: "chat" | "projects";
  recents: Conversation[];
  search: string;
  onSearch: (value: string) => void;
  onNewChat?: () => void;
  onOpenChat?: (chatId: string) => void;
  onDeleteChat?: (chatId: string) => void;
  children: ReactNode;
};

export function AppShell(props: AppShellProps) {
  return (
    <AuthGuard>
      <main className="app-frame">
        <Sidebar
          active={props.active}
          recents={props.recents}
          search={props.search}
          onSearch={props.onSearch}
          onNewChat={props.onNewChat}
          onOpenChat={props.onOpenChat}
          onDeleteChat={props.onDeleteChat}
        />
        <section className="main-surface">{props.children}</section>
      </main>
    </AuthGuard>
  );
}

"use client";

import { FolderPlus, Plus, Search, Sparkles } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { createProject, listChats, listProjects } from "@/lib/api";
import { Conversation, Project } from "@/types";

export default function ProjectsPage() {
  const [sidebarSearch, setSidebarSearch] = useState("");
  const [projectSearch, setProjectSearch] = useState("");
  const [recents, setRecents] = useState<Conversation[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([listProjects(), listChats()])
      .then(([projectData, chatData]) => {
        setProjects(projectData);
        setRecents(chatData.slice(0, 12));
      })
      .catch((err) => setError(err.message));
  }, []);

  const filteredProjects = useMemo(
    () =>
      projects.filter((project) =>
        project.name.toLowerCase().includes(projectSearch.toLowerCase()),
      ),
    [projectSearch, projects],
  );

  async function handleCreateProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedName = name.trim();
    if (!trimmedName) return;

    try {
      const project = await createProject({
        name: trimmedName,
        description: description.trim() || undefined,
      });
      setProjects((current) => [project, ...current]);
      setName("");
      setDescription("");
      setShowCreate(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create project.");
    }
  }

  return (
    <AppShell
      active="projects"
      recents={recents}
      search={sidebarSearch}
      onSearch={setSidebarSearch}
    >
      <div className="projects-page">
        <header className="projects-header">
          <div>
            <h1>Projects</h1>
            <p>Manage your active research and development workstreams.</p>
          </div>
          <div className="projects-tools">
            <label className="project-search">
              <Search size={24} />
              <input
                value={projectSearch}
                onChange={(event) => setProjectSearch(event.target.value)}
                aria-label="Search projects"
                type="search"
              />
            </label>
            <button className="new-project-button" onClick={() => setShowCreate(true)} type="button">
              <Plus size={18} />
              New project
            </button>
          </div>
        </header>

        {filteredProjects.length ? (
          <section className="project-grid" aria-label="Projects">
            {filteredProjects.map((project) => (
              <article className="project-card" key={project.id}>
                <FolderPlus size={22} />
                <h2>{project.name}</h2>
                <p>{project.description || "No description added."}</p>
              </article>
            ))}
          </section>
        ) : (
          <section className="projects-empty" aria-label="No projects">
            <Sparkles size={32} />
            <h2>Looking to start a project?</h2>
            <button className="create-project-tile" type="button" onClick={() => setShowCreate(true)}>
              <span>
                <Plus size={22} />
              </span>
              Create from project
            </button>
          </section>
        )}

        {showCreate ? (
          <div className="modal-backdrop" role="presentation">
            <form className="project-modal" onSubmit={handleCreateProject}>
              <h2>Create project</h2>
              <label>
                Project name
                <input value={name} onChange={(event) => setName(event.target.value)} required />
              </label>
              <label>
                Description
                <textarea
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                  rows={4}
                />
              </label>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowCreate(false)}>
                  Cancel
                </button>
                <button className="primary-button" type="submit">
                  Create
                </button>
              </div>
            </form>
          </div>
        ) : null}

        {error ? <p className="inline-error">{error}</p> : null}
      </div>
    </AppShell>
  );
}

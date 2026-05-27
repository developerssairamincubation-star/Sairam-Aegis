import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


@dataclass
class IngestionResult:
    indexed_files: int
    indexed_chunks: int
    changed_files: int
    last_ingested_at: str


class MarkdownIngestor:
    def __init__(self, knowledge_base_dir: Path, manifest_path: Path) -> None:
        self.knowledge_base_dir = knowledge_base_dir
        self.manifest_path = manifest_path
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=900,
            chunk_overlap=150,
            separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""],
        )

    def _read_manifest(self) -> dict[str, Any]:
        if not self.manifest_path.exists():
            return {"files": {}, "last_ingested_at": None}
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def _write_manifest(self, manifest: dict[str, Any]) -> None:
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    def _file_hash(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _load_documents(self, path: Path, rel_path: str, file_hash: str) -> list[Document]:
        text = path.read_text(encoding="utf-8")
        base_doc = Document(
            page_content=text,
            metadata={
                "source": rel_path,
                "sha256": file_hash,
                "title": path.stem,
            },
        )
        chunks = self.splitter.split_documents([base_doc])
        for index, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = f"{rel_path}:{index}"
        return chunks

    def ingest(self, vector_store) -> IngestionResult:
        self.knowledge_base_dir.mkdir(parents=True, exist_ok=True)
        manifest = self._read_manifest()
        known_files: dict[str, str] = manifest.get("files", {})
        current_files: dict[str, str] = {}
        changed_files = 0
        indexed_chunks = 0

        for md_file in sorted(self.knowledge_base_dir.rglob("*.md")):
            rel_path = md_file.relative_to(self.knowledge_base_dir).as_posix()
            file_hash = self._file_hash(md_file)
            current_files[rel_path] = file_hash

            if known_files.get(rel_path) == file_hash:
                continue

            changed_files += 1
            if hasattr(vector_store, "_collection"):
                vector_store._collection.delete(where={"source": rel_path})
            docs = self._load_documents(md_file, rel_path, file_hash)
            if docs:
                vector_store.add_documents(docs)
                indexed_chunks += len(docs)

        removed_files = set(known_files) - set(current_files)
        for rel_path in removed_files:
            changed_files += 1
            if hasattr(vector_store, "_collection"):
                vector_store._collection.delete(where={"source": rel_path})

        now = datetime.now(timezone.utc).isoformat()
        manifest["files"] = current_files
        manifest["last_ingested_at"] = now
        self._write_manifest(manifest)

        return IngestionResult(
            indexed_files=len(current_files),
            indexed_chunks=indexed_chunks,
            changed_files=changed_files,
            last_ingested_at=now,
        )

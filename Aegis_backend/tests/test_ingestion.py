from pathlib import Path

from app.rag.ingestion import MarkdownIngestor


class FakeCollection:
    def __init__(self) -> None:
        self.deleted_sources: list[str] = []

    def delete(self, where):
        self.deleted_sources.append(where["source"])


class FakeVectorStore:
    def __init__(self) -> None:
        self._collection = FakeCollection()
        self.documents = []

    def add_documents(self, docs):
        self.documents.extend(docs)


def test_markdown_ingestion_indexes_changed_files(tmp_path: Path):
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    (kb_dir / "intro.md").write_text("# Intro\n\nAegis content.", encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    store = FakeVectorStore()

    result = MarkdownIngestor(kb_dir, manifest_path).ingest(store)

    assert result.indexed_files == 1
    assert result.changed_files == 1
    assert store.documents
    assert store.documents[0].metadata["source"] == "intro.md"


def test_markdown_ingestion_skips_unchanged_files(tmp_path: Path):
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    (kb_dir / "intro.md").write_text("# Intro\n\nAegis content.", encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"

    MarkdownIngestor(kb_dir, manifest_path).ingest(FakeVectorStore())
    second_store = FakeVectorStore()
    result = MarkdownIngestor(kb_dir, manifest_path).ingest(second_store)

    assert result.indexed_files == 1
    assert result.changed_files == 0
    assert second_store.documents == []


def test_markdown_ingestion_deletes_removed_files(tmp_path: Path):
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    doc_path = kb_dir / "intro.md"
    doc_path.write_text("# Intro\n\nAegis content.", encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"

    MarkdownIngestor(kb_dir, manifest_path).ingest(FakeVectorStore())
    doc_path.unlink()
    second_store = FakeVectorStore()
    result = MarkdownIngestor(kb_dir, manifest_path).ingest(second_store)

    assert result.indexed_files == 0
    assert result.changed_files == 1
    assert second_store._collection.deleted_sources == ["intro.md"]

from app.rag.vector_store import SupabaseVectorStore


class FakeEmbeddings:
    def embed_documents(self, texts):
        return [[float(index), 0.0] for index, _ in enumerate(texts)]

    def embed_query(self, text):
        return [1.0, 0.0]


class FakeRepository:
    def __init__(self) -> None:
        self.query_embedding = None

    def match_rag_chunks(self, query_embedding, match_count):
        self.query_embedding = query_embedding
        assert match_count == 2
        return [
            {
                "content": "Constitution content",
                "source": "law.md",
                "title": "Law",
                "chunk_id": "law.md:0",
                "similarity": 0.91,
                "metadata": {"section": "intro"},
            }
        ]


def test_similarity_search_maps_supabase_results_to_documents():
    repository = FakeRepository()
    store = SupabaseVectorStore(repository=repository, embeddings=FakeEmbeddings())

    docs = store.similarity_search("what is law?", k=2)

    assert repository.query_embedding == [1.0, 0.0]
    assert docs[0].page_content == "Constitution content"
    assert docs[0].metadata["source"] == "law.md"
    assert docs[0].metadata["chunk_id"] == "law.md:0"
    assert docs[0].metadata["score"] == 0.91

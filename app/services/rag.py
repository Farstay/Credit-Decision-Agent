from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from app.config import settings


_model = None

def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    return _model

COLLECTION = "credit_rules"
VECTOR_SIZE = 384


def get_qdrant() -> QdrantClient:
    return QdrantClient(url=settings.qdrant_url, prefer_grpc=False)


def embed(text: str) -> list[float]:
    return _get_model().encode(text).tolist()


def index_rules():
    """Индексация: читаем регламенты, режем на чанки, кладём в Qdrant."""
    client = get_qdrant()

    # удаляем коллекцию, если была, и создаём заново
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )

    rules_path = Path(__file__).parent.parent / "knowledge" / "credit_rules.txt"
    text = rules_path.read_text(encoding="utf-8")
    chunks = [c.strip() for c in text.split("\n\n") if c.strip()]

    points = [
        PointStruct(id=i, vector=embed(chunk), payload={"text": chunk})
        for i, chunk in enumerate(chunks)
    ]
    client.upsert(collection_name=COLLECTION, points=points)
    return len(points)


def search_rules(query: str, top_k: int = 3) -> list[str]:
    """Семантический поиск: находим top_k релевантных правил под запрос."""
    client = get_qdrant()
    query_vector = embed(query)
    results = client.search(
        collection_name=COLLECTION,
        query_vector=query_vector,
        limit=top_k,
    )
    return [hit.payload["text"] for hit in results]
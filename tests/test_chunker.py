from src.ingestion.schemas import Contract
from src.preprocessing.chunker import AdaptiveChunker
from src.utils.config import ChunkingConfig


def make_contract(word_count: int, contract_id: str = "test_contract") -> Contract:
    text = " ".join(f"word{i}" for i in range(word_count))
    return Contract(
        contract_id=contract_id,
        title="Test Contract",
        raw_text=text,
        source_format="cuad_json",
    )


def test_small_document_yields_single_chunk():
    config = ChunkingConfig(small_doc_word_threshold=1500, chunk_size_tokens=500, chunk_overlap_tokens=50)
    chunker = AdaptiveChunker(config)
    contract = make_contract(word_count=100)

    chunks = chunker.chunk_contract(contract)

    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].contract_id == "test_contract"


def test_large_document_yields_multiple_chunks():
    config = ChunkingConfig(small_doc_word_threshold=200, chunk_size_tokens=100, chunk_overlap_tokens=10)
    chunker = AdaptiveChunker(config)
    contract = make_contract(word_count=1000)

    chunks = chunker.chunk_contract(contract)

    assert len(chunks) > 1
    for i, chunk in enumerate(chunks):
        assert chunk.chunk_index == i
        assert chunk.contract_id == "test_contract"


def test_chunk_ids_are_deterministic():
    config = ChunkingConfig(small_doc_word_threshold=200, chunk_size_tokens=100, chunk_overlap_tokens=10)
    chunker = AdaptiveChunker(config)
    contract = make_contract(word_count=500)

    chunks_a = chunker.chunk_contract(contract)
    chunks_b = chunker.chunk_contract(contract)

    assert [c.chunk_id for c in chunks_a] == [c.chunk_id for c in chunks_b]


def test_no_empty_chunks_produced():
    config = ChunkingConfig(small_doc_word_threshold=200, chunk_size_tokens=50, chunk_overlap_tokens=5)
    chunker = AdaptiveChunker(config)
    contract = make_contract(word_count=800)

    chunks = chunker.chunk_contract(contract)

    assert all(chunk.text.strip() for chunk in chunks)

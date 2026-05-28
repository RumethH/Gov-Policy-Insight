from pathlib import Path

import pytest
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from tests.fixtures.fake_embeddings import DeterministicEmbeddings


@pytest.mark.integration
def test_splitter_embeddings_and_chroma_roundtrip(tmp_path: Path) -> None:
    docs = [
        Document(
            page_content="NSW cyber policy requires incident reporting within 24 hours.",
            metadata={"source": "nsw_cyber_policy.pdf", "page": 2},
        )
    ]
    splitter = RecursiveCharacterTextSplitter(chunk_size=40, chunk_overlap=5)
    chunks = splitter.split_documents(docs)
    assert chunks

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=DeterministicEmbeddings(),
        persist_directory=str(tmp_path / "chroma"),
    )

    results = vectorstore.similarity_search("incident reporting timeframe", k=2)
    assert results
    assert any("incident" in d.page_content.lower() for d in results)

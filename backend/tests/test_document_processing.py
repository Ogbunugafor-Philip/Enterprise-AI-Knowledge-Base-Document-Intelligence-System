from app.services import chunking_service, document_processor_service, embedding_service, file_validation_service


def test_file_validation_service_validates_correct_file_types():
    assert file_validation_service.validate_file_type("policy.pdf", "application/pdf")[0]


def test_file_validation_service_rejects_disallowed_file_types():
    ok, reason = file_validation_service.validate_file_type("malware.exe", "application/octet-stream")

    assert not ok
    assert "not allowed" in reason


def test_file_validation_service_rejects_files_exceeding_size_limit():
    ok, reason = file_validation_service.validate_file_size(51 * 1024 * 1024, max_size_mb=50)

    assert not ok
    assert "exceeds" in reason


def test_file_validation_service_detects_file_type_spoofing():
    ok, reason = file_validation_service.validate_file_content("fake.pdf", b"not really a pdf")

    assert not ok
    assert "does not match" in reason


def test_chunking_service_hybrid_chunk_returns_non_empty_list_for_sample_text():
    text = "Introduction. " + "This policy explains secure document handling. " * 80
    chunks = chunking_service.hybrid_chunk(text)

    assert chunks
    assert all("chunk_text" in chunk for chunk in chunks)


def test_chunking_service_calculates_correct_token_count():
    assert chunking_service.get_token_count("one two three") == 3


def test_chunking_service_generates_unique_chunk_hashes():
    first = chunking_service.calculate_chunk_hash("first chunk")
    second = chunking_service.calculate_chunk_hash("second chunk")

    assert first != second
    assert len(first) == 64


def test_chunking_service_chunk_overlap_is_maintained_between_adjacent_chunks():
    sentence = " ".join(f"token{i}" for i in range(80)) + "."
    text = " ".join([sentence for _ in range(10)])
    chunks = chunking_service.semantic_chunk(text, target_max=120, overlap_tokens=10)

    assert len(chunks) > 1
    first_tail = chunks[0]["chunk_text"].split()[-10:]
    second_tokens = chunks[1]["chunk_text"].split()
    assert first_tail == second_tokens[:10]


def test_embedding_service_load_embedding_model_returns_model_instance():
    model = embedding_service.load_embedding_model()

    assert hasattr(model, "encode")


def test_embedding_service_generate_embedding_returns_correct_vector_dimensions():
    embedding = embedding_service.generate_embedding("sample chunk")

    assert len(embedding) == 384


def test_document_processor_service_clean_extracted_text_removes_excessive_whitespace():
    cleaned = document_processor_service.clean_extracted_text("Hello\\x00    world\\n\\n\\nNext")

    assert cleaned == "Hello world\\n\\nNext"

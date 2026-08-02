"""Tests du stockage des documents PDF attachés aux activités.

`documents` ne dépend ni de FastAPI ni de SQLAlchemy : ces tests écrivent dans un
`tmp_path` sans client HTTP ni base.
"""

import io

import pytest

import documents


@pytest.fixture(autouse=True)
def upload_dir(monkeypatch, tmp_path):
    """Isole les écritures dans un répertoire temporaire.

    `config.settings` étant instancié à l'import, `monkeypatch.setenv` n'aurait
    aucun effet : on patche l'attribut de l'objet déjà construit.
    """
    monkeypatch.setattr(documents.settings, "UPLOAD_DIR", str(tmp_path))
    return tmp_path


def _pdf(size: int = 1024) -> io.BytesIO:
    """Un contenu qui commence par la signature PDF, de la taille demandée."""
    return io.BytesIO(b"%PDF-1.7\n" + b"a" * max(0, size - 9))


class TestDocumentPath:
    def test_path_is_derived_from_the_id_not_the_filename(self, upload_dir):
        path = documents.document_path(7)

        assert path == upload_dir / "activities" / "7.pdf"


class TestSanitizeFilename:
    def test_keeps_a_plain_name(self):
        assert documents.sanitize_filename("reglement.pdf") == "reglement.pdf"

    def test_strips_directory_components(self):
        assert documents.sanitize_filename("../../etc/passwd") == "passwd"

    def test_strips_windows_directory_components(self):
        assert documents.sanitize_filename(r"C:\Temp\reglement.pdf") == "reglement.pdf"

    def test_falls_back_when_nothing_usable_remains(self):
        assert documents.sanitize_filename(None) == "document.pdf"
        assert documents.sanitize_filename("   ") == "document.pdf"

    def test_drops_characters_that_would_break_a_header(self):
        # Le nom part dans un `Content-Disposition` : un guillemet ou un saut de
        # ligne y permettrait d'injecter un en-tête.
        assert '"' not in documents.sanitize_filename('re"glement.pdf')
        assert "\n" not in documents.sanitize_filename("regle\nment.pdf")

    def test_bounds_the_length(self):
        assert len(documents.sanitize_filename("a" * 500)) <= 120


class TestStore:
    def test_writes_the_file_at_the_derived_path(self, upload_dir):
        path = documents.store(3, _pdf())

        assert path == upload_dir / "activities" / "3.pdf"
        assert path.read_bytes().startswith(b"%PDF")

    def test_creates_the_parent_directory(self, upload_dir):
        documents.store(3, _pdf())

        assert (upload_dir / "activities").is_dir()

    def test_rejects_a_file_that_is_not_a_pdf(self, upload_dir):
        with pytest.raises(documents.NotAPdf):
            documents.store(3, io.BytesIO(b"GIF89a rien a voir"))

    def test_rejects_an_empty_file(self, upload_dir):
        with pytest.raises(documents.NotAPdf):
            documents.store(3, io.BytesIO(b""))

    def test_rejects_a_file_over_the_limit(self, upload_dir):
        oversized = _pdf(documents.MAX_DOCUMENT_BYTES + 1)

        with pytest.raises(documents.DocumentTooLarge):
            documents.store(3, oversized)

    def test_accepts_a_file_exactly_at_the_limit(self, upload_dir):
        documents.store(3, _pdf(documents.MAX_DOCUMENT_BYTES))

        assert documents.document_path(3).exists()

    def test_leaves_nothing_behind_when_rejected(self, upload_dir):
        with pytest.raises(documents.NotAPdf):
            documents.store(3, io.BytesIO(b"pas un pdf"))

        assert not documents.document_path(3).exists()
        assert list((upload_dir / "activities").glob("*")) == []

    def test_replaces_an_existing_document(self, upload_dir):
        documents.store(3, io.BytesIO(b"%PDF-1.7 premier"))
        documents.store(3, io.BytesIO(b"%PDF-1.7 second"))

        assert documents.document_path(3).read_bytes() == b"%PDF-1.7 second"
        assert len(list((upload_dir / "activities").glob("*"))) == 1

    def test_keeps_the_previous_document_when_the_new_one_is_rejected(self, upload_dir):
        documents.store(3, io.BytesIO(b"%PDF-1.7 premier"))

        with pytest.raises(documents.NotAPdf):
            documents.store(3, io.BytesIO(b"pas un pdf"))

        assert documents.document_path(3).read_bytes() == b"%PDF-1.7 premier"


class TestDelete:
    def test_removes_the_file_and_reports_success(self, upload_dir):
        documents.store(3, _pdf())

        assert documents.delete(3) is True
        assert not documents.document_path(3).exists()

    def test_reports_failure_when_there_is_nothing_to_delete(self, upload_dir):
        assert documents.delete(3) is False

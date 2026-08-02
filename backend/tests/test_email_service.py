"""Tests du rendu des templates d'email.

Le rendu passe par Jinja2 avec auto-échappement. Deux modes d'échec sont couverts
ici, invisibles pour les tests d'API qui n'observent que le contexte transmis :
une clé absente du contexte, et une valeur contenant du HTML.
"""

import re

import pytest

from email_service import EmailSendError, render_template

PLACEHOLDER = re.compile(r"{{.*?}}|{%.*?%}")

SUBMISSION_CONTEXT = {
    "prenom": "Jean",
    "nom": "Dupont",
    "code": "ABC123XYZ789",
    "resume_url": "https://exemple.fr/adhesion?code=ABC123XYZ789",
    "documents": [],
}


class TestSubmissionTemplate:
    def test_every_placeholder_is_substituted(self):
        html = render_template("submission_email.html", SUBMISSION_CONTEXT)

        assert PLACEHOLDER.findall(html) == []

    def test_a_missing_key_is_an_email_failure(self):
        """Une clé oubliée ne doit pas produire un email tronqué mais un échec.

        `StrictUndefined` transforme l'oubli en `EmailSendError`, que l'appelant
        sait déjà absorber : l'adhésion reste enregistrée, `email_sent_at` reste
        NULL et le back-office propose le renvoi. Auparavant, le moteur maison
        laissait `{{ code }}` en clair dans l'email envoyé à l'adhérent.
        """
        incomplete = {k: v for k, v in SUBMISSION_CONTEXT.items() if k != "code"}

        with pytest.raises(EmailSendError, match="code"):
            render_template("submission_email.html", incomplete)

    def test_the_code_and_the_resume_link_are_present(self):
        html = render_template("submission_email.html", SUBMISSION_CONTEXT)

        assert SUBMISSION_CONTEXT["code"] in html
        assert f'href="{SUBMISSION_CONTEXT["resume_url"]}"' in html


VALIDATION_CONTEXT = {
    "prenom": "Jean",
    "nom": "Dupont",
    "code": "ABC123XYZ789",
    "adhesion_amount": 15.0,
    "activities": [{"name": "Yoga", "price": 100.0}],
    "total_cost": 115.0,
    "documents": [],
}


class TestEscaping:
    """Le rendu doit échapper le HTML porté par les valeurs du contexte.

    La substitution maison qui précédait ne l'échappait pas : `nom`, `prenom` et
    les noms d'activités partaient tels quels dans le corps de l'email.
    """

    def test_an_adherent_name_containing_html_is_escaped(self):
        html = render_template(
            "submission_email.html",
            {**SUBMISSION_CONTEXT, "nom": "Dupont<script>alert(1)</script>"},
        )

        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_the_resume_link_survives_escaping(self):
        """L'échappement ne doit pas casser une URL portant plusieurs paramètres :
        `&` devient `&amp;`, ce qui est la forme correcte dans un attribut HTML et
        reste interprété comme `&` par le client mail."""
        url = "https://exemple.fr/adhesion?code=ABC123XYZ789&source=email"

        html = render_template("submission_email.html", {**SUBMISSION_CONTEXT, "resume_url": url})

        assert 'href="https://exemple.fr/adhesion?code=ABC123XYZ789&amp;source=email"' in html

    def test_a_plain_value_is_left_untouched(self):
        """Garde-fou : l'échappement ne doit pas défigurer les valeurs normales."""
        html = render_template("submission_email.html", SUBMISSION_CONTEXT)

        assert "Bonjour Jean Dupont," in html


class TestValidationTemplate:
    def test_every_placeholder_is_substituted(self):
        html = render_template("validation_email.html", VALIDATION_CONTEXT)

        assert PLACEHOLDER.findall(html) == []

    def test_an_activity_name_containing_html_is_escaped(self):
        """Le vecteur de masse : un nom d'activité est saisi au back-office et
        diffusé à tous les inscrits. Un compte admin compromis en ferait une
        injection HTML vers l'ensemble des adhérents."""
        html = render_template(
            "validation_email.html",
            {
                **VALIDATION_CONTEXT,
                "activities": [
                    {"name": '<img src=x onerror="alert(1)">', "price": 100.0}
                ],
            },
        )

        # Aucune balise ni attribut exécutable ne se forme ; le nom reste lisible
        # sous forme échappée. On n'assert pas la graphie exacte des entités
        # (`&#34;` vs `&quot;`), qui est un détail de Jinja2.
        assert "<img" not in html
        assert 'onerror="alert(1)"' not in html
        assert "&lt;img src=x" in html

    def test_each_activity_becomes_a_row(self):
        html = render_template(
            "validation_email.html",
            {
                "prenom": "Jean",
                "nom": "Dupont",
                "code": "ABC123XYZ789",
                "adhesion_amount": 15.0,
                "activities": [
                    {"name": "Yoga", "price": 100.0},
                    {"name": "Judo", "price": 80.0},
                ],
                "total_cost": 195.0,
                "documents": [],
            },
        )

        assert "Activité : Yoga" in html
        assert "Activité : Judo" in html


DOCUMENT = {"name": "Gym", "url": "https://exemple.fr/api/activities/1/document"}


class TestDocumentsSection:
    """Le bloc « Documents à imprimer et signer », dans les deux emails.

    Des liens et non des pièces jointes : pas de limite de taille Brevo, pas de
    pénalité anti-spam, et le lien sert toujours la dernière version du document.
    """

    def test_the_validation_email_links_each_document(self):
        html = render_template(
            "validation_email.html", {**VALIDATION_CONTEXT, "documents": [DOCUMENT]}
        )

        assert f'href="{DOCUMENT["url"]}"' in html
        assert "Documents à imprimer et signer" in html

    def test_the_submission_email_links_each_document(self):
        html = render_template(
            "submission_email.html", {**SUBMISSION_CONTEXT, "documents": [DOCUMENT]}
        )

        assert f'href="{DOCUMENT["url"]}"' in html
        assert "Documents à imprimer et signer" in html

    def test_the_section_is_absent_without_documents(self):
        """Une adhésion sans activité à document ne doit pas voir un titre vide."""
        validation = render_template("validation_email.html", VALIDATION_CONTEXT)
        submission = render_template("submission_email.html", SUBMISSION_CONTEXT)

        assert "Documents à imprimer et signer" not in validation
        assert "Documents à imprimer et signer" not in submission

    def test_a_missing_documents_key_is_an_email_failure(self):
        """`StrictUndefined` : un contexte incomplet échoue au lieu de tronquer.

        Garde-fou sur les deux constructions de contexte de `crud` — si l'une
        oublie la clé, l'envoi lève plutôt que d'omettre silencieusement les
        documents dont l'adhérent a besoin.
        """
        incomplete = {k: v for k, v in VALIDATION_CONTEXT.items() if k != "documents"}

        with pytest.raises(EmailSendError, match="documents"):
            render_template("validation_email.html", incomplete)

    def test_a_document_name_containing_html_is_escaped(self):
        html = render_template(
            "validation_email.html",
            {
                **VALIDATION_CONTEXT,
                "documents": [{**DOCUMENT, "name": '<img src=x onerror="alert(1)">'}],
            },
        )

        assert "<img" not in html
        assert 'onerror="alert(1)"' not in html

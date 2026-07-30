"""Tests du rendu des templates d'email.

`render_template` est un moteur maison : il fait de simples `str.replace` sur
`{{ clé }}`. Une clé absente du contexte ne lève rien, elle laisse le placeholder
en clair dans l'email envoyé à l'adhérent. Ces tests couvrent ce mode d'échec,
que les tests d'API ne voient pas : eux n'observent que le contexte transmis.
"""

import re

from email_service import render_template

PLACEHOLDER = re.compile(r"{{.*?}}|{%.*?%}")

SUBMISSION_CONTEXT = {
    "prenom": "Jean",
    "nom": "Dupont",
    "code": "ABC123XYZ789",
    "resume_url": "https://exemple.fr/adhesion?code=ABC123XYZ789",
}


class TestSubmissionTemplate:
    def test_every_placeholder_is_substituted(self):
        html = render_template("submission_email.html", SUBMISSION_CONTEXT)

        assert PLACEHOLDER.findall(html) == []

    def test_a_missing_key_leaves_a_visible_placeholder(self):
        """Garde-fou : prouve que le test ci-dessus détecte bien une clé oubliée."""
        incomplete = {k: v for k, v in SUBMISSION_CONTEXT.items() if k != "code"}

        html = render_template("submission_email.html", incomplete)

        assert PLACEHOLDER.findall(html) == ["{{ code }}"]

    def test_the_code_and_the_resume_link_are_present(self):
        html = render_template("submission_email.html", SUBMISSION_CONTEXT)

        assert SUBMISSION_CONTEXT["code"] in html
        assert f'href="{SUBMISSION_CONTEXT["resume_url"]}"' in html


class TestValidationTemplate:
    def test_every_placeholder_is_substituted(self):
        html = render_template(
            "validation_email.html",
            {
                "prenom": "Jean",
                "nom": "Dupont",
                "code": "ABC123XYZ789",
                "adhesion_amount": 15.0,
                "activities": [{"name": "Yoga", "price": 100.0}],
                "total_cost": 115.0,
            },
        )

        assert PLACEHOLDER.findall(html) == []

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
            },
        )

        assert "Activité : Yoga" in html
        assert "Activité : Judo" in html

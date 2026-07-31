"""Tests de `docker/backup/backup.sh`.

Ce script n'est pas du backend, mais il vit ici : `mise run check` n'exécute que
pytest et vitest, et un test hors de ces deux suites ne serait jamais lancé.

Les commandes testées sont **extraites du script**, jamais recopiées : un test qui
réécrirait les options ne prouverait rien sur ce que le cron exécute réellement.
Le round-trip chiffrement/déchiffrement lance de vrais `openssl`, ce qui valide du
même coup la procédure de restauration documentée dans le script — le vrai risque
en durcissant la dérivation de clé étant de rendre les sauvegardes irrécupérables.

`shell=True` est délibéré : les commandes extraites contiennent un pipe
(`… | gunzip`), qu'une liste d'arguments ne saurait pas exécuter. Il n'y a pas
d'entrée utilisateur — la source est un fichier versionné du dépôt.
"""

import gzip
import re
import subprocess
from pathlib import Path

import pytest

BACKUP_SH = Path(__file__).parents[2] / "docker" / "backup" / "backup.sh"
SCRIPT = BACKUP_SH.read_text()
# Les commandes longues sont écrites sur plusieurs lignes : on replie les
# continuations `\` pour qu'une regex voie chaque commande d'un seul tenant.
SCRIPT_JOINED = SCRIPT.replace("\\\n", " ")
# Les commandes réellement exécutées, commentaires exclus — le script en contient
# qui citent les commandes qu'il exécute, et une regex les confondrait.
COMMANDS = "\n".join(
    line for line in SCRIPT_JOINED.splitlines() if not line.strip().startswith("#")
)

PASSPHRASE = "passphrase-de-test-longue-et-aleatoire"


def _extract(pattern: str, what: str, source: str = COMMANDS) -> str:
    """Extrait un fragment du script. Par défaut, cherche dans les commandes.

    `source=SCRIPT` pour aller lire les procédures documentées en commentaire.
    """
    match = re.search(pattern, source, re.M)
    assert match is not None, f"{what} introuvable dans {BACKUP_SH.name}"
    return match.group(1).strip()


class TestTransferIsEncrypted:
    """Vuln 6 — `curl … ftp://` transmettait `FTP_USER`/`FTP_PASSWORD` en clair.

    FTPS a été écarté : le cluster OVH répond `500 This security scheme is not
    implemented` à `AUTH TLS` comme à `AUTH SSL`. Le transport est donc SFTP.
    """

    def test_the_transfer_goes_through_sftp(self):
        transfer = _extract(r"^(.*\bsshpass\b.+)$", "la commande de transfert")

        assert " sftp " in f" {transfer} "

    def test_no_plain_ftp_transfer_remains(self):
        """Aucune invocation de curl vers ftp:// ne doit subsister.

        Ne considère que les lignes exécutant `curl` : le script mentionne encore
        `ftp://` dans des commentaires expliquant pourquoi il a été abandonné.
        """
        for line in SCRIPT.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or not stripped.startswith("curl"):
                continue
            assert "ftp://" not in stripped, f"transfert en clair possible : {stripped}"

    def test_host_key_verification_is_not_disabled(self):
        """Sans vérification d'hôte, le chiffrement ne protège plus rien.

        Un intermédiaire se ferait passer pour le serveur OVH et récupérerait le
        mot de passe au premier échange — soit exactement la Vuln 6, par un autre
        chemin. `accept-new` est acceptable (il enregistre à la première
        connexion, puis refuse tout changement) ; `no` et
        `UserKnownHostsFile=/dev/null` ne le sont pas.
        """
        assert "StrictHostKeyChecking=no" not in SCRIPT
        assert "UserKnownHostsFile=/dev/null" not in SCRIPT
        assert "known_hosts" in SCRIPT, (
            "le fichier known_hosts doit être persistant, sinon chaque redémarrage "
            "du conteneur ré-accepte aveuglément la clé présentée"
        )

    def test_the_password_never_appears_as_a_command_argument(self):
        """`sshpass -p <mot de passe>` l'exposerait dans `ps` à tout le conteneur.

        `-e` le lit dans l'environnement, qui n'est pas listable par les autres
        processus de la même façon.
        """
        transfer = _extract(r"^(.*\bsshpass\b.+)$", "la commande de transfert")

        assert "-e" in transfer.split()
        assert "-p" not in transfer.split()


class TestRemotePathStaysRelative:
    """En FTP, `/backup` était relatif au chroot du compte ; en SFTP, un chemin
    absolu viserait la racine du serveur, où le compte n'a rien à écrire."""

    def test_the_remote_directory_is_relative(self):
        put = _extract(r"^(put .+)$", "la commande put du batch sftp")
        destination = put.split()[-1]

        assert not destination.startswith("/"), (
            f"destination absolue en SFTP : {destination}"
        )


class TestEncryptionKeyDerivation:
    """Vuln 7 — sans `-pbkdf2`, OpenSSL retombe sur EVP_BytesToKey : MD5, une
    itération, soit un hachage par mot de passe candidat pour l'attaquant."""

    def test_the_key_derivation_is_hardened(self):
        encryption = _extract(r"^(openssl enc (?!-d).+)$", "la commande de chiffrement")

        assert "-pbkdf2" in encryption
        assert "-md sha256" in encryption
        iterations = re.search(r"-iter (\d+)", encryption)
        assert iterations is not None, "aucun nombre d'itérations fixé"
        assert int(iterations.group(1)) >= 100_000, "trop peu d'itérations"

    def test_the_documented_restore_command_actually_works(self, tmp_path):
        """Chiffre avec la commande du script, déchiffre avec celle documentée.

        C'est ce test qui protège la restauration : si les options de chiffrement
        changent sans que le commentaire suive, il casse.
        """
        # Le pipeline réel est `pg_dump | gzip | openssl` : le clair passé à openssl
        # est donc du gzip, et la restauration se termine par `| gunzip`.
        dump = b"-- contenu de sauvegarde\n" * 100
        plaintext = tmp_path / "dump.sql.gz"
        plaintext.write_bytes(gzip.compress(dump))
        encrypted = tmp_path / "dump.sql.gz.enc"

        encrypt = _extract(r"^(openssl enc (?!-d).+)$", "la commande de chiffrement")
        encrypt = encrypt.replace('"$BACKUP_GZ_FILE"', str(plaintext))
        encrypt = encrypt.replace('"$BACKUP_ENC_FILE"', str(encrypted))
        env = {"ENCRYPTION_PASSWORD": PASSPHRASE, "PATH": "/usr/bin:/bin"}
        done = subprocess.run(encrypt, shell=True, env=env, capture_output=True)
        assert done.returncode == 0, done.stderr.decode()
        assert encrypted.read_bytes() != plaintext.read_bytes()

        restore = _extract(r"^#\s*RESTAURATION\s*:\s*(openssl enc -d .+)$",
                           "la commande de restauration documentée", source=SCRIPT)
        restore = restore.replace("FICHIER.enc", str(encrypted))
        recovered = subprocess.run(restore, shell=True, env=env, capture_output=True)

        assert recovered.returncode == 0, recovered.stderr.decode()
        assert recovered.stdout == dump

    def test_a_wrong_passphrase_fails_to_decrypt(self, tmp_path):
        """Garde-fou : prouve que le test ci-dessus vérifie un vrai déchiffrement."""
        plaintext = tmp_path / "dump.sql.gz"
        plaintext.write_bytes(b"-- contenu de sauvegarde\n")
        encrypted = tmp_path / "dump.sql.gz.enc"

        encrypt = _extract(r"^(openssl enc (?!-d).+)$", "la commande de chiffrement")
        encrypt = encrypt.replace('"$BACKUP_GZ_FILE"', str(plaintext))
        encrypt = encrypt.replace('"$BACKUP_ENC_FILE"', str(encrypted))
        subprocess.run(
            encrypt, shell=True, check=True,
            env={"ENCRYPTION_PASSWORD": PASSPHRASE, "PATH": "/usr/bin:/bin"},
        )

        restore = _extract(r"^#\s*RESTAURATION\s*:\s*(openssl enc -d .+)$",
                           "la commande de restauration documentée", source=SCRIPT)
        restore = restore.replace("FICHIER.enc", str(encrypted))
        done = subprocess.run(
            restore, shell=True, capture_output=True,
            env={"ENCRYPTION_PASSWORD": "mauvaise-passphrase", "PATH": "/usr/bin:/bin"},
        )

        assert done.returncode != 0


class TestLegacyBackupsRemainReadable:
    """Les archives d'avant le durcissement doivent rester déchiffrables.

    Elles ont été produites sans `-pbkdf2`, donc avec EVP_BytesToKey/MD5 : leur
    lecture exige la commande *sans* ces options. Le script doit la documenter,
    sinon une restauration devient impossible le jour où elle est nécessaire.
    """

    def test_the_legacy_restore_command_is_documented_and_works(self, tmp_path):
        dump = b"-- sauvegarde d'avant le correctif\n"
        plaintext = tmp_path / "ancien.sql.gz"
        plaintext.write_bytes(gzip.compress(dump))
        encrypted = tmp_path / "ancien.sql.gz.enc"
        env = {"ENCRYPTION_PASSWORD": PASSPHRASE, "PATH": "/usr/bin:/bin"}

        # Chiffrement à l'ancienne, tel que le cron le faisait avant le correctif.
        subprocess.run(
            f'openssl enc -aes-256-cbc -salt -in {plaintext} -out {encrypted} '
            f'-pass env:ENCRYPTION_PASSWORD',
            shell=True, check=True, env=env, capture_output=True,
        )

        legacy = _extract(
            r"^#\s*RESTAURATION \(archives d'avant le durcissement\)\s*:\s*(openssl enc -d .+)$",
            "la commande de restauration des anciennes archives",
            source=SCRIPT,
        )
        legacy = legacy.replace("FICHIER.enc", str(encrypted))
        done = subprocess.run(legacy, shell=True, env=env, capture_output=True)

        assert done.returncode == 0, done.stderr.decode()
        assert done.stdout == dump


@pytest.fixture(autouse=True, scope="module")
def _openssl_is_available():
    """Ces tests exécutent openssl : sans lui, ils seraient trompeusement verts."""
    assert subprocess.run(["openssl", "version"], capture_output=True).returncode == 0

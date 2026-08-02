"""Stockage des documents PDF attachés aux activités.

Le chemin du fichier est dérivé de l'id de l'activité, jamais du nom fourni par
le client : concaténer un nom reçu au répertoire d'upload est le vecteur
classique de path traversal (`../../etc/passwd`). Le nom d'origine ne survit que
comme libellé, dans la colonne `activities.document_filename`.

Module volontairement sans dépendance à FastAPI ni à SQLAlchemy : c'est le seul
endroit qui touche au système de fichiers, et il se teste sans HTTP ni base.
"""
import os
from pathlib import Path

from config import settings

# 10 Mo. Un règlement scanné sans compression dépasse vite quelques mégaoctets ;
# au-delà, c'est un fichier qui n'a rien à faire dans un email d'adhésion.
MAX_DOCUMENT_BYTES = 10 * 1024 * 1024

PDF_MAGIC = b"%PDF"
_CHUNK = 64 * 1024
_MAX_FILENAME_LENGTH = 120


class NotAPdf(Exception):
    """Le contenu téléversé ne commence pas par la signature PDF."""


class DocumentTooLarge(Exception):
    """Le contenu téléversé dépasse `MAX_DOCUMENT_BYTES`."""


def document_path(activity_id: int) -> Path:
    return Path(settings.UPLOAD_DIR) / "activities" / f"{activity_id}.pdf"


def sanitize_filename(filename: str | None) -> str:
    """Réduit un nom fourni par le client à un libellé sûr.

    Ce nom finit dans un en-tête `Content-Disposition` et dans du HTML d'email :
    on ne garde que le basename, sans caractère de contrôle ni guillemet, borné
    en longueur. Il ne sert jamais à construire un chemin.
    """
    candidate = (filename or "").replace("\\", "/").split("/")[-1]
    candidate = os.path.basename(candidate).strip()
    candidate = "".join(
        c for c in candidate if c.isprintable() and c not in '"\r\n'
    ).strip()
    return candidate[:_MAX_FILENAME_LENGTH] or "document.pdf"


def store(activity_id: int, source) -> Path:
    """Écrit le document de l'activité et renvoie son chemin.

    `source` est un objet fichier binaire (typiquement `UploadFile.file`). Le
    contenu est lu par blocs et la taille vérifiée au fil de l'écriture : un
    `read()` complet laisserait un client imposer la consommation mémoire du
    serveur. L'écriture passe par un fichier temporaire suivi d'un `os.replace`
    atomique, pour qu'un échec en cours de route ne laisse jamais un PDF tronqué
    — ni ne détruise le document précédent.

    Lève `NotAPdf` ou `DocumentTooLarge`.
    """
    path = document_path(activity_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")

    try:
        with tmp.open("wb") as out:
            header = source.read(len(PDF_MAGIC))
            if not header.startswith(PDF_MAGIC):
                # Le `content_type` annoncé par le client ne prouve rien : seuls
                # les octets le font.
                raise NotAPdf("Le fichier n'est pas un PDF")
            out.write(header)

            total = len(header)
            while chunk := source.read(_CHUNK):
                total += len(chunk)
                if total > MAX_DOCUMENT_BYTES:
                    raise DocumentTooLarge("Le document dépasse la taille autorisée")
                out.write(chunk)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise

    os.replace(tmp, path)
    return path


def delete(activity_id: int) -> bool:
    """Supprime le document. Renvoie `False` s'il n'y en avait pas."""
    path = document_path(activity_id)
    if not path.exists():
        return False
    path.unlink()
    return True

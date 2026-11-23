import io
import os
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_UPLOAD_SIZE = 8 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
MAX_IMAGE_DIMENSION = 6000

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}

STORAGE_ROOT = Path(
    os.getenv(
        "WARDROBE_STORAGE_PATH",
        str(Path(__file__).resolve().parents[2] / "storage"),
    )
).resolve()

GARMENT_STORAGE = STORAGE_ROOT / "garments"


class ImageValidationError(Exception):
    """Erro de validação de uma imagem enviada."""


def process_image(original_bytes: bytes) -> tuple[bytes, int, int]:
    """Valida e normaliza uma imagem para WebP."""

    if not original_bytes:
        raise ImageValidationError("O arquivo enviado está vazio.")

    if len(original_bytes) > MAX_UPLOAD_SIZE:
        raise ImageValidationError("A imagem deve possuir no máximo 8 MB.")

    try:
        with Image.open(io.BytesIO(original_bytes)) as source:
            if source.format not in ALLOWED_FORMATS:
                raise ImageValidationError("Formato inválido. Envie JPEG, PNG ou WebP.")

            if getattr(source, "n_frames", 1) != 1:
                raise ImageValidationError("Imagens animadas não são permitidas.")

            width, height = source.size

            if width <= 0 or height <= 0:
                raise ImageValidationError("Dimensões inválidas.")

            if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
                raise ImageValidationError(
                    "Cada dimensão da imagem deve ter no máximo 6000 pixels."
                )

            if width * height > MAX_IMAGE_PIXELS:
                raise ImageValidationError("A imagem ultrapassa o limite de 20 megapixels.")

            source.verify()

        with Image.open(io.BytesIO(original_bytes)) as source:
            image = ImageOps.exif_transpose(source)
            image.load()

            has_alpha = image.mode in {"RGBA", "LA"} or "transparency" in image.info

            normalized = image.convert("RGBA" if has_alpha else "RGB")

            width, height = normalized.size

            output = io.BytesIO()

            normalized.save(
                output,
                format="WEBP",
                quality=85,
                method=6,
            )

            return output.getvalue(), width, height

    except ImageValidationError:
        raise

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise ImageValidationError("Não foi possível processar a imagem enviada.") from None


def save_image(image_bytes: bytes) -> str:
    """Salva uma imagem e retorna sua chave de armazenamento."""

    GARMENT_STORAGE.mkdir(parents=True, exist_ok=True)

    storage_key = f"{uuid4().hex}.webp"
    destination = GARMENT_STORAGE / storage_key

    destination.write_bytes(image_bytes)

    return storage_key


def read_image(storage_key: str) -> bytes:
    """Lê uma imagem armazenada."""

    if (
        not storage_key
        or Path(storage_key).name != storage_key
        or not storage_key.endswith(".webp")
    ):
        raise FileNotFoundError("Imagem não encontrada.")

    destination = (GARMENT_STORAGE / storage_key).resolve()

    if destination.parent != GARMENT_STORAGE.resolve():
        raise FileNotFoundError("Imagem não encontrada.")

    return destination.read_bytes()


def delete_image(storage_key: str) -> None:
    """Remove uma imagem do armazenamento."""

    if (
        not storage_key
        or Path(storage_key).name != storage_key
        or not storage_key.endswith(".webp")
    ):
        raise FileNotFoundError("Imagem não encontrada.")

    destination = (GARMENT_STORAGE / storage_key).resolve()

    if destination.parent != GARMENT_STORAGE.resolve():
        raise FileNotFoundError("Imagem não encontrada.")

    destination.unlink(missing_ok=True)

"""Private Bio-Formats archive acquisition for the OME-XML test."""

import hashlib
from http.client import HTTPException
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import time
from urllib.error import URLError
from urllib.request import urlopen

_URL = "https://downloads.openmicroscopy.org/bio-formats/8.1.0/artifacts/bftools.zip"
# SHA-256 of the 8.1.0 archive retrieved from the official HTTPS URL above.
_SHA256 = "8c80e5cc8525e17b958ca8d2d816a13342bdb64e852c5a4f981da2efd3da2ba5"


def _sha256(path: Path) -> str:
    """Return the file digest without loading the archive into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _get_bftools_archive(cache_dir: Path) -> Path:
    """Return the pinned archive, verifying both cached and downloaded bytes.

    Parameters
    ----------
    cache_dir : pathlib.Path
        Persistent directory for the Bio-Formats 8.1.0 archive. Created if absent.

    Returns
    -------
    pathlib.Path
        Path to the SHA-256-verified archive. Downloads are published atomically.

    Raises
    ------
    RuntimeError
        All three download attempts failed. Each uses a 30-second socket timeout,
        with 1- and 2-second backoff between attempts. Partial files are removed.
    OSError
        The cache cannot be read or written.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    archive = cache_dir / "bftools-8.1.0.zip"
    if archive.exists():
        if _sha256(archive) == _SHA256:
            return archive
        archive.unlink()

    with TemporaryDirectory(prefix="download-", dir=cache_dir) as staging:
        partial = Path(staging) / "bftools.zip"
        attempt = 0
        while True:
            attempt += 1
            try:
                with (
                    urlopen(_URL, timeout=30) as response,
                    partial.open("wb") as output,
                ):
                    shutil.copyfileobj(response, output)
                if _sha256(partial) != _SHA256:
                    raise ValueError("Bio-Formats archive SHA-256 mismatch")
            except (
                URLError,
                HTTPException,
                TimeoutError,
                ConnectionError,
                ValueError,
            ) as error:
                partial.unlink(missing_ok=True)
                if attempt == 3:
                    raise RuntimeError(
                        "Unable to acquire verified Bio-Formats 8.1.0 archive "
                        "after 3 attempts"
                    ) from error
                time.sleep(attempt)
            else:
                return partial.replace(archive)

"""
Trust corporate TLS inspection certificates.

Office HTTPS proxies inject a company-issued CA. Python HTTP clients
(httpx / Hugging Face Hub) verify against certifi only, so they reject
that chain as a self-signed certificate. macOS Keychain already trusts
the company CA (Safari/curl work); this module merges those certs into
the bundle httpx reads from SSL_CERT_FILE.

Python 3.13+ / OpenSSL 3 also rejects many corporate CAs for missing
Authority Key Identifier (VERIFY_X509_STRICT). That flag is cleared on
the default SSL context; verification itself stays enabled.
"""
from __future__ import annotations

import os
import ssl
import subprocess
import sys
from pathlib import Path

_CONFIGURED = False
_ORIGINAL_CREATE_DEFAULT_CONTEXT = ssl.create_default_context


def configure_ssl_for_corporate_proxy() -> Path | None:
    """Build a certifi + OS-keychain CA bundle and point SSL env vars at it.

    Safe to call more than once. Does not override SSL_CERT_FILE if the
    user already set one.

    Returns:
        Path to the combined PEM bundle, or None if certifi is unavailable.
    """
    global _CONFIGURED
    if _CONFIGURED:
        existing = os.environ.get("SSL_CERT_FILE")
        return Path(existing) if existing else None

    try:
        import certifi
    except ImportError:
        _CONFIGURED = True
        return None

    cache_dir = Path(__file__).resolve().parents[2] / "data" / "processed"
    cache_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = cache_dir / "combined-ca-bundle.pem"

    pem_parts = [Path(certifi.where()).read_text(encoding="utf-8", errors="replace")]
    if sys.platform == "darwin":
        pem_parts.extend(_export_macos_keychain_certs())

    bundle_path.write_text("\n".join(pem_parts), encoding="utf-8")

    if not os.environ.get("SSL_CERT_FILE"):
        os.environ["SSL_CERT_FILE"] = str(bundle_path)
    if not os.environ.get("REQUESTS_CA_BUNDLE"):
        os.environ["REQUESTS_CA_BUNDLE"] = os.environ["SSL_CERT_FILE"]
    if not os.environ.get("CURL_CA_BUNDLE"):
        os.environ["CURL_CA_BUNDLE"] = os.environ["SSL_CERT_FILE"]
    # Xet uses its own TLS stack and often fails on inspected networks.
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

    _relax_openssl_strict_ca_flags()

    _CONFIGURED = True
    return Path(os.environ["SSL_CERT_FILE"])


def _relax_openssl_strict_ca_flags() -> None:
    """Keep TLS verify on, but allow corporate CAs that fail OpenSSL 3 strict checks."""

    def create_default_context(*args, **kwargs):  # type: ignore[no-untyped-def]
        ctx = _ORIGINAL_CREATE_DEFAULT_CONTEXT(*args, **kwargs)
        if hasattr(ssl, "VERIFY_X509_STRICT"):
            ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
        if hasattr(ssl, "VERIFY_X509_PARTIAL_CHAIN"):
            ctx.verify_flags |= ssl.VERIFY_X509_PARTIAL_CHAIN
        return ctx

    ssl.create_default_context = create_default_context  # type: ignore[method-assign]
    ssl._create_default_https_context = create_default_context  # type: ignore[attr-defined]


def _export_macos_keychain_certs() -> list[str]:
    keychains = [
        "/Library/Keychains/System.keychain",
        "/System/Library/Keychains/SystemRootCertificates.keychain",
        str(Path.home() / "Library/Keychains/login.keychain-db"),
    ]
    exported: list[str] = []
    for keychain in keychains:
        if not Path(keychain).exists():
            continue
        try:
            result = subprocess.run(
                ["security", "find-certificate", "-a", "-p", keychain],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if result.returncode == 0 and "BEGIN CERTIFICATE" in result.stdout:
            exported.append(result.stdout)
    return exported

import os
import ssl

from src.utils.ssl_certs import configure_ssl_for_corporate_proxy


def test_configure_ssl_sets_cert_bundle_env(tmp_path, monkeypatch):
    monkeypatch.delenv("SSL_CERT_FILE", raising=False)
    monkeypatch.delenv("REQUESTS_CA_BUNDLE", raising=False)
    monkeypatch.delenv("CURL_CA_BUNDLE", raising=False)

    bundle = configure_ssl_for_corporate_proxy()

    assert bundle is not None
    assert bundle.exists()
    assert os.environ["SSL_CERT_FILE"] == str(bundle)
    ctx = ssl.create_default_context()
    if hasattr(ssl, "VERIFY_X509_STRICT"):
        assert not (ctx.verify_flags & ssl.VERIFY_X509_STRICT)

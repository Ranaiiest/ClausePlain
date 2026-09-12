"""
ClausePlain CLI — analyze a user-uploaded legal document.

    python main.py analyze path/to/contract.pdf
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.utils.ssl_certs import configure_ssl_for_corporate_proxy

configure_ssl_for_corporate_proxy()

from src.ingestion.limits import NotLegalDocumentError, UploadRejectedError
from src.product.workspace import DocumentWorkspace
from src.utils.config import load_config
from src.utils.logger import configure_logging, get_logger


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ClausePlain — explain a legal document")
    parser.add_argument("command", choices=["analyze"], help="Command to run.")
    parser.add_argument("path", help="Path to a PDF or .txt legal document.")
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument(
        "--question",
        default=None,
        help="Optional follow-up question answered from the document.",
    )
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    path = Path(args.path)
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 1

    config = load_config(args.config)
    configure_logging(log_dir=config.paths.log_dir, level=config.log_level)
    logger = get_logger(__name__)

    workspace = DocumentWorkspace(config)
    try:
        result = workspace.analyze_file(path)
    except NotLegalDocumentError as exc:
        print(f"Not a legal document: {exc}", file=sys.stderr)
        return 3
    except UploadRejectedError as exc:
        print(str(exc), file=sys.stderr)
        return 4

    if result.rejected:
        print(f"Not a legal document: {result.rejection_reason}", file=sys.stderr)
        return 3

    logger.info(
        "Analyzed '{}' with {} in {:.2f}s",
        result.contract.title,
        result.model_name,
        result.latency_seconds,
    )
    print(json.dumps(result.analysis.model_dump(), indent=2, ensure_ascii=False))

    if args.question:
        answer, q_latency = workspace.ask(
            result.contract.contract_id,
            result.contract.title,
            args.question,
        )
        print("\n--- answer ---")
        print(answer)
        logger.info("Chat answered in {:.2f}s", q_latency)
    return 0


if __name__ == "__main__":
    sys.exit(main())

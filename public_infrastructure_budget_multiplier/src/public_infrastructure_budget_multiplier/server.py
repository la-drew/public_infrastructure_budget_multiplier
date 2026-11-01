"""Small dependency-free HTTP server for the estimator and static web app."""

from __future__ import annotations

import argparse
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .model import ModelInputError, estimate_project


ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = ROOT / "web"


class RiskLabHandler(BaseHTTPRequestHandler):
    server_version = "public_infrastructure_budget_multiplier/0.1"

    def _json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if urlparse(self.path).path != "/api/estimate":
            self._json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 1_000_000:
                raise ModelInputError("Request body must be between 1 byte and 1 MB.")
            payload = json.loads(self.rfile.read(length))
            self._json(estimate_project(payload))
        except (json.JSONDecodeError, ModelInputError) as exc:
            self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception:
            self._json({"error": "The estimate could not be calculated."}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        path = urlparse(self.path).path
        if path == "/api/health":
            self._json({"status": "ok", "model_version": "0.1.0"})
            return
        if path == "/api/schema":
            self._json({
                "project_types": list(PROJECT_TYPES),
                "phases": list(PHASES),
                "delivery_methods": list(DELIVERY_METHODS),
            })
            return

        requested = "index.html" if path == "/" else path.lstrip("/")
        candidate = (WEB_ROOT / requested).resolve()
        if WEB_ROOT.resolve() not in candidate.parents and candidate != WEB_ROOT.resolve():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not candidate.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        content = candidate.read_bytes()
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


PROJECT_TYPES = ("road", "bridge", "rail", "water", "energy", "public_building", "broadband", "other")
PHASES = ("concept", "planning", "preliminary_design", "final_design", "procurement", "construction")
DELIVERY_METHODS = ("design_bid_build", "design_build", "cmgc", "p3")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run public_infrastructure_budget_multiplier")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), RiskLabHandler)
    print(f"public_infrastructure_budget_multiplier is running at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()


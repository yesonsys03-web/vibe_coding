from __future__ import annotations

import os
import socket

import uvicorn


def _port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def main() -> None:
    host = os.getenv("DOCSTYLE_API_HOST", "127.0.0.1")
    port = int(os.getenv("DOCSTYLE_API_PORT", "8000"))
    reload_flag = os.getenv("DOCSTYLE_API_RELOAD", "1") != "0"

    if _port_in_use(host, port):
        raise SystemExit(
            f"Port {port} is already in use. "
            f"Stop existing process first (e.g., lsof -nP -iTCP:{port} -sTCP:LISTEN)."
        )

    uvicorn.run("web.api:app", host=host, port=port, reload=reload_flag)


if __name__ == "__main__":
    main()

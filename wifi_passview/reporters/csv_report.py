"""CSV reporter for wifi-passview."""

from __future__ import annotations

import csv
import io
from pathlib import Path

from ..models import ScanResult

HEADERS = ["ssid", "password", "auth_type", "band", "auto_connect", "last_connected"]


def to_csv_string(result: ScanResult, redact: bool = False) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=HEADERS)
    writer.writeheader()
    for p in result.profiles:
        src = p.redact() if redact else p
        writer.writerow({
            "ssid": src.ssid,
            "password": src.password or "",
            "auth_type": src.auth_type or "",
            "band": src.band or "",
            "auto_connect": src.auto_connect if src.auto_connect is not None else "",
            "last_connected": src.last_connected or "",
        })
    return buf.getvalue()


def write(result: ScanResult, output_path: Path, redact: bool = False):
    output_path.write_text(to_csv_string(result, redact=redact), encoding="utf-8")

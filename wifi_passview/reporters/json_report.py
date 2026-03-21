"""JSON reporter for wifi-passview."""

from __future__ import annotations

import json
from pathlib import Path

from ..models import ScanResult


def to_dict(result: ScanResult, redact: bool = False) -> dict:
    profiles = []
    for p in result.profiles:
        src = p.redact() if redact else p
        profiles.append({
            "ssid": src.ssid,
            "password": src.password,
            "auth_type": src.auth_type,
            "band": src.band,
            "auto_connect": src.auto_connect,
            "last_connected": src.last_connected,
        })

    return {
        "platform": result.platform,
        "summary": {
            "total": result.total,
            "with_password": result.with_password,
            "without_password": result.without_password,
        },
        "profiles": profiles,
        "errors": result.errors,
    }


def write(result: ScanResult, output_path: Path, redact: bool = False):
    data = to_dict(result, redact=redact)
    output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def print_json(result: ScanResult, redact: bool = False):
    import click
    click.echo(json.dumps(to_dict(result, redact=redact), indent=2))

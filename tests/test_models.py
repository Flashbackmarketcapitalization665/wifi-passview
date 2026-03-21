"""Tests for wifi-passview models and platform parsers."""

from __future__ import annotations

import textwrap
import tempfile
from pathlib import Path

import pytest

from wifi_passview.models import WifiProfile, ScanResult


class TestWifiProfile:
    def test_has_password_true(self):
        p = WifiProfile(ssid="Home", password="secret123")
        assert p.has_password is True

    def test_has_password_false(self):
        p = WifiProfile(ssid="OpenWifi")
        assert p.has_password is False

    def test_redact_long_password(self):
        p = WifiProfile(ssid="Home", password="mysecretpass")
        r = p.redact()
        assert r.password.startswith("my")
        assert r.password.endswith("ss")
        assert "***" in r.password
        assert r.ssid == "Home"

    def test_redact_short_password(self):
        p = WifiProfile(ssid="Home", password="ab")
        r = p.redact()
        assert r.password == "****"

    def test_redact_none_password(self):
        p = WifiProfile(ssid="Open")
        r = p.redact()
        assert r.password is None

    def test_redact_does_not_mutate_original(self):
        p = WifiProfile(ssid="Home", password="secret123")
        r = p.redact()
        assert p.password == "secret123"
        assert r.password != "secret123"


class TestScanResult:
    def test_counts(self):
        result = ScanResult(profiles=[
            WifiProfile("Net1", password="pass1"),
            WifiProfile("Net2", password=None),
            WifiProfile("Net3", password="pass3"),
        ])
        assert result.total == 3
        assert result.with_password == 2
        assert result.without_password == 1


class TestLinuxParser:
    def test_parse_nm_file(self, tmp_path):
        from wifi_passview.platforms.linux import _parse_nm_file

        conf = tmp_path / "HomeNetwork.nmconnection"
        conf.write_text(textwrap.dedent("""
            [connection]
            id=HomeNetwork
            type=wifi
            autoconnect=yes

            [wifi]
            ssid=HomeNetwork

            [wifi-security]
            key-mgmt=wpa-psk
            psk=supersecret123
        """))

        result = ScanResult(platform="linux")
        _parse_nm_file(conf, result)

        assert len(result.profiles) == 1
        assert result.profiles[0].ssid == "HomeNetwork"
        assert result.profiles[0].password == "supersecret123"
        assert result.profiles[0].auth_type == "wpa-psk"
        assert result.profiles[0].auto_connect is True

    def test_parse_nm_file_no_wifi_section(self, tmp_path):
        from wifi_passview.platforms.linux import _parse_nm_file

        conf = tmp_path / "vpn.nmconnection"
        conf.write_text(textwrap.dedent("""
            [connection]
            id=MyVPN
            type=vpn
        """))

        result = ScanResult(platform="linux")
        _parse_nm_file(conf, result)
        assert len(result.profiles) == 0

    def test_parse_wpa_supplicant(self, tmp_path):
        from wifi_passview.platforms import linux

        wpa_conf = tmp_path / "wpa_supplicant.conf"
        wpa_conf.write_text(textwrap.dedent("""
            ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
            update_config=1

            network={
                ssid="CoffeeShopWifi"
                psk="latteplease"
                key_mgmt=WPA-PSK
            }

            network={
                ssid="GuestNetwork"
                key_mgmt=NONE
            }
        """))

        # Temporarily patch the path list
        original = linux.WPA_SUPPLICANT_PATHS
        linux.WPA_SUPPLICANT_PATHS = [wpa_conf]

        result = ScanResult(platform="linux")
        linux._try_wpa_supplicant(result)

        linux.WPA_SUPPLICANT_PATHS = original

        assert len(result.profiles) == 2
        coffee = next(p for p in result.profiles if p.ssid == "CoffeeShopWifi")
        assert coffee.password == "latteplease"
        guest = next(p for p in result.profiles if p.ssid == "GuestNetwork")
        assert guest.password is None

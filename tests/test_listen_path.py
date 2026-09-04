"""LocalNet recreate + listen path guards. No algod, no mnemonic, no spend."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text()
LISTEN_SRC = (ROOT / "scripts" / "localnet_listen.py").read_text()
RECREATE_SRC = (ROOT / "scripts" / "localnet_recreate.py").read_text()
DEPLOY = json.loads((ROOT / "docs" / "deploy.json").read_text())
LOCALNET = json.loads((ROOT / "docs" / "localnet.json").read_text())
LISTEN = json.loads((ROOT / "docs" / "listen.json").read_text())

BANK = "IFZZOTEBLLAV7DA4WP7IPZWZW67KXB5ZNYLZAWJ2S6M3KKNAX55BRXVK2Y"
# Ephemeral LocalNet ids from older proofs must never leak into deploy.json.
FORBIDDEN_LOCALNET_COPY = {1001, 1002, 1003, 1004, 1005, 1110, 1131, 1170, 1171, 1202, 1203, 1257, 1258}


def test_deploy_json_never_holds_localnet_ids() -> None:
    assert DEPLOY["network"] == "testnet"
    assert DEPLOY["appId"] == 0
    assert DEPLOY["upkeepId"] == 0
    assert DEPLOY.get("executeTxid", "") == ""
    assert DEPLOY.get("reportTxid", "") == ""
    assert DEPLOY["hook"] == "watch()uint64"
    assert DEPLOY["appId"] not in FORBIDDEN_LOCALNET_COPY
    assert DEPLOY["appId"] != int(LOCALNET["appId"])
    assert DEPLOY["appId"] != int(LISTEN["appId"])
    assert DEPLOY["appId"] != int(LISTEN.get("mockKeeperAppId") or -1)
    # LocalNet app ids must not appear anywhere in TestNet deploy.json.
    blob = json.dumps(DEPLOY)
    assert str(LOCALNET["appId"]) not in blob
    assert str(LISTEN.get("mockKeeperAppId")) not in blob


def test_localnet_json_schema_fields() -> None:
    required = {
        "network",
        "genesisId",
        "algod",
        "appId",
        "appAddress",
        "createTxid",
        "confirmedRound",
        "creator",
        "contract",
        "source",
        "notes",
    }
    assert required.issubset(LOCALNET.keys())
    assert LOCALNET["network"] == "localnet"
    assert LOCALNET["genesisId"] == "dockernet-v1"
    assert LOCALNET["algod"] == "http://localhost:4001"
    assert LOCALNET["contract"] == "Watchdog"
    assert LOCALNET["source"] == "smart_contracts/watchdog/contract.py"
    assert int(LOCALNET["appId"]) > 0
    assert int(LOCALNET["confirmedRound"]) > 0
    assert isinstance(LOCALNET["createTxid"], str) and len(LOCALNET["createTxid"]) >= 40
    assert isinstance(LOCALNET["appAddress"], str) and len(LOCALNET["appAddress"]) >= 50
    assert "Do NOT copy this appId into docs/deploy.json" in LOCALNET["notes"]
    assert "81" in LOCALNET["notes"] and "87" in LOCALNET["notes"]
    assert BANK not in json.dumps(LOCALNET)
    assert "testnet" not in LOCALNET["genesisId"].lower()
    assert "mainnet" not in LOCALNET["genesisId"].lower()


def test_listen_json_schema_and_watchdog_calls() -> None:
    required = {
        "network",
        "genesisId",
        "algod",
        "appId",
        "appAddress",
        "mockKeeperAppId",
        "mockKeeperCreateTxid",
        "mockKeeperConfirmedRound",
        "creator",
        "lastRound",
        "calls",
        "global",
        "notes",
    }
    assert required.issubset(LISTEN.keys())
    assert LISTEN["network"] == "localnet"
    assert LISTEN["genesisId"] == "dockernet-v1"
    assert LISTEN["algod"] == "http://localhost:4001"
    assert int(LISTEN["appId"]) == int(LOCALNET["appId"])
    assert LISTEN["appAddress"] == LOCALNET["appAddress"]
    assert int(LISTEN["mockKeeperAppId"]) > 0
    assert int(LISTEN["mockKeeperAppId"]) != int(LISTEN["appId"])
    assert int(LISTEN["lastRound"]) >= int(LOCALNET["confirmedRound"])

    methods = [c["method"] for c in LISTEN["calls"]]
    assert methods == ["set_keeper", "set_max_age", "report", "watch"]
    assert all(c.get("success") is True for c in LISTEN["calls"])
    assert all(
        isinstance(c.get("txid"), str) and len(c["txid"]) >= 40 for c in LISTEN["calls"]
    )
    assert all(int(c.get("round") or 0) > 0 for c in LISTEN["calls"])

    report = next(c for c in LISTEN["calls"] if c["method"] == "report")
    assert report["via"] == "interested_party_pull"
    assert report["hook"] == "report"
    assert int(report["value"]) == 42

    watch = next(c for c in LISTEN["calls"] if c["method"] == "watch")
    assert watch["via"] == "mock_keeper.watch"
    assert watch["hook"] == "watch"
    assert int(watch["innerCount"]) >= 1
    assert int(watch["targetAppId"]) == int(LISTEN["appId"])

    g = LISTEN["global"]
    assert int(g["last_value"]) == 42
    assert int(g["stale"]) == 0
    assert int(g["watch_count"]) >= 1
    assert int(g["last_watch_round"]) > 0
    assert int(g["last_report_round"]) > 0
    assert int(g["keeper_app"]) == int(LISTEN["mockKeeperAppId"])
    assert int(g["max_age"]) == 1000
    assert "Do NOT copy this appId into docs/deploy.json" in LISTEN["notes"]
    assert "81" in LISTEN["notes"] and "87" in LISTEN["notes"]
    assert BANK not in json.dumps(LISTEN)


def test_listen_and_recreate_scripts_stay_on_localhost() -> None:
    for src in (LISTEN_SRC, RECREATE_SRC):
        assert 'ALGOD_URL = "http://localhost:4001"' in src
        assert 'KMD_URL = "http://localhost:4002"' in src
        assert "testnet-api" not in src
        assert "mainnet-api" not in src
        assert "Never writes docs/deploy.json" in src
        assert "refuse_wrong_network" in src
        assert 'if "testnet" in g:' in src
        assert 'if "mainnet" in g:' in src
        assert f'BANK = "{BANK}"' in src
        assert "if addr == BANK:" in src
        assert "DEPLOY_JSON.write_text" not in src
        assert "mnemonic" not in src.lower() or "never" in src.lower()


def test_listen_script_writes_listen_json_only() -> None:
    assert "LISTEN_JSON.write_text" in LISTEN_SRC
    assert "OUT.write_text" in RECREATE_SRC  # localnet.json
    assert re.search(r"DEPLOY_JSON\.write", LISTEN_SRC) is None
    assert re.search(r"DEPLOY_JSON\.write", RECREATE_SRC) is None
    assert "mock_keeper.watch" in LISTEN_SRC or "MK_WATCH" in LISTEN_SRC
    # Mock keeper entry is watch(uint64)void (target app id); hook itself is watch()uint64.
    assert 'Method.from_signature("watch(uint64)void")' in LISTEN_SRC
    assert 'Method.from_signature("report(uint64)uint64")' in LISTEN_SRC
    assert 'Method.from_signature("set_max_age(uint64)void")' in LISTEN_SRC
    assert 'Method.from_signature("set_keeper(uint64)void")' in LISTEN_SRC


def test_readme_localnet_proof_matches_json() -> None:
    """README LocalNet proof paragraph must match docs/localnet.json + listen.json."""
    app_id = int(LOCALNET["appId"])
    create_round = int(LOCALNET["confirmedRound"])
    mock_id = int(LISTEN["mockKeeperAppId"])
    last_watch = int(LISTEN["global"]["last_watch_round"])
    last_round = int(LISTEN["lastRound"])

    assert f"**appId {app_id}**" in README
    assert f"confirmed round **{create_round}**" in README
    assert f"mock keeper **{mock_id}**" in README
    assert f"last_watch_round={last_watch}" in README
    assert f"last-round after listen: {last_round}" in README
    assert "last_value=42" in README
    assert "stale=0" in README
    assert "watch_count=1" in README

    assert "docs/localnet.json" in README
    assert "docs/listen.json" in README
    assert "LocalNet ids are ephemeral" in README
    assert "Do **not** copy any LocalNet app id into `docs/deploy.json`" in README
    assert "`appId` stays 0 until a real TestNet create" in README
    assert "scripts/localnet_recreate.py" in README
    assert "scripts/localnet_listen.py" in README
    # Live TestNet table stays honest zeros.
    assert "appId 0" in README or "appId stays 0" in README
    assert "**not done**" in README


def test_go_localnet_proof_cli_exists() -> None:
    """Offline Go CLI reads localnet/listen JSON; asserts deploy appId stays 0."""
    main = ROOT / "cmd" / "localnet-proof" / "main.go"
    assert main.is_file()
    body = main.read_text()
    assert "deploy.json" in body
    assert "appId" in body
    assert "no mnemonic" in body.lower() or "No mnemonic" in body
    assert "no algod" in body.lower() or "no network" in body.lower()
    assert (ROOT / "go.mod").is_file()
    assert "github.com/corvid-agent/arcron-oracle-watchdog" in (ROOT / "go.mod").read_text()

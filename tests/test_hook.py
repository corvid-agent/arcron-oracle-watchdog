"""Static checks that the hook rules hold. No TestNet, no mnemonic."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "smart_contracts" / "watchdog" / "contract.py").read_text()
README = (ROOT / "README.md").read_text()


def test_hook_is_zero_arg() -> None:
    assert "def watch(self) -> UInt64:" in SRC
    assert "def watch(self, " not in SRC


def test_watch_takes_no_oracle_value() -> None:
    """The scheduled call cannot be handed a price. Selector only."""
    start = SRC.index("def watch(self)")
    end = len(SRC)
    body = SRC[start:end]
    assert "value" not in body.split(":", 1)[0]
    assert "last_value.value =" not in body


def test_report_is_the_pull() -> None:
    assert "def report(self, value: UInt64) -> UInt64:" in SRC
    report = SRC[SRC.index("def report(") : SRC.index("def watch(")]
    assert "self.last_value.value = value" in report


def test_auth_uses_application_address_not_itob() -> None:
    assert "Application(keeper).address" in SRC
    assert "itob(" not in SRC


def test_keeper_id_is_not_hardcoded_in_the_contract() -> None:
    assert "769891898" not in SRC


def test_create_does_not_take_the_keeper() -> None:
    assert "def create(self) -> None:" in SRC
    assert "def create(self, " not in SRC
    assert "def set_keeper(self, keeper: Application) -> None:" in SRC


def test_unconfigured_watch_returns_rather_than_asserting() -> None:
    start = SRC.index("def watch(self)")
    body = SRC[start:]
    assert "if keeper == 0 or max_age == 0:" in body
    assert "return count" in body


def test_readme_says_keeper_supplies_no_oracle_data() -> None:
    assert "the keeper supplies no oracle data" in README.lower()

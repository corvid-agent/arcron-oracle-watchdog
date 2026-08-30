# pyright: reportMissingModuleSource=false
"""Staleness watchdog on Algorand TestNet.

Pull pattern: Arcron's scheduled call only accounts whether the last report is
stale. The interested party brings the outside reference on-chain in their own
`report` transaction. Readers pull global state in theirs. The keeper supplies
no data.

TestNet only. Unaudited. Not a product. Do not send real funds.

TRAP: a sloppy deploy that mapped every uint64 create-arg onto the TestNet
keeper app id would freeze a cadence at ~68 years. `create()` takes zero
arguments. The keeper is named once via `set_keeper(app)`. Interval and
max-age are not constructor args. Do not compare the inner sender against
itob of the keeper id — that is 8 bytes, not an address. Auth is
Application(keeper_app).address.
"""

from algopy import (
    ARC4Contract,
    Application,
    Global,
    GlobalState,
    Txn,
    UInt64,
)
from algopy.arc4 import abimethod


class Watchdog(ARC4Contract):
    """Accounts staleness on a schedule. Interested party pulls the value in.

    TestNet only. Unaudited.
    """

    def __init__(self) -> None:
        self.last_value = GlobalState(UInt64(0))
        self.last_report_round = GlobalState(UInt64(0))
        self.stale = GlobalState(UInt64(0))
        self.last_watch_round = GlobalState(UInt64(0))
        self.watch_count = GlobalState(UInt64(0))
        self.keeper_app = GlobalState(UInt64(0))
        self.max_age = GlobalState(UInt64(0))
        self.min_rounds = GlobalState(UInt64(0))

    @abimethod(create="require")
    def create(self) -> None:
        """No-op create. Zero arguments on purpose.

        A create_arg of type uint64 is how a sloppy deploy script confused the
        keeper app id with a cadence. There is nothing to pass here.
        """
        self.last_value.value = UInt64(0)
        self.last_report_round.value = UInt64(0)
        self.stale.value = UInt64(0)
        self.last_watch_round.value = UInt64(0)
        self.watch_count.value = UInt64(0)
        self.keeper_app.value = UInt64(0)
        self.max_age.value = UInt64(0)
        self.min_rounds.value = UInt64(30)  # integrating.md floor for lateness-as-signal

    @abimethod()
    def set_keeper(self, keeper: Application) -> None:
        """Name the Arcron keeper whose app account may call `watch`.

        Creator only, once. Pass the keeper *application*, store `.id`.
        `watch` authorizes Application(keeper).address — the inner-call
        sender when Arcron execute() inner-calls this app — never
        itob of the keeper id.
        """
        assert Txn.sender == Global.creator_address, "Only the creator can set the keeper"
        assert self.keeper_app.value == 0, "Keeper already set"
        assert keeper.id != 0, "Keeper app required"
        self.keeper_app.value = keeper.id

    @abimethod()
    def set_max_age(self, rounds: UInt64) -> None:
        """How many rounds a report may age before `watch` marks it stale.

        Creator only. A round count, not a wall-clock, not a keeper app id.
        """
        assert Txn.sender == Global.creator_address, "Only the creator can set max age"
        assert rounds > 0, "max_age must be > 0"
        self.max_age.value = rounds

    @abimethod()
    def report(self, value: UInt64) -> UInt64:
        """Interested party pulls an outside reference on-chain.

        Anyone may call this. The keeper does not. Arcron does not pass a
        value: the hook is zero-arg. Clears `stale` and stamps `last_report_round`.
        """
        self.last_value.value = value
        self.last_report_round.value = Global.round
        self.stale.value = UInt64(0)
        return value

    @abimethod()
    def watch(self) -> UInt64:
        """Arcron hook. Zero arguments; selector is the only app arg.

        Accounting only: sets `stale` from last_report_round vs max_age.
        Moves nothing, calls nothing, names no extra accounts. Fail-soft:
        unconfigured or too-soon returns rather than rejects, so a keeper
        is not backed off for a no-work call.
        """
        keeper: UInt64 = self.keeper_app.value
        max_age: UInt64 = self.max_age.value
        count: UInt64 = self.watch_count.value
        if keeper == 0 or max_age == 0:
            return count

        # Inner-call sender is the keeper *app account*, not itob of the keeper id.
        assert (
            Txn.sender == Application(keeper).address
        ), "Only the keeper app may watch"

        last_watch: UInt64 = self.last_watch_round.value
        min_rounds: UInt64 = self.min_rounds.value
        current: UInt64 = Global.round
        if last_watch != 0 and current < last_watch + min_rounds:
            return count

        last_report: UInt64 = self.last_report_round.value
        if last_report == 0 or current > last_report + max_age:
            self.stale.value = UInt64(1)
        else:
            self.stale.value = UInt64(0)

        self.last_watch_round.value = current
        count = count + 1
        self.watch_count.value = count
        return count

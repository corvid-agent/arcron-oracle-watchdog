# pyright: reportMissingModuleSource=false
"""LocalNet-only mock Arcron keeper for watchdog.

Inner-calls Watchdog.watch() so Txn.sender on the target is this app address.
Not a product. Not for TestNet. Never copy this app id into docs/deploy.json.
"""

from algopy import ARC4Contract, Application, Global, OnCompleteAction, itxn
from algopy.arc4 import abimethod, arc4_signature


class MockKeeper(ARC4Contract):
    """Inner-calls watchdog.watch()uint64."""

    @abimethod()
    def watch(self, app: Application) -> None:
        itxn.ApplicationCall(
            app_id=app,
            app_args=(arc4_signature("watch()uint64"),),
            apps=(Global.current_application_id,),
            on_completion=OnCompleteAction.NoOp,
        ).submit()

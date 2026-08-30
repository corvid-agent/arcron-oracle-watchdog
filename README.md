# arcron-oracle-watchdog

TestNet Arcron watchdog that accounts staleness on a schedule while the interested party pulls the outside reference in their own transaction.

## Live proof

**not done** — this commit ships the compiling contract, CI, and Pages stub. Live TestNet create / register / execute were not confirmed (dispenser captcha/401), so ids are zeros. Never invent txids.

| item | value |
|------|-------|
| app id | **not done** (`docs/deploy.json` appId 0) |
| upkeep id on 769891898 | **not done** |
| execute txid (keeper called `watch`) | **not done** |
| report txid (interested party pulled) | **not done** |
| keeper | [769891898](https://testnet.explorer.perawallet.app/application/769891898) live, frozen=0 |
| Pages | https://corvid-agent.github.io/arcron-oracle-watchdog/ (publishes `docs/` from `main`) |

## How to run

TestNet only. Throwaway account, public TestNet dispenser. No mnemonic in this repo.

1. `pip install puyapy`
2. Compile: `puyapy smart_contracts/watchdog/contract.py --out-dir smart_contracts/artifacts/watchdog --resource-encoding value`
3. Create with **ZERO** args (`create()void`). Do not pass a uint64. Mapping every uint64 onto 769891898 would freeze a cadence at ~68 years.
4. `set_keeper(Application(769891898))` — pass the application, store `.id`. Auth on the hook is `Application(keeper_app).address`, never `itob(keeper_id)`.
5. `set_max_age(rounds)` — creator. Round count, not a keeper id.
6. Register on keeper 769891898 with **SKIP_AHEAD** (CATCH_UP is encoded as 0 and is the wrong default). Hook `watch()uint64`, selector only. `interval_rounds` at least 30, `fee_per_execution` at least 4,000 µALGO. Cadence is a register field, not a constructor arg.
7. Interested party calls `report(value)` in their own transaction. That is the outside reference. The keeper never carries it.
8. Readers pull `last_value` / `stale` / `last_report_round` from global state in their own transactions.

## Measured cost

Not measured here (no confirmed TestNet deploy). Arcron's own figures, from `docs/integrating.md` in CorvidLabs/arcron, not this demo:

| item | µALGO |
|------|-------|
| box MBR (bare 4-byte selector) | ≈ 62,100 (`2,500 + 400 × (139 + len(encoded call_args))`) |
| per execution floor | 4,000 (`MIN_UPKEEP_FEE`) |
| live spend of this app | **not done** |

## What does not work

- No TestNet create, no upkeep, no execute. Dispenser captcha/401. appId stays 0.
- Pages board is a stub until `docs/deploy.json` `appId` is flipped after a real create.
- CI is compile + grep guards, not a LocalNet execute.
- The hook cannot fetch an off-chain price. That is the point: the keeper supplies no data. If `report` never runs, `watch` marks stale and returns.
- TestNet keeper 769891898 may be late. Interval floor 30 so ordinary lateness is not treated as a signal.

## Honesty block

Unaudited. TestNet only. First-party demo, not a product. No MainNet path; this repo will refuse one. Do not send mainnet funds. Keeper 769891898. Throwaway dispenser. Apache-2.0. Pull pattern: the schedule accounts; the interested party pulls; the keeper supplies no data. Hook is `watch()`, zero args. Auth is `Application(keeper).address`, never `itob`.

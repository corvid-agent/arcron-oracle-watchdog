# arcron-oracle-watchdog

TestNet Arcron watchdog that accounts staleness on a schedule while the interested party pulls the outside reference in their own transaction.

## The keeper supplies no oracle data

The keeper supplies no oracle data. Arcron `execute` inner-calls `watch()` with the method selector only: no price, no feed, no bytes from the keeper. `watch` only accounts whether the last `report` is older than `max_age`. The interested party brings the outside reference in their own `report(value)` transaction. Readers pull global state in theirs.


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

LocalNet proof for Pages lives in `docs/localnet.json` and `docs/listen.json` (CRT shows them when present). `docs/history.json` appends LocalNet listen samples for the phosphor staleness / last-report / watch-count graphs (in-page sql.js). `node scripts/append_history.mjs` appends from `listen.json` without touching `deploy.json`. `docs/deploy.json` stays honest TestNet `appId: 0`.

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

## LocalNet recreate + listen (not TestNet)

Create, `set_keeper(Application(...))`, `set_max_age`, an interested-party `report(value)`, and a mock-keeper inner-call of `watch()` were proven on AlgoKit LocalNet (`dockernet-v1`). That is **not** TestNet. Do **not** copy any LocalNet app id into `docs/deploy.json` or treat it as TestNet. TestNet `appId` stays 0 until a real TestNet create.

This pass (2026-09-04 midday MT): `python scripts/localnet_recreate.py` created Watchdog **appId 1025** at confirmed round **19** (`createTxid` in `docs/localnet.json`). Then `python scripts/localnet_listen.py` created mock keeper **1026**, set_keeper, set_max_age(1000), interested-party `report(42)`, and inner-called `watch` (1 inner). Global after listen: last_value=42, stale=0, watch_count=1, last_watch_round=25. LocalNet last-round after listen: 25. Did not spend the TestNet bank. Did not poke upkeep 81 or 87. LocalNet was reset (last-round ~18); prior appIds 1257/1258 are gone.

LocalNet ids are ephemeral (DevMode / reset). They are not a product. They are not TestNet explorer links.
LocalNet proof for Pages lives in `docs/localnet.json` and `docs/listen.json` (CRT shows them when present). `docs/deploy.json` stays honest TestNet `appId: 0`.

```bash
# Docker daemon required
algokit localnet start
# wait until localhost:4001 /v2/status answers

pip install puyapy py-algorand-sdk
python scripts/localnet_recreate.py
# writes docs/localnet.json with network:"localnet" and the new appId
python scripts/localnet_listen.py
# set_keeper + set_max_age + report(42) + mock watch; writes docs/listen.json
```

Both scripts talk only to `localhost:4001` / `4002`, sign with the LocalNet KMD
`unencrypted-default-wallet` (never print a mnemonic), refuse TestNet/MainNet
genesis ids, refuse signing as the TestNet bank, and never modify `docs/deploy.json`.

Optional offline check (no algod, no mnemonic): `go run ./cmd/localnet-proof` reads
`docs/localnet.json` + `docs/listen.json` and asserts `docs/deploy.json` still has `appId` 0.

DevMode holds last-round at 0 until the first tx. A successful create is a confirmed
`application-index` on genesis id `dockernet-v1`, not a TestNet explorer link.


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
- CI is compile + static hook/honesty tests. LocalNet recreate/listen (set_keeper, set_max_age, report, mock watch) are proven on the box against localhost:4001; they are not TestNet.
- The hook cannot fetch an off-chain price. That is the point: the keeper supplies no data. If `report` never runs, `watch` marks stale and returns.
- TestNet keeper 769891898 may be late. Interval floor 30 so ordinary lateness is not treated as a signal.

## Honesty block

Unaudited. TestNet only. First-party demo, not a product. No MainNet path; this repo will refuse one. Do not send mainnet funds. Keeper 769891898. Throwaway dispenser. Apache-2.0. Pull pattern: the schedule accounts; the interested party pulls; the keeper supplies no data. Hook is `watch()`, zero args. Auth is `Application(keeper).address`, never `itob`.

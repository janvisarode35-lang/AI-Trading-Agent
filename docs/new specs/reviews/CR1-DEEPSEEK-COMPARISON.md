# CR-1: Claude and DeepSeek compared

Date: 2026-10-18. Same input for both: `paste-ready/CR1-PDT-PASTE.txt` (SHA-256
`a34d2455…0022950`). Claude's result: `docs/new specs/SPEC-CR1-US-DAY-TRADING.md` with its patch and
test. DeepSeek's result: `paste-ready/outputs/CR1-DEEPSEEK-raw.txt` (web chat, Search on, DeepThink
off; the saved text was checked against the page by SHA-256).

## Where they agree

| Point | Claude | DeepSeek |
|-------|--------|----------|
| The USD 25,000 PDT floor is no longer FINRA's rule | Yes, from FINRA's rule text, Notice 26-10 and the SEC order | Yes, from search snippets |
| Effective 2026-06-04; phase-in to 2027-10-20 | Yes | Yes (but see D-1) |
| Brokers may keep the old rule during the phase-in | Yes, from the SEC order's own words | Yes, from a broker summary |
| Alpaca lifted PDT | Yes (Alpaca blog, 2026-06-04) | Yes (Alpaca docs, via search) |
| USD 2,000 margin minimum unchanged; new 90-day freeze with the lesser of 5% or USD 1,000 exclusion | Yes | Yes |
| Cash accounts: settled funds and good-faith violations, not PDT; T+1 | Yes, with 12 CFR 220.2, 220.8 and 17 CFR 240.15c6-1 | Yes, no CFR citations |
| Do not pin 25,000 as a live value | Yes | Yes |

## Where DeepSeek is wrong or weaker

| # | Point | Effect |
|---|-------|--------|
| D-1 | Its register row says the phase-in ends **2026-10-20**; its own text and test say 2027-10-20. | Its diff would write a wrong regulatory date into a frozen register. |
| D-2 | It calls investor.gov "FINRA's own investor education site". It is the SEC's. | Citation error. |
| D-3 | No primary source fetched, no SEC release number (it lists it as an open question). Claude has Release No. 34-105226, 91 FR 20731. | DeepSeek's entries cannot be audited as primary-sourced; it says so itself. |
| D-4 | Legacy counting "per round trip", "Interpretation /02", and "equity checked at the end of the session of the fourth day trade" are stated without a source. FINRA deleted those interpretations (Notice 26-10, endnote 2). | Unverifiable statements about the legacy rule; Claude flags the deletion and over-counts instead ([DEFAULT-57]). |
| D-5 | Its test imports modules that do not exist (`provider.enums`, `provider.spec`), checks an input name the policy does not use (`day_trade_count`; the policy says `day_trades_5d`), and never looks at `account.pdt_equity_floor_usd: 25000` in `config/policy.yaml`, the place the obsolete number actually lives. Its register test requires `PDT-1` in `STAGE-0-FREEZE.md`, so it fails until a frozen historical file is edited. | The test would error on import, and the live 25,000 slips past it. Claude's test passes now and was shown to fail on three mutations. |
| D-6 | It places a resolved item in §6.2 "OPEN — carried, not gating" and adds no §9 change-log entry. `STAGE-0-FREEZE.md` §8 says a change without a §9 entry "has not happened". | Its diff breaks the freeze's own amendment rule. Claude's patch adds §6.5 and a §9 row, and passes `git apply --check`. |
| D-7 | It reads #33 as gap-audit G-2 and cannot identify #19. They are GitHub issues: #19 is P3.2 Execution, #33 is P6.3 Compliance. | Its "unblocked" answer is about the wrong items. |
| D-8 | It did not have the Model B records in its input, so it treats the system as still trading. | Expected from its input; Claude states that v1 sends no orders (CR1-P2). |

## What DeepSeek adds

| # | Point | Disposition |
|---|-------|-------------|
| A-1 | The legacy definition reportedly also required day trades to exceed 6% of the account's trades in the window. | Added to the spec as OQ-CR1-5; not verified. The over-count of [DEFAULT-57] is unaffected. |
| A-2 | An explicit "if the account is ever misconfigured as margin, deny everything" rule for a cash-account design. | Not adopted: the new run's US account is a margin account run with zero borrowing ([DEFAULT-16]), so the guard is AMD-4's settled-cash limit instead. |
| A-3 | Ask IBKR whether it still applies the legacy rule. | Covered by [DEFAULT-55]: a broker without a verified record is treated as enforcing it. |

## Verdict

Same conclusion. Claude's version is the one to keep: primary-sourced, with the correct phase-in
date in the register diff, and a test that runs and pins the values.

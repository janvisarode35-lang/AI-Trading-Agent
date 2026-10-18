claude.ai chat (Opus 5.5, Medium), new chat, run 2026-10-18 from the Claude desktop browser pane.
Input: paste-ready/CR1-PDT-PASTE.txt (187,956 characters, SHA-256 a34d2455...0022950), rebuilt in
the page from commit 1ef1777 and hash-checked before sending; it arrived as one "Pasted text.txt"
attachment. Chat: https://claude.ai/chat/0558d9e9-a17e-40ba-b167-4b7e989f4b6e
The chat used web search (5 searches, 1 site read) and produced three files in its own sandbox,
saved beside this one: SPEC-P2.9-US-DAYTRADE-REG.md, us_daytrade.py, verify_us_daytrade_reg.py.
Text below is the chat's final answer as stored by claude.ai (markdown).
==========================================================================================

I'll verify the PDT threshold against FINRA and SEC primary sources first, because the number may have changed in 2025–2026.

I'm writing the pinned-facts module first so the test can pin its hash.

You asked me to verify a number that no longer exists, so the useful output is a retirement record, not a verification.

**What I found**
- [Certain] The $25,000 PDT floor in Rule 4210(f)(8)(B)(iv)a. was real. It is now gone. On April 14, the SEC approved SR-FINRA-2025-017, replacing the day trading margin requirements under Rule 4210, including the pattern-day-trader count requirements and the $25,000 minimum equity requirement.
- [Certain] The effective date was June 4, 2026. Firms needing more time may phase in over 18 months, until October 20, 2027. The amendments eliminate paragraph (f)(8)(B), along with associated provisions in paragraphs (b), (f)(10) and (g)(13). The SEC order is Release No. 105226, 91 FR 20731.
- [Certain] The PDT rule was a margin-account rule, and so is its replacement. The new intraday margin calculation applies to each customer margin account other than good-faith and portfolio-margin accounts. ADR-12 makes your US account a cash account, so the $25,000 floor never governed you.
- [Certain] What does govern a cash account is Reg T. If a security is sold before it was paid for in full, the privilege of delaying payment beyond trade date is withdrawn for 90 calendar days.

**What I built**
- **REGT-001.** Every entry must be funded from settled cash only. That makes free-riding and good-faith violations impossible by construction, which downgrades M-6 to informational.
- **REGT-002.** Any broker restriction, including a leftover PDT flag during a broker's phase-in, denies new entries. Re-enabling requires a human.
- **Day-trade count.** Kept as monitor-only telemetry. [Guessing] The multi-fill counting convention is labelled an ASSUMPTION, because FINRA deleted those interpretations.
- **Register.** The diff adds a new §6.5 to STAGE-0-FREEZE for regulatory values.
- **Test.** It pins a SHA-256 over all the regulatory facts and lints `src/` and `config/` for any live PDT value of 25,000. All 16 checks pass under `python -O`. I confirmed it catches a change: setting the floor to 25,001 fails two checks.

**Where this conflicts with your rules**
- Invariant 9 requires "US PDT handling". That rule no longer exists, so I proposed amendment A-PDT-1 for the Owner to decide. I did not quietly reword the invariant.

**What I could not determine**
- **#19 and #33.** Neither appeared in what you pasted, so I can't say which one this unblocks. G-2's own listed blockers, P3.2 and P6.3, are both unblocked.
- **#16 / Q-P1.1-1 condition 3.** I don't have the text, so I can't confirm condition 3 is satisfied.
- **Alpaca details.** [Likely] Alpaca says it migrated on June 4, but that comes from its forum, not its API docs. Its account field names for settled cash and restrictions are an open question. I did not guess them.
- **T+1 source.** [Certain] T+1 settlement itself is verified. I cited law-firm summaries of SEC Release 34-96930 rather than the SEC PDF.

**Two things to check in your repo**
- `policy.yaml` already has a rule called `CASH-001`. Check whether REGT-001 duplicates it.
- If you edit a pinned file and rerun within the same second, clear `__pycache__` first. A stale cached copy briefly made my own test report the old value.

Sources:
- [FINRA weekly update, 2026-04-15](https://www.finra.org/compliance-tools/weekly-archive/04152026)
- [FINRA Regulatory Notice 26-10](https://www.finra.org/sites/default/files/2026-04/Regulatory-Notice-26-10.pdf)
- [SEC Release 34-42418 (original $25,000 text)](https://www.sec.gov/rule-release/34-42418)
- [FINRA Regulatory Notice 21-24](https://www.finra.org/rules-guidance/notices/21-24)
- [12 CFR 220.8 (eCFR)](https://www.ecfr.gov/current/title-12/chapter-II/subchapter-A/part-220/section-220.8)
- [Davis Polk on T+1](https://www.davispolk.com/insights/client-update/sec-adopts-t-1-settlement-effective-may-2024)
- [Alpaca forum thread](https://forum.alpaca.markets/t/pdt-change-approved-when-will-changes-take-effect/18701)

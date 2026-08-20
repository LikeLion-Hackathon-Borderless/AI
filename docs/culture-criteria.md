# Cross-Cultural Ambiguity Criteria for Async Work Messages

This document defines the 16 phrase-level ambiguity patterns that `ditto` detects,
the research basis behind them, and how they informed both the few-shot prompt and
the evaluation (golden) set used to measure model accuracy.

## Design Principles

- **Source**: four of Erin Meyer's *The Culture Map* axes that map directly onto
  async text messages — Scheduling, Evaluating, Disagreeing, and Communicating.
- **Classification**: each item is labeled either **bidirectional** (equally
  ambiguous regardless of sender/receiver direction) or **direction-specific**
  (the pattern shows up differently depending on who is sending to whom).
- **Framing discipline**: no item asserts that a nationality "always" interprets a
  phrase a certain way — every entry is phrased as a *possible* reading, validated
  or refined against real survey data (below), not asserted from literature alone.

## How the Golden Set Was Built — Survey-Grounded, Not Assumed

Literature review alone tells you a phrase *might* be ambiguous; it doesn't tell
you whether Korean speakers actually disagree about what it means. To close that
gap, each of the 16 candidate items was tested with a domestic survey (Korean
office workers and students, n=12–15 per axis) before being locked into the
prompt or the evaluation set:

- Respondents read each ambiguous phrase and picked among 2–3 candidate
  interpretations, plus rated how often they'd actually been confused by it in
  real work.
- **Genuinely ambiguous** (kept as-is, used to build both the few-shot examples
  and the golden set's "ambiguous" test cases): interpretations split with
  standard deviation ≥ 1.7, or two candidate readings landed within a point of
  each other. These are cases where domestic speakers *themselves* don't
  converge on one meaning.
- **Locally converged** (reframed, not dropped): interpretations converged
  strongly on one reading (SD ≤ 1.3, or a ≥3-point gap between candidates).
  These phrases aren't confusing to a domestic speaker — the real risk is that
  the domestic "default" reading collides with a different organization's or
  culture's default. They stayed in the dataset under this reframed rationale
  rather than being treated as ambiguous in the naive sense.

The golden set (`agent/data/golden.json`, 36 cases) then pairs each of the 16
items with two test messages: an **ambiguous** paraphrase (expected to trigger
detection) and an **explicit** paraphrase that spells out the same content
unambiguously (expected to *not* trigger — this is what lets the evaluation
measure precision, not just recall, from the same set of underlying scenarios).

## 1. Scheduling — Time Expressions (bidirectional)

Korea is classified under Meyer's Scheduling axis as a flexible-time culture, in
contrast to linear-time cultures like Germany or Switzerland. Survey validation
(n=14) confirmed this is the highest-risk axis in practice — all five items
scored 5.4–6.4 out of 7 on "I've actually been confused by this before,"
regardless of whether interpretations split (T01/T04/T05) or converged toward
one reading (T02/T03).

| ID | Example phrase | Why it's a problem | Explicit alternative | Status |
|---|---|---|---|---|
| T01 | "By tomorrow, please" | Sender's or receiver's timezone as the reference point is unclear — three candidate readings actually split (sender-local 5.2 / receiver-local 4.1 / within-24h 2.4) | "By 6 PM KST, July 30th" | Ambiguous |
| T02 | "As soon as possible" | Relative expression with no concrete deadline — leans toward "within 1–2 days" (5.6) but the need-to-reconfirm response was also high (5.4) | "By 5 PM this Friday" | Ambiguous |
| T03 | "By end of day if possible" | Unclear whether "if possible" lowers priority or states a real deadline — leans weakly toward "hard deadline" (5.9) | "Hard deadline today" vs. "Ideally today, but by noon tomorrow at the latest" | Ambiguous |
| T04 | "Sometime this week" | Wide day-of-week range makes it hard to predict when work will actually start — two candidate readings landed almost exactly tied (5.3 vs. 5.1), the strongest split among all five items | "Draft by Wednesday, final by Friday" | Ambiguous |
| T05 | "I'll get back to you soon" | The unit of time behind "soon" varies by culture and by individual — all three candidates (1–2 hours / same day / next business day) clustered closely (3.1–3.6) | "I'll reply within 2 hours" / "I'll reply by tomorrow morning" | Ambiguous |

## 2. Evaluating / Disagreeing — Feedback & Pushback (direction-specific)

Meyer places Korea, alongside Japan and Thailand, at the indirect-feedback
extreme, and this is broadly supported by literature on Confucian hierarchy and
face-saving norms — the strongest literature support of the four axes covered
here. The United States is classified as only moderately indirect, and only for
*negative* feedback specifically (general communication style is direct) — F04
through F06 below are phrased to reflect that nuance rather than describing US
communication as uniformly direct.

Survey validation (n=15) confirmed F01/F02/F05 genuinely split among domestic
respondents. F03 and F04 turned out the opposite way: domestic respondents
converged strongly on one reading, so those two were reframed from "ambiguous"
to "locally converged" (see note below the table).

| ID | Direction | Example phrase | Sender's intent | Receiver's likely reading | Explicit alternative | Status |
|---|---|---|---|---|---|---|
| F01 | KR→US | "This direction is fine, but maybe let's think about it a bit more?" | Requesting the current plan be reconsidered (indirect pushback) | Positive evaluation + an optional, take-it-or-leave-it suggestion | "I'd like the current direction reconsidered. Please include an alternative in the revision." | Ambiguous (3.5 vs. 4.4 split) |
| F02 | KR→US | "It seems like everyone feels that way" | Conveying team-wide concern | Vague social pressure with no real evidence behind it | "[Name] and [Name] raised the same concern (with specifics)" | Ambiguous (4.5 vs. 2.9 split) |
| F03 | KR→US | "This looks fine, but..." | The clause after "but" is the actual feedback — **domestic readers already catch this strongly** (5.5 vs. 2.7) | Domestic respondents largely reject the naive reading ("fine" taken at face value, "but" discounted) — low misread risk when the sender is also a domestic colleague | Separate approval from revision requests into distinct sentences (still worth doing for clarity even domestically) | Locally converged |
| F04 | US→KR | "This is great, but I think we should reconsider X" | Softened phrasing, but a concrete revision is genuinely expected | **Domestic respondents read this as an almost-mandatory requirement, not a soft suggestion** (mean 6.1, SD 0.77, near-unanimous) — the risk isn't that domestic readers under-read this (as originally assumed); it's the gap between the native speaker's actual intent (literature: softened suggestion) and how strongly domestic readers take it | Explicitly separate approval status from required changes | Locally converged |
| F05 | US→KR | "I strongly disagree with this approach" | Professional disagreement, not personal | The strong wording can read as a sign of relationship strain | Structure the message as reasoning + a concrete alternative | Ambiguous (3.9 vs. 3.5 split) |
| F06 | US→KR | "Can you walk me through your reasoning?" | Genuine interest in the decision rationale | Can read as distrust of or pushback against the decision | Separate the purpose (understanding) from the question itself | Ambiguous (4.7 vs. weaker alternative, modest gap) |

> **Note on F03/F04**: both items' original assumption — "the receiver misses the
> softened signal" — was rejected by the domestic data. For F03, domestic
> readers already catch the nuance. For F04, domestic readers overshoot the
> nuance in the *opposite* direction, reading it as more mandatory than
> intended. In both cases the actual risk isn't "domestic readers don't
> understand" — it's **the gap between what a native English speaker actually
> means and what a domestic reader defaults to.**

## 3. Cross-Organization Decision-Status Vocabulary (bidirectional)

This category borrows its name from Meyer's Deciding axis (consensual vs.
top-down decision-making), but what it actually captures isn't national culture
— it's that words like "approved" or "done" **mean different things at
different organizations** (different companies, different teams). This
directly addresses the hackathon track's "organizational boundary" requirement.
`DECISION_STATUS_VOCABULARY` in `agent/` (six normalized states: final /
provisional-pending-revision / first-pass-pending-approval / proposal-only /
on-hold / undetermined) implements this as a cross-organization vocabulary
normalization problem.

| ID | Example phrase | Why it's a problem | Explicit alternative | Status |
|---|---|---|---|---|
| D01 | "Let's just go with this for now" | The original assumption (final approval vs. a provisional trial being unclear) was rejected domestically — respondents converged overwhelmingly on "first attempt" (6.4 vs. 2.6). The real risk is that the *weight* of "for now" differs by company (moderate reported confusion frequency, 3.8) | Explicitly state "final decision" vs. "first test, decide after seeing results" (still recommended as a safeguard when moving between organizations) | Locally converged |
| D02 | "Review complete" | "Complete" means different things at different organizations (final approval vs. a first pass) — **domestic respondents genuinely split here too** (3.0 vs. 5.0, SD > 2.0, the largest split among all five items) | Map each organization's terms to standardized status values | Ambiguous (strongest split) |
| D03 | "Confirmed" | The original assumption (approval vs. mere acknowledgment being unclear) was rejected domestically — respondents converged overwhelmingly on "acknowledged receipt" (5.9 vs. 2.2). The risk surfaces when moving between organizations where "confirmed" carries different weight | Distinguish "I approve" from "acknowledged and reviewing" (still useful when anticipating a move between organizations) | Locally converged |
| D04 | "No objections" | Doesn't distinguish active agreement from passive non-objection — **domestic respondents genuinely split here too** (3.7 vs. 4.3, both with SD > 2.0) | Distinguish "I agree" from "no particular concerns, so I'm fine with proceeding" | Ambiguous |
| D05 | "Let's talk about it again later" | The original assumption (on-hold vs. a soft decline being unclear) was rejected domestically — respondents converged overwhelmingly on "on hold" (6.1 vs. 2.9). However, "this later turned out to have actually been a decline" was reported at a moderate-to-high frequency (4.2) — the default reading is trustworthy but occasionally wrong | State the reason for the hold plus a concrete follow-up date (directly narrows this gap) | Locally converged |

> **Note on D01/D03/D05**: all three items' original assumption — "this phrase
> is inherently ambiguous" — was rejected by the domestic data; domestic
> speakers already converge on one reading among themselves. The remaining risk
> isn't "domestic speakers get confused" — it's **when this domestic default
> collides with a different organization's or culture's default** (D01/D03:
> differing organizational norms; D05: the sender's usual literal meaning
> occasionally doubling as a softened decline). D02 and D04 remain the two
> highest-priority items in this category, since they're the ones domestic
> speakers genuinely split on too.

**Recruiting implication**: for interview-based validation of this category,
"has worked at 2+ companies" is a better screening criterion than "has
Korea–US collaboration experience," since the underlying variable is
organizational practice, not national culture.

## Appendix: Communicating — Tone & Context (excluded from implementation)

High-context vs. low-context general communication (tone, indirect phrasing)
was evaluated and **excluded from the shipped model**: a full golden-set run
scored 0/3 recall on this category, and literature review confirmed that even
top-performing LLMs fall short of human-level performance on indirect-speech
and tone interpretation. The category remains reserved as a schema safety net
(`AmbiguityCategory`'s `OTHER` value) but isn't used in the few-shot prompt or
the golden set. Kept below for reference only.

| ID | Direction | Example phrase | Why it's a problem | Explicit alternative |
|---|---|---|---|---|
| C01 | KR→US | Conclusion delivered with no context | Low-context readers feel the reasoning behind the decision is missing | Add 1–2 lines of core rationale alongside the conclusion |
| C02 | US→KR | Direct instruction with no framing | Omitting hierarchical/relational context can read as a curt, one-sided order | Briefly include the purpose and context of the instruction |
| C03 | bidirectional | Emoji/exclamation-point frequency differences | Reads as warmth to one side, lack of seriousness to the other | Agree on a team-level tone guideline separately |
| C04 | bidirectional | Silence (no response) | Reads as implicit agreement to one side, an unresolved open question to the other | Pre-agree on a rule for how long to wait before treating silence as a decision |

## Implementation Mapping

All 16 implemented items (T01–05, F01–06, D01–05) live in
`agent/src/ditto_agent/llm/culture_criteria.py` as `CULTURE_CRITERIA`, along
with a fixed few-shot subset used in the system prompt (deliberately limited in
size — including every item in the prompt does not improve accuracy and can
hurt it). The excluded `OTHER` items (C01–04) are documented above for
reference but not implemented.

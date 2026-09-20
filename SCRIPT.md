# SENTINEL — 75-second demo script

**Target: 75s.** Spoken text below is ~185 words at a natural 150 wpm. Do not
rush it; the pauses are part of the timing.

**The one rule:** the screen must show what your voice is claiming, at the
moment you claim it. Judges score storytelling and design highest — a smooth
narration over a stuttering screen loses more than a plain narration over a
confident one.

---

## The spine

> Safety reports are written one at a time and read one at a time.
> The warning signs were in the last one. SENTINEL reads them together.

Every line below serves that. If you cut for time, cut adjectives, never the
spine.

---

## Shot list

| # | Time | On screen | You say |
|---|---|---|---|
| 1 | 0:00–0:10 | `/analyze`, empty upload zone. Cursor still. | *(hook — see below)* |
| 2 | 0:10–0:20 | Drag the PDF in. Click **Run Analysis**. | setup |
| 3 | 0:20–0:35 | Pipeline nodes lighting up, one by one | the pipeline |
| 4 | 0:35–0:50 | Risk card — gauge, then the four components | the number |
| 5 | 0:50–1:05 | Scroll to precursors, then regulatory clauses | the payoff |
| 6 | 1:05–1:15 | Corrective actions, IMMEDIATE at top. Hold. | the close |

---

## Script

### 1 · Hook — 0:00

> **"India recorded forty-eight thousand factory accidents in one year.**
> **Every one was investigated. Every report was filed. And almost none of them**
> **were ever read against each other."**

*Pause. Let it land.*

> **"The warning signs for the next accident are sitting in the last one."**

**Delivery:** slow, flat, no smile. Do not say "Hi, we're team X" — you have
ten seconds to earn attention and a greeting spends all of them. Introduce
yourselves at the end, or not at all.

---

### 2 · Setup — 0:10

> **"This is SENTINEL. I'm giving it a real fatality investigation it has**
> **never seen."**

*Drag the PDF. Click Run Analysis. Stop talking and let the pipeline start.*

---

### 3 · The pipeline — 0:20

*Nodes are lighting up. Match your words to the node that is actually lit.*

> **"It's extracting the incident, pulling hazard entities, then searching**
> **twenty-six real investigation reports and fifteen OSHA standards — keyword**
> **and semantic search at once, re-ranked, then trimmed to the sentences that**
> **actually matched."**

**Delivery:** this is the one place to speed up slightly. It should feel like
watching something work, not like a feature list.

---

### 4 · The number — 0:35

*Gauge animates. Then put the cursor on the component breakdown.*

> **"The risk score isn't a guess. Four weighted components — severity,**
> **frequency, regulatory exposure, precursor density."**

*Trace down the four rows with the cursor as you say the next line.*

> **"Every number is shown with its weight. They add up to the total. No model**
> **touches this — it's deterministic Python."**

**This is your credibility moment.** Judges have watched a dozen demos where a
model emitted a number. Yours shows its arithmetic. Slow down here.

---

### 5 · The payoff — 0:50

*Scroll to precursors.*

> **"And here's the part that isn't summarisation. These precursor patterns**
> **were found in this report — and in past ones. That count is how many."**

*Scroll to a regulatory clause. Expand it.*

> **"Every regulation is retrieved text with its source document attached.**
> **The system can't cite a standard that isn't in the corpus. It can't**
> **hallucinate a law."**

**Delivery:** "It can't hallucinate a law" is your strongest line. Land it, then
stop for half a beat.

---

### 6 · Close — 1:05

*Corrective actions, IMMEDIATE at the top. Stop scrolling. Hold the frame.*

> **"Upload to corrective actions in under a minute — with the reasoning**
> **visible at every step. That's SENTINEL."**

*Hold two seconds on the IMMEDIATE actions. Do not scroll after the last word.*

---

## Recording

**Before you hit record**

- Hit `/health` once to wake Render — a cold start is ~50 seconds of dead air
- Run the exact analysis once so it's warm, then reload for the take
- Browser at 1920×1080, zoom 100%, **hide bookmarks bar**, close every other tab
- Full screen, no dev tools, no IDE visible
- Have the PDF already on the desktop so the drag is one clean motion

**Audio** carries 40 points and is the easiest to lose. Phone earbuds 15cm from
your mouth beat a laptop mic every time. Record in a room with soft furniture,
not a hard-walled room. Turn off the fan and AC.

**Do a silent run first.** Click through the whole demo once with no talking to
learn where the app pauses, so your words land on the right frames.

**Record audio and screen separately if you can.** Narrating live over a demo
you're also driving is the most common cause of a stumble at 0:40.

---

## If something breaks mid-take

Do not restart and do not apologise. Keep narrating the spine:

> "It's cross-referencing against the historical corpus right now — that
> retrieval is the part that makes this more than a summariser."

An empty result is survivable. Dead air and an apology are not.

---

## Cut list (if you're over 80 seconds)

Cut in this order — first to go, first:

1. "keyword and semantic search at once, re-ranked, then trimmed…" → **"searching twenty-six real investigations and fifteen OSHA standards."**
2. "severity, frequency, regulatory exposure, precursor density" → **"four weighted components."**
3. The whole of shot 3's narration — just let the pipeline animate in silence for three seconds. It's more impressive without commentary.

**Never cut:** the hook, "they add up to the total", or "it can't hallucinate a law."

---

## Claims you can defend

Every number here is real. If a judge challenges you:

| Claim | Backing |
|---|---|
| 48,000 factory accidents | DGFASLI Annual Report, 2022 |
| 26 investigation reports | US Chemical Safety Board, public domain |
| 15 OSHA standards | Pulled verbatim from the federal eCFR API |
| "deterministic Python" | `backend/app/tools/scoring.py` — no model call in the function |
| "can't hallucinate a law" | Clause text is the retrieved passage; nothing generates citations |
| "components add up" | Each is rounded before weighting, specifically so the displayed maths reconciles |

**Do not claim:** real-time monitoring, a trained model, or Indian regulatory
coverage — the corpus is US federal. If asked about India: *"The pipeline is
source-agnostic — the Factories Act drops into the same regulatory index. We
built on CSB and OSHA because they're openly licensed and machine-readable."*
That is true, and it is a better answer than overclaiming.

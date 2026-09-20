# Regulatory corpus

Populated automatically:

```bash
python scripts/fetch_corpus.py       # downloads 15 OSHA standards here
python scripts/seed_regulatory.py    # chunks, embeds and indexes them
```

`fetch_corpus.py` pulls every standard that `clause_family` knows how to weight,
straight from the [eCFR API](https://www.ecfr.gov) as verbatim text — so a
retrieved clause always maps to a real risk weight rather than falling back to
the general duty clause.

**The Indian Factories Act 1948 is not fetched automatically.** India Code and
the Legislative Department block automated download, and the readable mirrors
are blog summaries rather than the enacted text. Feeding a paraphrase to a
system whose central claim is verbatim citation would be worse than omitting it.
Download it by hand from <https://www.indiacode.nic.in> into this directory and
re-run the seed script.

To add anything else by hand, drop `.txt` or `.pdf` files here and re-run.

**The file name becomes the citation shown to the user.** Name each file after
the standard it contains:

```
OSHA 29 CFR 1910.147 - Control of hazardous energy.txt
OSHA 29 CFR 1910.146 - Permit-required confined spaces.txt
OSHA 29 CFR 1926.501 - Fall protection duty.txt
Indian Factories Act 1948.txt
EPA Risk Management Program 40 CFR 68.txt
```

`clause_family` is derived from that name (see
`app/tools/retrieval.py::clause_family`), and it is what weights the regulatory
component of the risk score. An unrecognised citation falls back to the general
duty clause weight.

## Where to get them — all free

| Source | URL |
|---|---|
| OSHA 29 CFR 1910 (General Industry) | <https://www.osha.gov/laws-regs/regulations/standardnumber/1910> |
| OSHA 29 CFR 1926 (Construction) | <https://www.osha.gov/laws-regs/regulations/standardnumber/1926> |
| eCFR (clean plain-text/XML export of the above) | <https://www.ecfr.gov/current/title-29> |
| EPA Risk Management Program (40 CFR 68) | <https://www.ecfr.gov/current/title-40/part-68> |
| Indian Factories Act 1948 | <https://www.indiacode.nic.in/> |

## Why this matters

SENTINEL never generates a regulatory citation. Every clause in the UI is a
passage retrieved from this corpus. If a standard is not in this directory,
SENTINEL cannot cite it — which is the point.

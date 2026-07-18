# Example: New Blog Post Workflow

```
/new-post pour over vs french press
```

**What happens:**

1. **Keyword research** (live DataForSEO):

```
python scripts/dfs_client.py ideas   --keyword "pour over vs french press" --limit 50
python scripts/dfs_client.py volume  --keywords "pour over vs french press,french press vs pour over,pour over coffee,..."
```

Primary keyword chosen on evidence: `pour over vs french press`
(2,900/mo, difficulty 31, commercial-investigation intent).

2. **SERP analysis** — `dfs_client.py serp` shows: AI Overview present,
   PAA box, top 5 are all comparison guides (1,800-2,400 words). Page type
   to build: comparison guide with a decision table.

3. **Competitor outlines** — top 5 fetched; coverage matrix shows all cover
   taste/caffeine/cost; none cover grind-size troubleshooting or brew-ratio
   math → those become the differentiators.

4. **Brief written** to `CONTENT-BRIEF-pour-over-vs-french-press.md`:

```
Title: Pour Over vs French Press: Taste, Cost, and Effort Compared (2026)
Primary: pour over vs french press (2,900/mo)
Secondary: french press vs pour over caffeine (480/mo), is pour over better
  than french press (320/mo), ...
Structure:
  H2: The 60-second answer        ← 145-word self-contained answer block
  H2: Taste comparison
  H2: Caffeine: which is stronger?
  H2: Cost over 12 months (table)
  H2: Cleanup and effort
  H2: Brew ratio math (differentiator)
  H2: Grind size troubleshooting (differentiator)
  H2: Which should you buy? (decision table)
Word count: ~2,200
Schema: Article + FAQPage (PAA questions)
Internal links: /guides/grind-size, /gear/best-gooseneck-kettle, ...
```

5. **Publish checklist** appended: meta title 58 chars, single H1, alt text
   plan, schema validated, IndexNow submission step.

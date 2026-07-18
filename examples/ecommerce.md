# Example: Ecommerce Category Launch

User runs a specialty coffee gear shop and wants to launch a "manual
grinders" category.

```
Follow the workflow-ecommerce-launch skill for category "manual coffee grinders"
on https://gear.example
```

**What happens:**

1. **Demand mapping** (live):

```
python scripts/dfs_client.py ideas  --keyword "manual coffee grinder" --limit 50
python scripts/dfs_client.py volume --keywords "manual coffee grinder,hand coffee grinder,best manual coffee grinder,..."
python scripts/dfs_client.py serp   --keyword "manual coffee grinder"
```

Keyword map: category head term (9,900/mo, transactional) →
`/collections/manual-grinders`; filter-level terms ("manual espresso
grinder" 1,300/mo, "travel hand grinder" 880/mo) → indexable filter pages;
product long-tail assigned to PDPs.

2. **Marketplace intel** — `dfs_client.py amazon --keyword "manual coffee
   grinder"` shows the $40-$90 band dominates and titles lead with burr
   type; SERP shows Popular Products carousel → Product schema mandatory.

3. **Category page spec** — H1 "Manual Coffee Grinders", 180-word intro
   above the grid, only 2 demand-backed filters get indexable URLs
   (espresso-capable, travel-size); all other facets `noindex` + canonical.

4. **Product schema** generated per PDP:

```
python scripts/schema_gen.py product --field name="..." \
  --field offers.price=79 --field offers.priceCurrency=USD \
  --field offers.availability=https://schema.org/InStock --script-tag
```

5. **Supporting content plan** — buying guide ("How to choose a manual
   grinder"), comparison ("Manual vs electric grinders"), how-to ("Dial in
   grind size for pour over") — each briefed with the content-brief skill,
   all linking up to the category.

6. **Launch checklist + 30-day measurement plan** — re-check positions with
   `dfs_client.py ranked --target gear.example` at weeks 2/4.

Output: `ECOMMERCE-LAUNCH-manual-grinders-2026-07-17.md`

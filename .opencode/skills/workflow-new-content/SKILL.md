---
name: workflow-new-content
description: End-to-end workflow for planning a new SEO-driven blog post or article, from keyword research through brief to publish-ready checklist. Use when the user says write a blog post, new article, plan content for a keyword, or help me rank for a topic.
---

# Workflow: New Blog Post / Article

Takes a topic from idea to a publish-ready plan grounded in live SERP data.

## Inputs

- Required: topic or seed keyword
- Optional: target audience, word count, internal URLs to link
  (audience and voice come from `seo-project.yml` when present)

## Steps

### 1. Keyword research (skill: `keyword-research`)

```
python scripts/dfs_client.py ideas   --keyword "<seed>" --limit 50
python scripts/dfs_client.py related --keyword "<seed>" --limit 30
python scripts/dfs_client.py volume  --keywords "<shortlist>"
```

Pick one primary keyword (volume × attainable difficulty × business fit) and
3-6 secondary keywords. Show the numbers that justify the pick.

### 2. SERP + intent analysis (skills: `serp-analysis`, `search-intent-analysis`)

```
python scripts/dfs_client.py serp --keyword "<primary>" --limit 20
```

Classify intent (informational / commercial / transactional / navigational),
identify the page type Google rewards (listicle, guide, tool, comparison),
and list SERP features present (AI Overview, PAA, video, images).

### 3. Competitive outline (skills: `competitor-audit`, `content-gap-analysis`)

Fetch the top 5 ranking pages (webfetch). Build a coverage matrix: which
subtopics each competitor covers. The brief must cover the union of table-
stakes subtopics plus at least 2 differentiators no competitor covers well.

### 4. Content brief (skill: `content-brief`)

Produce the brief with: title options, target keywords with volumes,
search intent, recommended structure (H2/H3 outline), word count target,
entities to mention (skill: `entity-extraction`), questions to answer
(from PAA), internal links to include, and schema to add
(`python scripts/schema_gen.py article ...`).

### 5. AI-search readiness (skills: `answer-engine-optimization`, `llm-citation-readiness`)

Add to the brief: a 130-170 word self-contained answer block under the
first H2, question-form headings where natural, and attribution/citation
requirements for statistics.

### 6. Publish checklist

End with a pre-publish checklist: metadata lengths, heading hierarchy,
image alt text, schema validated, internal links placed, URL slug,
canonical, and IndexNow/submission step.

## Output

Write the full brief to `CONTENT-BRIEF-<keyword-slug>.md` and summarise the
keyword choice + outline + differentiators in chat. Write in British English
by default; end the brief file with:
`Built by Lee Beirne · OpenCode SEO Suite — inspired by AgriciDaniel/claude-seo`

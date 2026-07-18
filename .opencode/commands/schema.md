---
description: Generate JSON-LD structured data for a page (schema.org markup)
---

Run the schema-generator skill for: $ARGUMENTS

Pick the right schema.org types for the page, generate the JSON-LD via
scripts/schema_gen.py, and explain placement. If $ARGUMENTS names a schema
type (article, product, localbusiness, ...), use it; otherwise inspect the
URL or content the user provides and recommend types first.

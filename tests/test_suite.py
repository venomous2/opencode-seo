"""Test suite for the OpenCode SEO Suite scripts.

Run:  python -m pytest tests/ -v
All tests are offline — no API calls.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import cache  # noqa: E402
import citation_score  # noqa: E402
import cost_ledger  # noqa: E402
import dfs_client  # noqa: E402
import drift_store  # noqa: E402
import event_log  # noqa: E402
import impact_report  # noqa: E402
import indexnow  # noqa: E402
import ai_visibility  # noqa: E402
import link_graph  # noqa: E402
import link_graph_render  # noqa: E402
import log_analyzer  # noqa: E402
import project_dashboard  # noqa: E402
import project_memory  # noqa: E402
import recommend_store  # noqa: E402
import report_build  # noqa: E402
import report_pdf  # noqa: E402
import report_publish  # noqa: E402
import rule_engine  # noqa: E402
import schema_gen  # noqa: E402
import seo_config  # noqa: E402
import seo_fix  # noqa: E402
import seo_forecast  # noqa: E402
import seo_lint  # noqa: E402
import seo_pr_check  # noqa: E402
import spa_detect  # noqa: E402
import sxo_analyser  # noqa: E402
import watch  # noqa: E402


# ---------------------------------------------------------------------------
# rule_engine
# ---------------------------------------------------------------------------

class TestRuleEngine:
    def test_load_all_rules(self):
        rules = rule_engine.load_rules()
        assert len(rules) >= 26
        ids = [r["id"] for r in rules]
        assert len(ids) == len(set(ids)), "duplicate rule ids"

    def test_all_embedded_rule_tests_pass(self):
        rules = rule_engine.load_rules()
        result = rule_engine.test_rules(rules)
        assert result["failed"] == 0, f"failing rules: {result['failures']}"

    def test_category_filter(self):
        rules = rule_engine.load_rules(category="metadata")
        assert rules and all(r["category"] == "metadata" for r in rules)

    def test_invalid_rule_rejected(self, tmp_path):
        bad = tmp_path / "bad.yaml"
        bad.write_text("id: x\ncategory: y\n", encoding="utf-8")
        with pytest.raises(rule_engine.RuleError):
            rule_engine.load_rules(rules_dir=tmp_path)


class TestConditions:
    @pytest.mark.parametrize("detect,page,expected", [
        ({"field": "title", "condition": "empty"}, {"title": ""}, True),
        ({"field": "title", "condition": "empty"}, {"title": "Hi"}, False),
        ({"field": "h1_count", "condition": "empty"}, {"h1_count": 0}, True),
        ({"field": "status", "condition": "empty"}, {"status": 0}, False),  # not count-field
        ({"field": "h1_count", "condition": "max", "value": 1}, {"h1_count": 2}, True),
        ({"field": "word_count", "condition": "min", "value": 300}, {"word_count": 80}, True),
        ({"field": "word_count", "condition": "min", "value": 300}, {"word_count": 900}, False),
        ({"field": "images_missing_alt", "condition": "gte", "value": 1},
         {"images_missing_alt": 2}, True),
        ({"field": "title_length", "condition": "lte", "value": 65},
         {"title_length": 65}, True),
        ({"field": "noindex", "condition": "is_true"}, {"noindex": True}, True),
        ({"field": "has_viewport", "condition": "is_false"}, {"has_viewport": None}, True),
        ({"field": "url", "condition": "not_contains", "value": "https://"},
         {"url": "http://x.com"}, True),
        ({"field": "schema_types", "condition": "list_contains", "value": "Article"},
         {"schema_types": ["article", "BreadcrumbList"]}, True),
        ({"field": "schema_types", "condition": "list_not_contains", "value": "Article"},
         {"schema_types": ["Product"]}, True),
        ({"field": "canonical", "condition": "matches", "value": "^/"},
         {"canonical": "/page"}, True),
    ])
    def test_evaluate(self, detect, page, expected):
        assert rule_engine.evaluate(detect, page) is expected

    def test_scoring(self):
        rules = [
            {"id": "a", "category": "c", "severity": "critical",
             "confidence": "high", "detect": {"field": "title", "condition": "empty"},
             "why": "w", "fix": {"guidance": "g"}},
            {"id": "b", "category": "c", "severity": "low",
             "confidence": "high", "detect": {"field": "h2_count", "condition": "empty"},
             "why": "w", "fix": {"guidance": "g"}},
        ]
        result = rule_engine.run({"title": "", "h2_count": 0}, rules)
        assert result["score"] == 100 - 25 - 3
        assert result["failed"] == 2
        assert result["findings"][0]["severity"] == "critical"  # sorted first


# ---------------------------------------------------------------------------
# seo_lint
# ---------------------------------------------------------------------------

FIXTURE_HTML = """<html lang="en"><head>
<title>Great Page Title That Is Long Enough</title>
<meta name="viewport" content="width=device-width">
</head><body>
<h1>Topic</h1><h2>Section</h2>
<p>""" + " ".join(["word"] * 50) + """</p>
<img src="a.jpg">
</body></html>"""


class TestSeoLint:
    def test_parse_html_fields(self):
        page = seo_lint.parse_html(FIXTURE_HTML, "https://x.com")
        assert page["title"].startswith("Great Page")
        assert page["h1_count"] == 1
        assert page["images_total"] == 1
        assert page["images_missing_alt"] == 1
        assert page["has_viewport"] is True
        assert page["html_lang"] == "en"
        assert page["first_h2_para_words"] == 50

    def test_lint_local_skips_url_rules(self):
        rules = rule_engine.load_rules()
        page = seo_lint.parse_html(FIXTURE_HTML, "some/local/file.html")
        results = seo_lint.lint_pages([page], rules, None, local=True)
        fired_ids = {f["id"] for r in results for f in r["findings"]}
        assert "page-not-https" not in fired_ids
        assert "images-missing-alt" in fired_ids

    def test_min_score_gate(self, tmp_path, monkeypatch, capsys):
        f = tmp_path / "p.html"
        f.write_text(FIXTURE_HTML, encoding="utf-8")
        rc = seo_lint.main(["--file", str(f), "--min-score", "100"])
        assert rc == 1   # fixture page has findings, so any gate fails
        rc = seo_lint.main(["--file", str(f), "--min-score", "0"])
        assert rc == 0   # no page can score below 0

    def test_good_page_scores_high(self, tmp_path):
        good = ("<html lang=\"en\"><head><title>"
                + "T" * 55 + "</title>"
                + '<meta name="description" content="' + "d" * 140 + '">'
                + '<meta name="viewport" content="width=device-width">'
                + '<meta property="og:title" content="T">'
                + '<meta name="twitter:card" content="summary">'
                + '<link rel="canonical" href="https://x.com/p">'
                + '<script type="application/ld+json">'
                + '{"@context":"https://schema.org","@type":"Article"}'
                + '</script><script type="application/ld+json">'
                + '{"@context":"https://schema.org","@type":"BreadcrumbList"}'
                + '</script><script type="application/ld+json">'
                + '{"@context":"https://schema.org","@type":"Organization"}'
                + "</script></head><body>"
                + '<a href="#main">Skip to content</a><nav>menu</nav><main>'
                + "<h1>Topic</h1><h2>Section</h2>"
                + '<a href="/quote">Get a quote</a>'
                + "<p>Rated 5 stars by 2,000 happy customers across the UK. "
                + "Every job comes with a full money-back guarantee, so you "
                + "can book with complete confidence today.</p>"
                + "<p>" + " ".join(["word"] * 350) + "</p>"
                + '<img src="a.jpg" alt="descriptive">'
                + '<a href="/one">1</a><a href="/two">2</a>'
                + '<a href="/three">3</a>'
                + '<a href="https://source.example/study">source</a>'
                + '<a href="tel:+442012345678">020 1234 5678</a>'
                + "<h2>Frequently asked questions</h2><p>Answers.</p>"
                + "</main></body></html>")
        page = seo_lint.parse_html(good, "https://x.com/p")
        rules = rule_engine.load_rules()
        results = seo_lint.lint_pages([page], rules, None, local=True)
        assert results[0]["score"] >= 90

class TestSchemaGen:
    def test_basic_type(self):
        node = schema_gen.build("organization", ["name=Acme", "url=https://a.com"])
        assert node["@context"] == "https://schema.org"
        assert node["@type"] == "Organization"
        assert node["name"] == "Acme"

    def test_dot_notation_nests(self):
        node = schema_gen.build("localbusiness",
                                ["address.city=Leeds", "address.postcode=LS1"])
        assert node["address"]["city"] == "Leeds"

    def test_comma_makes_array(self):
        node = schema_gen.build("organization",
                                ["sameAs=https://x.com,https://y.com"])
        assert node["sameAs"] == ["https://x.com", "https://y.com"]

    def test_scalar_coercion(self):
        node = schema_gen.build("offer",
                                ["price=49.99", "inventory=12", "available=true"])
        assert node["price"] == 49.99
        assert node["inventory"] == 12
        assert node["available"] is True

    def test_bad_field_raises(self):
        with pytest.raises(ValueError):
            schema_gen.build("article", ["no-equals-sign"])


# ---------------------------------------------------------------------------
# seo_config
# ---------------------------------------------------------------------------

class TestSeoConfig:
    def test_dotenv_parsing(self, tmp_path):
        env = tmp_path / ".env"
        env.write_text('DATAFORSEO_LOGIN="user@x.com"\n'
                       "DATAFORSEO_PASSWORD=pw123\n# comment\n\n")
        values = seo_config._load_dotenv(env)
        assert values["DATAFORSEO_LOGIN"] == "user@x.com"
        assert values["DATAFORSEO_PASSWORD"] == "pw123"

    def test_credentials_missing_raises(self, monkeypatch, tmp_path):
        monkeypatch.setattr(seo_config, "CREDENTIALS_FILE",
                            tmp_path / "nope.json")
        monkeypatch.setattr(seo_config, "_find_dotenv", lambda start=None: None)
        for var in ("DATAFORSEO_LOGIN", "DATAFORSEO_PASSWORD"):
            monkeypatch.delenv(var, raising=False)
        with pytest.raises(seo_config.ConfigError):
            seo_config.dataforseo_credentials()

    def test_env_credentials_win(self, monkeypatch, tmp_path):
        monkeypatch.setattr(seo_config, "CREDENTIALS_FILE",
                            tmp_path / "nope.json")
        monkeypatch.setattr(seo_config, "_find_dotenv", lambda start=None: None)
        monkeypatch.setenv("DATAFORSEO_LOGIN", "env-user")
        monkeypatch.setenv("DATAFORSEO_PASSWORD", "env-pass")
        assert seo_config.dataforseo_credentials() == ("env-user", "env-pass")


# ---------------------------------------------------------------------------
# dfs_client payload builders (offline)
# ---------------------------------------------------------------------------

class TestDfsPayloads:
    class Args:
        location = "United States"
        language = "English"
        limit = 10
        device = "desktop"
        mode = "gap"
        keyword = "test kw"
        keywords = "a, b ,c"
        target = "example.com"
        target1 = "a.com"
        target2 = "b.com"
        url = "https://example.com"

    def test_serp_payload(self):
        payload = dfs_client.build_payload("serp", self.Args())
        assert payload[0]["keyword"] == "test kw"
        assert payload[0]["depth"] == 10

    def test_volume_splits_keywords(self):
        payload = dfs_client.build_payload("volume", self.Args())
        assert payload[0]["keywords"] == ["a", "b", "c"]

    def test_intersection_gap_mode(self):
        payload = dfs_client.build_payload("intersection", self.Args())
        assert payload[0]["intersections"] is False
        assert payload[0]["target1"] == "a.com"

    def test_unknown_command_raises(self):
        with pytest.raises(dfs_client.DfsError):
            dfs_client.build_payload("nope", self.Args())

    def test_trends_payload(self):
        class TrendsArgs(self.Args):
            date_from = "2025-01-01"
            date_to = "2026-01-01"
        payload = dfs_client.build_payload("trends", TrendsArgs())
        assert payload[0]["keywords"] == ["a", "b", "c"]
        assert payload[0]["date_from"] == "2025-01-01"
        assert payload[0]["type"] == "web"

    def test_location_aliases(self):
        assert dfs_client.normalise_location("UK") == "United Kingdom"
        assert dfs_client.normalise_location("usa") == "United States"
        assert dfs_client.normalise_location("U.S.") == "United States"
        assert dfs_client.normalise_location("United Kingdom") == "United Kingdom"
        assert dfs_client.normalise_location("Narnia") == "Narnia"

    def test_location_alias_applied_in_payload(self):
        class UkArgs(self.Args):
            location = "UK"
        payload = dfs_client.build_payload("volume", UkArgs())
        assert payload[0]["location_name"] == "United Kingdom"

    def test_batch1_payloads(self):
        class A(self.Args):
            keywords = "a,b"
            date_from = "2025-01-01"
            date_to = "2026-01-01"
        maps = dfs_client.build_payload("serp-maps", A())
        assert maps[0]["keyword"] == "test kw" and maps[0]["depth"] == 10
        ac = dfs_client.build_payload("autocomplete", A())
        assert ac[0]["keyword"] == "test kw"
        kd = dfs_client.build_payload("kd", A())
        assert kd[0]["keywords"] == ["a", "b"]
        hist = dfs_client.build_payload("backlinks-history", A())
        assert hist[0]["target"] == "example.com"
        assert hist[0]["date_from"] == "2025-01-01"
        ranks = dfs_client.build_payload("bulk-ranks", A())
        assert ranks[0]["targets"] == ["example.com"]
        tech = dfs_client.build_payload("technologies", A())
        assert tech[0]["target"] == "example.com"
        for engine in ("serp-bing", "serp-youtube", "serp-news"):
            payload = dfs_client.build_payload(engine, A())
            assert payload[0]["keyword"] == "test kw"


# ---------------------------------------------------------------------------
# ai_visibility
# ---------------------------------------------------------------------------

class TestAiVisibility:
    BODY = {"tasks": [{"result": [{"items": [
        {"text": "For EOR in the UK, popular options include Acme Corp "
                  "(acme.example), Remote, and Deel."}]}]}]}

    def test_brand_mentioned_detection(self):
        hit = ai_visibility.brand_mentioned(self.BODY, "Acme", "acme.example")
        assert hit["mentioned"] is True
        assert hit["brand_hit"] is True
        assert "Acme" in hit["excerpt"]

    def test_brand_not_mentioned(self):
        miss = ai_visibility.brand_mentioned(self.BODY, "Nobody Inc", "")
        assert miss["mentioned"] is False
        assert miss["excerpt"] == ""

    def test_domain_only_hit(self):
        hit = ai_visibility.brand_mentioned(self.BODY, "Other Name",
                                            "acme.example")
        assert hit["mentioned"] is True
        assert hit["domain_hit"] is True

    def test_save_and_compare(self, monkeypatch, tmp_path):
        monkeypatch.setattr(ai_visibility, "STORE_DIR", tmp_path)
        snap1 = {"results": [
            {"prompt": "p1", "mentioned": True},
            {"prompt": "p2", "mentioned": False}], "visibility_rate": 50.0}
        snap2 = {"results": [
            {"prompt": "p1", "mentioned": False},
            {"prompt": "p2", "mentioned": True},
            {"prompt": "p3", "mentioned": True}], "visibility_rate": 66.7}
        ai_visibility.save_snapshot("x.com", snap1)
        ai_visibility.save_snapshot("x.com", snap2)
        snaps = ai_visibility.list_snapshots("x.com")
        assert len(snaps) == 2
        diff = ai_visibility.compare(
            ai_visibility.load("x.com", snaps[0]),
            ai_visibility.load("x.com", snaps[1]))
        assert "p2" in diff["visibility_gained"]
        assert "p1" in diff["visibility_lost"]
        assert "p3" in diff["visibility_gained"]
        assert diff["rate_to"] == 66.7

    def test_aio_check_present_and_mentioned(self):
        serp = {"tasks": [{"result": [{"items": [
            {"type": "organic", "url": "https://a.com"},
            {"type": "ai_overview",
             "text": "Top picks include Acme and others.",
             "references": [{"domain": "acme.example", "url": "https://acme.example"},
                            {"domain": "rival.example", "url": "https://rival.example"}]},
        ]}]}]}
        out = ai_visibility.aio_check(serp, "Acme", "")
        assert out["present"] is True
        assert out["mentioned"] is True
        assert out["cited_domains"] == ["acme.example", "rival.example"]

    def test_aio_check_absent(self):
        serp = {"tasks": [{"result": [{"items": [
            {"type": "organic", "url": "https://a.com"}]}]}]}
        assert ai_visibility.aio_check(serp, "Acme", "") == {"present": False}

    def test_prompt_mentioned_new_structure(self):
        record = {"prompt": "p",
                  "llm": [{"platform": "chat_gpt", "mentioned": False},
                          {"platform": "gemini", "mentioned": True}],
                  "ai_overview": {"present": True, "mentioned": False}}
        assert ai_visibility._prompt_mentioned(record) is True
        record2 = {"prompt": "p",
                   "llm": [{"platform": "chat_gpt", "mentioned": False}],
                   "ai_overview": {"present": True, "mentioned": True}}
        assert ai_visibility._prompt_mentioned(record2) is True
        record3 = {"prompt": "p",
                   "llm": [{"platform": "chat_gpt", "mentioned": False}],
                   "ai_overview": {"present": False}}
        assert ai_visibility._prompt_mentioned(record3) is False


# ---------------------------------------------------------------------------
# indexnow
# ---------------------------------------------------------------------------

class TestIndexNow:
    @pytest.fixture(autouse=True)
    def temp_keys(self, monkeypatch, tmp_path):
        monkeypatch.setattr(indexnow, "KEYS_FILE", tmp_path / "keys.json")
        monkeypatch.setattr(indexnow, "SUITE_DIR", tmp_path)
        yield

    def test_init_generates_and_persists_key(self):
        first = indexnow.init_key("example.com")
        assert first["new"] is True
        assert len(first["key"]) == 32
        assert first["key_file_url"].endswith(f"/{first['key']}.txt")
        second = indexnow.init_key("example.com")
        assert second["new"] is False
        assert second["key"] == first["key"]  # stable, not rotated

    def test_submit_without_key_errors(self):
        with pytest.raises(indexnow.IndexNowError, match="No IndexNow key"):
            indexnow.submit("unknown.example", ["https://unknown.example/a"])

    def test_submit_empty_urls_errors(self):
        indexnow.init_key("example.com")
        with pytest.raises(indexnow.IndexNowError, match="No URLs"):
            indexnow.submit("example.com", [])


# ---------------------------------------------------------------------------
# report_pdf
# ---------------------------------------------------------------------------

class TestReportPdf:
    def test_find_browser_returns_path_or_none(self, monkeypatch):
        monkeypatch.setattr(report_pdf, "CANDIDATES", [])
        monkeypatch.setattr(report_pdf.shutil, "which", lambda name: None)
        assert report_pdf.find_browser() is None

    def test_find_browser_uses_which_fallback(self, monkeypatch):
        monkeypatch.setattr(report_pdf, "CANDIDATES", [])
        monkeypatch.setattr(report_pdf.shutil, "which",
                            lambda name: "/usr/bin/chromium" if name == "chromium" else None)
        assert report_pdf.find_browser() == "/usr/bin/chromium"


# ---------------------------------------------------------------------------
# report_publish
# ---------------------------------------------------------------------------

class TestReportPublish:
    MD = ("# Test Report\n\n## Executive summary\n\nThings are fine.\n\n"
          "## Findings\n\n| Severity | Item |\n|---|---|\n| Low | x |\n")

    def test_missing_file(self, tmp_path):
        result = report_publish.publish(tmp_path / "nope.md", "B", None, "F",
                                        onepager=True, html_only=True)
        assert "error" in result

    def test_html_only_produces_html_and_onepager(self, tmp_path):
        md = tmp_path / "r.md"
        md.write_text(self.MD, encoding="utf-8")
        result = report_publish.publish(md, "Lee Beirne", None,
                                        report_build.DEFAULT_FOOTER,
                                        onepager=True, html_only=True)
        assert Path(result["html"]).is_file()
        assert Path(result["onepager_html"]).is_file()
        assert "skipped" in result["pdf"]

    def test_no_onepager(self, tmp_path):
        md = tmp_path / "r.md"
        md.write_text(self.MD, encoding="utf-8")
        result = report_publish.publish(md, "Lee Beirne", None,
                                        report_build.DEFAULT_FOOTER,
                                        onepager=False, html_only=True)
        assert "html" in result
        assert "onepager_html" not in result

    def test_no_browser_graceful_skip(self, tmp_path, monkeypatch):
        monkeypatch.setattr(report_pdf, "find_browser", lambda: None)
        md = tmp_path / "r.md"
        md.write_text(self.MD, encoding="utf-8")
        result = report_publish.publish(md, "B", None, "F",
                                        onepager=True, html_only=False)
        assert "no headless browser" in result["pdf"]


# ---------------------------------------------------------------------------
# cache
# ---------------------------------------------------------------------------

class TestCache:
    @pytest.fixture(autouse=True)
    def temp_cache(self, monkeypatch, tmp_path):
        monkeypatch.setattr(cache, "CACHE_DIR", tmp_path / "cache")
        yield

    def test_roundtrip(self):
        payload = [{"keyword": "x"}]
        body = {"status_code": 20000, "tasks": []}
        assert cache.get("serp", payload) is None
        cache.put("serp", payload, body)
        assert cache.get("serp", payload) == body

    def test_expired_entry_returns_none(self, monkeypatch):
        payload = [{"keyword": "x"}]
        cache.put("serp", payload, {"a": 1})
        monkeypatch.setattr(cache, "TTL", {"serp": -1})
        assert cache.get("serp", payload) is None

    def test_clear(self):
        cache.put("serp", [{"k": 1}], {"a": 1})
        cache.put("serp", [{"k": 2}], {"a": 2})
        assert cache.stats()["entries"] == 2
        assert cache.clear() == 2
        assert cache.stats()["entries"] == 0


# ---------------------------------------------------------------------------
# cost_ledger
# ---------------------------------------------------------------------------

class TestCostLedger:
    @pytest.fixture(autouse=True)
    def temp_ledger(self, monkeypatch, tmp_path):
        monkeypatch.setattr(cost_ledger, "LEDGER", tmp_path / "costs.jsonl")
        monkeypatch.setattr(cost_ledger, "SUITE_DIR", tmp_path)
        yield

    def test_log_and_report(self):
        cost_ledger.log("serp", 0.002)
        cost_ledger.log("ranked", 0.01)
        cost_ledger.log("serp", 0.002)
        report = cost_ledger.report(by="command")
        assert report["call_count"] == 3
        assert report["periods"]["all_time"]["cost_usd"] == pytest.approx(0.014)
        assert report["by_command"]["ranked"]["cost_usd"] == 0.01

    def test_log_none_cost_skipped(self):
        cost_ledger.log("serp", None)
        assert cost_ledger.report()["call_count"] == 0


# ---------------------------------------------------------------------------
# drift_store
# ---------------------------------------------------------------------------

class TestDriftStore:
    @pytest.fixture(autouse=True)
    def temp_drift(self, monkeypatch, tmp_path):
        monkeypatch.setattr(drift_store, "DRIFT_DIR", tmp_path / "drift")
        monkeypatch.setattr(event_log, "EVENTS_DIR", tmp_path / "events")
        yield

    def test_save_and_list(self):
        drift_store.save("example.com", {"scores": {"technical": 70}})
        drift_store.save("example.com", {"scores": {"technical": 80}})
        assert len(drift_store.list_snapshots("example.com")) == 2

    def test_compare_scores_and_rankings(self):
        old = {"_saved_at": 1,
               "scores": {"technical": 70},
               "rankings": [{"keyword": "a", "position": 8, "url": "/a"},
                            {"keyword": "b", "position": 3, "url": "/b"}],
               "backlinks": {"referring_domains": 50}}
        new = {"_saved_at": 2,
               "scores": {"technical": 76},
               "rankings": [{"keyword": "a", "position": 4, "url": "/a"},
                            {"keyword": "c", "position": 9, "url": "/c"}],
               "backlinks": {"referring_domains": 58}}
        diff = drift_store.compare(old, new)
        assert diff["score_changes"]["technical"]["delta"] == 6
        assert diff["rankings"]["gained"] == ["c"]
        assert diff["rankings"]["lost"] == ["b"]
        assert diff["rankings"]["moved_up"][0]["keyword"] == "a"
        assert diff["backlinks"]["referring_domains"]["delta"] == 8

    def test_build_chart_specs(self):
        old = {"scores": {"technical": 70, "content": 60},
               "rankings": [{"keyword": "a", "position": 8, "url": "/a"},
                            {"keyword": "b", "position": 3, "url": "/b"}],
               "backlinks": {"referring_domains": 50},
               "mentions": {"ai_mentions": 4}}
        new = {"scores": {"technical": 76, "content": 60},
               "rankings": [{"keyword": "a", "position": 4, "url": "/a"},
                            {"keyword": "c", "position": 9, "url": "/c"}],
               "backlinks": {"referring_domains": 58},
               "mentions": {"ai_mentions": 9}}
        specs = drift_store.build_chart_specs(old, new)
        types = [s["type"] for s in specs]
        assert types == ["compare", "compare", "stats"]
        scores = specs[0]
        assert scores["max"] == 100
        assert ["Technical", 70, 76] in scores["data"]
        metrics = specs[1]
        assert ["Referring Domains", 50, 58] in metrics["data"]
        stats = specs[2]
        flat = {row[0]: row[1] for row in stats["data"]}
        assert flat["Keywords gained"] == "1"
        assert flat["Keywords lost"] == "1"
        assert flat["Moved up"] == "1"
        assert flat["Moved down"] == "0"

    def test_build_chart_specs_empty_when_nothing_comparable(self):
        assert drift_store.build_chart_specs({"notes": "x"}, {"notes": "y"}) == []


# ---------------------------------------------------------------------------
# recommend_store
# ---------------------------------------------------------------------------

def _rec(url="https://example.com/", finding="missing-title",
         source="rule:missing-title", **overrides):
    base = {"url": url, "source": source, "finding": finding,
            "severity": "critical", "why": "w", "fix": "f"}
    base.update(overrides)
    return base


class TestRecommendStore:
    @pytest.fixture(autouse=True)
    def temp_store(self, monkeypatch, tmp_path):
        monkeypatch.setattr(recommend_store, "RECS_DIR", tmp_path / "recs")
        monkeypatch.setattr(event_log, "EVENTS_DIR", tmp_path / "events")
        yield

    def test_raise_and_list(self):
        saved = recommend_store.raise_rec("example.com", _rec())
        assert saved["status"] == "open" and saved["times_raised"] == 1
        assert len(saved["id"]) == 12
        recs = recommend_store.list_recs("example.com")
        assert len(recs) == 1 and recs[0]["finding"] == "missing-title"

    def test_reraise_dedups_and_counts(self):
        recommend_store.raise_rec("example.com", _rec())
        again = recommend_store.raise_rec("example.com", _rec())
        assert again["times_raised"] == 2
        assert len(recommend_store.list_recs("example.com")) == 1

    def test_different_url_is_a_different_rec(self):
        recommend_store.raise_rec("example.com", _rec(url="https://example.com/a"))
        recommend_store.raise_rec("example.com", _rec(url="https://example.com/b"))
        assert len(recommend_store.list_recs("example.com")) == 2

    def test_status_flow_and_history(self):
        saved = recommend_store.raise_rec("example.com", _rec())
        recommend_store.set_status("example.com", saved["id"], "accepted")
        recommend_store.set_status("example.com", saved["id"], "done",
                                   note="deployed")
        rec = recommend_store.get("example.com", saved["id"])
        assert rec["status"] == "done" and rec["last_note"] == "deployed"
        # closed items hidden by default, visible with include_closed
        assert recommend_store.list_recs("example.com") == []
        assert len(recommend_store.list_recs("example.com",
                                             include_closed=True)) == 1
        kinds = [e["event"] for e in
                 recommend_store.history("example.com", saved["id"])]
        assert kinds == ["raise", "status", "status"]

    def test_done_rec_reopens_when_redetected(self):
        saved = recommend_store.raise_rec("example.com", _rec())
        recommend_store.set_status("example.com", saved["id"], "done")
        again = recommend_store.raise_rec("example.com", _rec())
        assert again["status"] == "open" and again["times_raised"] == 2

    def test_ignored_rec_stays_ignored(self):
        saved = recommend_store.raise_rec("example.com", _rec())
        recommend_store.set_status("example.com", saved["id"], "ignored")
        again = recommend_store.raise_rec("example.com", _rec())
        assert again["status"] == "ignored" and again["times_raised"] == 2

    def test_set_status_rejects_bad_values(self):
        saved = recommend_store.raise_rec("example.com", _rec())
        with pytest.raises(ValueError):
            recommend_store.set_status("example.com", saved["id"], "banana")
        assert recommend_store.set_status("example.com", "nope", "done") is None

    def test_summary_counts(self):
        recommend_store.raise_rec("example.com", _rec())
        recommend_store.raise_rec("example.com",
                                  _rec(finding="short-meta",
                                       source="rule:short-meta",
                                       severity="medium"))
        summary = recommend_store.summary("example.com")
        assert summary["total"] == 2 and summary["actionable"] == 2
        assert summary["actionable_by_severity"]["critical"] == 1
        assert summary["actionable_by_severity"]["medium"] == 1

    def test_save_lint_results_resolves_fixed_findings(self):
        rules = rule_engine.load_rules(category="metadata")
        failing = seo_lint.lint_pages(
            [{"url": "https://example.com/", "title": "",
              "meta_description": "x" * 100}], rules, None)
        assert failing[0]["findings"], "fixture should fail missing-title"
        first = recommend_store.save_lint_results("example.com", failing, rules)
        assert first["raised"] >= 1 and first["resolved"] == 0

        passing = seo_lint.lint_pages(
            [{"url": "https://example.com/", "title": "A proper title",
              "meta_description": "x" * 100}], rules, None)
        second = recommend_store.save_lint_results("example.com", passing, rules)
        assert second["resolved"] >= 1
        rec = recommend_store.list_recs("example.com", status="resolved")
        assert any(r["finding"] == "missing-title" for r in rec)

    def test_resolution_only_touches_rules_that_ran(self):
        # an open rec from a rule outside this run must survive
        recommend_store.raise_rec(
            "example.com",
            _rec(finding="no-https", source="rule:no-https",
                 url="https://example.com/"))
        rules = rule_engine.load_rules(category="metadata")
        failing = seo_lint.lint_pages(
            [{"url": "https://example.com/", "title": ""}], rules, None)
        recommend_store.save_lint_results("example.com", failing, rules)
        recs = recommend_store.list_recs("example.com")
        assert any(r["finding"] == "no-https" and r["status"] == "open"
                   for r in recs)

    def test_lint_save_cli_persists(self, tmp_path, monkeypatch, capsys):
        page = tmp_path / "p.html"
        page.write_text("<html><head></head><body><h1>Hi</h1></body></html>",
                        encoding="utf-8")
        rc = seo_lint.main(["--file", str(page), "--save",
                            "--domain", "example.com"])
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out["store"]["domain"] == "example.com"
        assert out["store"]["raised"] >= 1
        assert recommend_store.summary("example.com")["actionable"] >= 1

    def test_domains_lists_known_stores(self):
        recommend_store.raise_rec("example.com", _rec())
        recommend_store.raise_rec("other.co.uk", _rec())
        assert recommend_store.domains() == ["example.com", "other.co.uk"]

    def test_priority_score_components(self):
        base = {"severity": "critical", "confidence": "high",
                "times_raised": 1}
        assert recommend_store.priority_score(base) == 5.0
        assert recommend_store.priority_score(
            {**base, "auto_fixable": True}) == 6.25
        assert recommend_store.priority_score(
            {**base, "times_raised": 3}) == 6.0          # +10% per re-raise
        capped = recommend_store.priority_score({**base, "times_raised": 99})
        assert capped == 7.5                             # persistence cap +50%
        valued = {"severity": "medium", "confidence": "high",
                  "times_raised": 1,
                  "evidence": {"est_monthly_clicks": 1000}}
        # value impact (1 + log10(1000) = 4) beats the medium severity (2)
        assert recommend_store.priority_score(valued) == 4.0

    def test_list_orders_by_priority(self):
        recommend_store.raise_rec(
            "example.com",
            _rec(finding="medium-with-value", source="rule:m1",
                 severity="medium", confidence="high",
                 evidence={"est_monthly_clicks": 1000}))
        recommend_store.raise_rec("example.com", _rec())  # critical, plain
        recs = recommend_store.list_recs("example.com")
        assert all("priority" in r for r in recs)
        # both score 4.0; the critical wins the tiebreak on severity
        assert recs[0]["finding"] == "missing-title"
        assert recs[1]["finding"] == "medium-with-value"
        sev = recommend_store.list_recs("example.com", sort="severity")
        assert sev[0]["severity"] == "critical"


# ---------------------------------------------------------------------------
# seo_forecast
# ---------------------------------------------------------------------------

class TestSeoForecast:
    @pytest.fixture(autouse=True)
    def temp_drift(self, monkeypatch, tmp_path):
        monkeypatch.setattr(drift_store, "DRIFT_DIR", tmp_path / "drift")
        monkeypatch.setattr(event_log, "EVENTS_DIR", tmp_path / "events")
        yield

    def test_ctr_boundaries(self):
        assert seo_forecast.ctr(1) == 0.25
        assert seo_forecast.ctr(10) == 0.010
        assert seo_forecast.ctr(15) == 0.004
        assert seo_forecast.ctr(25) == 0.001
        assert seo_forecast.ctr(0) == seo_forecast.ctr(1)

    def test_estimate_bands(self):
        est = seo_forecast.estimate(1000, 3)
        assert est["expected"] == 80
        assert est["low"] == 48 and est["high"] == 112

    def test_main_offline_from_snapshot(self, capsys):
        drift_store.save("f.com", {"rankings": [
            {"keyword": "a", "position": 8, "url": "/a",
             "search_volume": 1000},
            {"keyword": "b", "position": 15, "url": "/b",
             "search_volume": 500}]})
        rc = seo_forecast.main(["--domain", "f.com", "--target-position",
                                "3", "--snapshot"])
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out["totals"]["current_clicks_expected"] == 20   # 18 + 2
        assert out["totals"]["target_clicks_expected"] == 120   # 80 + 40
        assert out["totals"]["uplift_expected"] == 100
        assert out["totals"]["uplift_low"] == 52
        assert out["totals"]["uplift_high"] == 148
        assert out["keywords"][0]["keyword"] == "a"             # volume order
        assert "ctr_curve" in out["assumptions"]
        latest = drift_store.load("f.com",
                                  drift_store.list_snapshots("f.com")[-1])
        assert latest["forecast"]["uplift_expected"] == 100

    def test_keywords_flag_uses_volume_pull(self, monkeypatch, capsys):
        drift_store.save("f2.com", {"rankings": [
            {"keyword": "c", "position": 5, "url": "/c",
             "search_volume": 200}]})
        monkeypatch.setattr(seo_forecast, "_dfs", lambda *a, **k: {
            "result": [{"items": [{"keyword": "d",
                                   "search_volume": 300}]}]})
        rc = seo_forecast.main(["--domain", "f2.com", "--keywords", "c,d"])
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        rows = {r["keyword"]: r for r in out["keywords"]}
        assert rows["c"]["current_position"] == 5
        assert rows["d"]["current_position"] is None
        assert rows["d"]["target_clicks"]["expected"] == 24     # 300 x 0.08


# ---------------------------------------------------------------------------
# impact_report
# ---------------------------------------------------------------------------

class TestImpactReport:
    @pytest.fixture(autouse=True)
    def temp_stores(self, monkeypatch, tmp_path):
        monkeypatch.setattr(recommend_store, "RECS_DIR", tmp_path / "recs")
        monkeypatch.setattr(drift_store, "DRIFT_DIR", tmp_path / "drift")
        monkeypatch.setattr(event_log, "EVENTS_DIR", tmp_path / "events")
        yield

    def test_keyword_fix_verdict_improved(self):
        drift_store.save("example.com", {"rankings": [
            {"keyword": "espresso", "position": 18, "url": "/e"}]})
        rec = recommend_store.raise_rec("example.com", {
            "url": "/e", "source": "skill:watch",
            "key": "rank-loss-espresso",
            "finding": "Ranking dropped: 'espresso' 12 → 18",
            "severity": "high",
            "evidence": {"keyword": "espresso", "was": 12, "now": 18}})
        recommend_store.set_status("example.com", rec["id"], "done")
        drift_store.save("example.com", {"rankings": [
            {"keyword": "espresso", "position": 6, "url": "/e"}]})
        out = impact_report.report("example.com", 90)
        assert out["evaluated"] == 1
        assert out["counts"]["improved"] == 1
        assert out["items"][0]["verdict"] == "improved"
        assert "association" in out["note"]

    def test_url_fix_verdict_and_insufficient_data(self):
        drift_store.save("example.com", {"rankings": [
            {"keyword": "a", "position": 12, "url": "/p"},
            {"keyword": "b", "position": 14, "url": "/p"}]})
        rec = recommend_store.raise_rec("example.com", {
            "url": "/p", "source": "rule:missing-title",
            "finding": "missing-title", "severity": "critical"})
        recommend_store.set_status("example.com", rec["id"], "done")
        drift_store.save("example.com", {"rankings": [
            {"keyword": "a", "position": 5, "url": "/p"},
            {"keyword": "b", "position": 7, "url": "/p"}]})
        # completed after the newest snapshot -> nothing to measure yet
        late = recommend_store.raise_rec("example.com", {
            "url": "/q", "source": "rule:missing-h1",
            "finding": "missing-h1", "severity": "high"})
        recommend_store.set_status("example.com", late["id"], "done",
                                   note="just now")
        out = impact_report.report("example.com", 90)
        verdicts = {i["finding"]: i["verdict"] for i in out["items"]}
        assert verdicts["missing-title"] == "improved"
        assert verdicts["missing-h1"] == "insufficient_data"
        assert out["counts"]["improved"] == 1
        assert out["counts"]["insufficient_data"] == 1


# ---------------------------------------------------------------------------
# event_log
# ---------------------------------------------------------------------------

class TestEventLog:
    @pytest.fixture(autouse=True)
    def temp_events(self, monkeypatch, tmp_path):
        monkeypatch.setattr(event_log, "EVENTS_DIR", tmp_path / "events")
        monkeypatch.setattr(recommend_store, "RECS_DIR", tmp_path / "recs")
        monkeypatch.setattr(drift_store, "DRIFT_DIR", tmp_path / "drift")
        yield

    def test_log_and_list(self):
        event_log.log("example.com", "note", "first")
        event_log.log("example.com", "note", "second")
        out = event_log.events("example.com")
        assert [e["summary"] for e in out] == ["first", "second"]
        assert all(e["type"] == "note" and e["ts"] for e in out)

    def test_limit_type_and_since_filters(self):
        event_log.log("example.com", "note", "a")
        event_log.log("example.com", "lint_saved", "b")
        future = int(time.time()) + 60
        assert len(event_log.events("example.com", limit=1)) == 1
        assert event_log.events("example.com", limit=1)[0]["summary"] == "b"
        assert [e["summary"] for e in
                event_log.events("example.com", type="note")] == ["a"]
        assert event_log.events("example.com", since=future) == []

    def test_log_never_raises(self, monkeypatch, tmp_path):
        # EVENTS_DIR points at a regular file: mkdir must fail silently
        blocker = tmp_path / "blocker"
        blocker.write_text("x")
        monkeypatch.setattr(event_log, "EVENTS_DIR", blocker)
        event_log.log("example.com", "note", "swallowed")  # no exception

    def test_domains(self):
        event_log.log("b.co.uk", "note", "x")
        event_log.log("a.com", "note", "x")
        assert event_log.domains() == ["a.com", "b.co.uk"]

    def test_data_layer_integrations(self):
        # raise -> rec_raised once; re-raise while open -> no extra event
        saved = recommend_store.raise_rec("example.com", _rec())
        recommend_store.raise_rec("example.com", _rec())
        types = [e["type"] for e in event_log.events("example.com")]
        assert types == ["rec_raised"]
        # status change -> rec_status; done then re-raise -> rec_reopened
        recommend_store.set_status("example.com", saved["id"], "done")
        recommend_store.raise_rec("example.com", _rec())
        types = [e["type"] for e in event_log.events("example.com")]
        assert types == ["rec_raised", "rec_status", "rec_reopened"]

    def test_drift_save_logs_snapshot(self):
        drift_store.save("example.com", {"scores": {"technical": 70}})
        events = event_log.events("example.com", type="snapshot_saved")
        assert len(events) == 1
        assert "scores" in events[0]["summary"]


# ---------------------------------------------------------------------------
# project_dashboard
# ---------------------------------------------------------------------------

class TestProjectDashboard:
    @pytest.fixture(autouse=True)
    def temp_stores(self, monkeypatch, tmp_path):
        monkeypatch.setattr(recommend_store, "RECS_DIR", tmp_path / "recs")
        monkeypatch.setattr(drift_store, "DRIFT_DIR", tmp_path / "drift")
        monkeypatch.setattr(event_log, "EVENTS_DIR", tmp_path / "events")
        self.tmp = tmp_path
        yield

    def _seed(self):
        recommend_store.raise_rec(
            "example.com",
            _rec(finding="missing-title", source="rule:missing-title",
                 severity="critical", why="No title tag"))
        recommend_store.raise_rec(
            "example.com",
            _rec(finding="Merge grinder pages", source="skill:site-audit",
                 severity="high", why="Cannibalisation"))
        drift_store.save("example.com",
                         {"scores": {"technical": 70, "content": 65,
                                     "authority": 50, "cwv": 60,
                                     "ai_search": 40}})
        drift_store.save("example.com",
                         {"scores": {"technical": 80, "content": 70,
                                     "authority": 55, "cwv": 65,
                                     "ai_search": 45}})

    def test_overall_score_weighting(self):
        snap = {"scores": {"technical": 100, "content": 100, "authority": 0,
                           "cwv": 100, "ai_search": 100}}
        assert project_dashboard.overall_score(snap) == 80.0
        assert project_dashboard.overall_score({"scores": {}}) is None
        assert project_dashboard.overall_score(
            {"scores": {"technical": 50, "content": 100}}) == 75.0

    def test_build_markdown_full(self):
        self._seed()
        markdown, meta = project_dashboard.build_markdown("example.com")
        assert "## Top actions" in markdown
        assert "Missing title" in markdown
        assert "Merge grinder pages" in markdown
        assert "## Recent activity" in markdown
        assert '"type": "donut"' in markdown
        assert meta["actionable"] == 2
        assert meta["critical_open"] == 1
        assert meta["snapshots"] == 2
        assert meta["health"] == 66.8         # weighted blend of snapshot 2
        assert meta["health_delta"] == 6.6    # up from 60.2

    def test_build_markdown_empty_stores(self):
        markdown, meta = project_dashboard.build_markdown("empty.com")
        assert "No drift snapshots yet" in markdown
        assert "queue is empty" in markdown
        assert meta["health"] is None and meta["actionable"] == 0

    def test_main_writes_html_and_md(self, monkeypatch, capsys):
        self._seed()
        monkeypatch.chdir(self.tmp)
        rc = project_dashboard.main(["--domain", "example.com"])
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        html = Path(out["html"])
        assert html.is_file() and html.suffix == ".html"
        assert Path(out["markdown"]).is_file()
        page = html.read_text(encoding="utf-8")
        assert "Project Dashboard" in page and "example.com" in page
        assert "Missing title" in page


# ---------------------------------------------------------------------------
# watch
# ---------------------------------------------------------------------------

def _ranked_payload(*rows):
    """Simple-shape ranked response: (keyword, position, url) rows."""
    return {"result": [{"items": [
        {"keyword": kw, "position": pos, "url": url} for kw, pos, url in rows
    ]}]}


class TestWatch:
    @pytest.fixture(autouse=True)
    def temp_stores(self, monkeypatch, tmp_path):
        monkeypatch.setattr(recommend_store, "RECS_DIR", tmp_path / "recs")
        monkeypatch.setattr(drift_store, "DRIFT_DIR", tmp_path / "drift")
        monkeypatch.setattr(event_log, "EVENTS_DIR", tmp_path / "events")
        monkeypatch.setattr(watch, "_ai_visibility",
                            lambda *a, **k: pytest.fail("offline"))
        yield

    def test_rank_items_captures_search_volume(self):
        labs = {"result": [{"items": [{
            "keyword_data": {"keyword": "espresso",
                             "keyword_info": {"search_volume": 1900}},
            "ranked_serp_element": {"serp_item": {"rank_group": 7,
                                                  "url": "/e"}}}]}]}
        items = watch.rank_items(labs)
        assert items[0]["search_volume"] == 1900

    def test_rank_loss_rec_carries_click_estimate(self, monkeypatch):
        drift_store.save("example.com", {"rankings": [
            {"keyword": "grinders", "position": 12, "url": "/g",
             "search_volume": 50000}]})
        monkeypatch.setattr(watch, "_dfs", lambda *a, **k: _ranked_payload())
        watch.check_rankings("example.com", "United States", "English", 50)
        recs = recommend_store.list_recs("example.com")
        evidence = recs[0]["evidence"]
        assert evidence["est_monthly_searches"] == 50000
        assert evidence["est_monthly_clicks"] == 200   # 50000 x CTR(12)
        # value impact (3.3) lifts it above the medium severity base (2.0)
        assert recs[0]["priority"] > 2.0

    def test_rank_items_simple_and_labs_shapes(self):
        simple = _ranked_payload(("grinders", 4, "/g"))
        labs = {"result": [{"items": [{
            "keyword_data": {"keyword": "espresso"},
            "ranked_serp_element": {"serp_item": {"rank_group": 7,
                                                  "url": "/e"}}}]}]}
        assert watch.rank_items(simple) == [
            {"keyword": "grinders", "position": 4, "url": "/g"}]
        assert watch.rank_items(labs) == [
            {"keyword": "espresso", "position": 7, "url": "/e"}]
        assert watch.rank_items({"result": []}) == []

    def test_backlink_summary_shapes(self):
        direct = {"result": [{"referring_domains": 120, "backlinks": 3400}]}
        nested = {"result": [{"items": [{"referring_domains": 9,
                                         "backlinks": 40}]}]}
        assert watch.backlink_summary(direct) == {
            "referring_domains": 120, "backlinks": 3400}
        assert watch.backlink_summary(nested)["referring_domains"] == 9
        assert watch.backlink_summary({"result": [{"other": 1}]}) == {}

    def test_rankings_loss_rec_and_recovery(self, monkeypatch):
        drift_store.save("example.com", {"rankings": [
            {"keyword": "grinders", "position": 4, "url": "/g"},
            {"keyword": "espresso", "position": 12, "url": "/e"},
            {"keyword": "obscure", "position": 45, "url": "/o"}]})
        # 'grinders' gone, 'espresso' slid 12 -> 18; 'obscure' ignored (>20)
        monkeypatch.setattr(watch, "_dfs", lambda *a, **k: _ranked_payload(
            ("espresso", 18, "/e"), ("new kw", 9, "/n")))
        result, items = watch.check_rankings("example.com",
                                             "United States", "English", 50)
        assert result["tracked"] == 2 and result["losses_raised"] == 2
        recs = recommend_store.list_recs("example.com")
        lost = [r for r in recs if "grinders" in r["finding"]]
        dropped = [r for r in recs if "espresso" in r["finding"]]
        assert lost and lost[0]["severity"] == "high"     # was top-10
        assert dropped and dropped[0]["severity"] == "medium"  # drop of 6
        assert all(r["source"] == "skill:watch" for r in recs)

        # next run: 'grinders' recovered to its old position
        monkeypatch.setattr(watch, "_dfs", lambda *a, **k: _ranked_payload(
            ("grinders", 4, "/g"), ("espresso", 18, "/e")))
        result2, _ = watch.check_rankings("example.com",
                                          "United States", "English", 50)
        assert result2["recovered"] == 1
        resolved = recommend_store.list_recs("example.com",
                                             status="resolved")
        assert any("grinders" in r["finding"] for r in resolved)
        # still-open espresso rec did not duplicate on the second run
        open_recs = recommend_store.list_recs("example.com")
        assert len([r for r in open_recs
                    if "espresso" in r["finding"]]) == 1

    def test_competitor_growth_rec_and_dedup(self, monkeypatch):
        drift_store.save("competitor-rival.com", {"rankings": [
            {"keyword": "old kw", "position": 5, "url": "/o"}]})
        gained = _ranked_payload(("old kw", 5, "/o"), ("new a", 3, "/a"),
                                 ("new b", 4, "/b"), ("new c", 6, "/c"))
        monkeypatch.setattr(watch, "_dfs", lambda *a, **k: gained)
        report = watch.check_competitors("example.com", ["rival.com"],
                                         "United States", "English", 50)
        assert report["competitors"][0]["rec_raised"] is True
        recs = recommend_store.list_recs("example.com")
        assert len(recs) == 1
        assert "rival.com" in recs[0]["finding"]
        assert "3" in recs[0]["finding"]          # 3 new keywords
        # a second identical run gains nothing new — no raise, no duplicate
        watch.check_competitors("example.com", ["rival.com"],
                                "United States", "English", 50)
        recs = recommend_store.list_recs("example.com")
        assert len(recs) == 1 and recs[0]["times_raised"] == 1

    def test_competitor_below_threshold_stays_quiet(self, monkeypatch):
        drift_store.save("competitor-rival.com", {"rankings": [
            {"keyword": "old kw", "position": 5, "url": "/o"}]})
        gained = _ranked_payload(("old kw", 5, "/o"), ("new a", 3, "/a"))
        monkeypatch.setattr(watch, "_dfs", lambda *a, **k: gained)
        watch.check_competitors("example.com", ["rival.com"],
                                "United States", "English", 50)
        assert recommend_store.list_recs("example.com") == []

    def test_run_daily_offline(self, monkeypatch, tmp_path):
        html = "<html><head></head><body><h1>Hi</h1></body></html>"
        from site_crawler import FetchResult
        monkeypatch.setattr(
            watch, "fetch",
            lambda url, timeout: FetchResult(200, "text/html", html, {}))
        monkeypatch.setattr(watch, "_dfs", lambda *a, **k: _ranked_payload(
            ("grinders", 4, "/g")))
        summary = watch.run("example.com", "daily",
                            ["https://example.com"], [], "", None,
                            "United States", "English", 50)
        assert summary["checks"]["lint"]["pages_linted"] == 1
        assert summary["checks"]["lint"]["raised"] >= 1
        assert summary["checks"]["rankings"]["tracked"] == 1
        assert summary["snapshot_saved"] == ["rankings"]
        assert summary["cost_usd"] == 0.0
        # completion event landed on the timeline
        assert any(e["type"] == "watch_completed"
                   for e in event_log.events("example.com"))

    def test_run_weekly_skips_ai_without_brand(self, monkeypatch):
        monkeypatch.setattr(
            watch, "fetch",
            lambda url, timeout=20: pytest.fail("no pages in this run"))
        responses = {"ranked": _ranked_payload(("grinders", 4, "/g")),
                     "backlinks": {"result": [{"referring_domains": 10,
                                               "backlinks": 50}]}}
        monkeypatch.setattr(watch, "_dfs",
                            lambda args, sandbox=False, **k: responses[args[0]])
        summary = watch.run("example.com", "weekly", [], [], "", None,
                            "United States", "English", 50)
        assert summary["checks"]["ai_visibility"].startswith("skipped")
        assert summary["checks"]["backlinks"]["referring_domains"] == 10
        assert "backlinks" in summary["snapshot_saved"]

    def test_schedule_lines(self):
        lines = watch.schedule_lines("example.com", "weekly")
        assert "schtasks" in lines["windows_schtasks"]
        assert "example.com" in lines["windows_schtasks"]
        assert "cron" in lines["note"] or "0 7" in lines["cron"]

    def test_dry_run_calls_nothing(self, monkeypatch, capsys):
        monkeypatch.setattr(watch, "_dfs",
                            lambda *a, **k: pytest.fail("offline"))
        monkeypatch.setattr(watch, "_memory_fallbacks", lambda: {})
        rc = watch.main(["--domain", "example.com", "--dry-run"])
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out["checks"] == list(watch.PROFILES["weekly"])
        assert "nothing was called" in out["note"]


# ---------------------------------------------------------------------------
# link_graph + renderer
# ---------------------------------------------------------------------------

CRAWL_FIXTURE = {
    "summary": {"start_url": "https://x.com"},
    "pages": [
        {"url": "https://x.com", "status": 200,
         "internal_outlinks": [{"url": "https://x.com/a", "anchor": "A"},
                               {"url": "https://x.com/b", "anchor": "click here"}]},
        {"url": "https://x.com/a", "status": 200,
         "internal_outlinks": [{"url": "https://x.com", "anchor": "Home"},
                               {"url": "https://x.com/c", "anchor": "C"}]},
        {"url": "https://x.com/b", "status": 200,
         "internal_outlinks": [{"url": "https://x.com", "anchor": "Home"}]},
        {"url": "https://x.com/c", "status": 200, "internal_outlinks": []},
        {"url": "https://x.com/orphan", "status": 200, "internal_outlinks": []},
    ],
}


class TestLinkGraph:
    def test_analyse_orphans_and_links(self):
        result = link_graph.analyse(CRAWL_FIXTURE["pages"], "https://x.com")
        assert result["orphan_pages"] == ["https://x.com/orphan"]
        top = result["most_linked_pages"][0]
        assert top["url"] == "https://x.com" and top["inlinks"] == 2
        assert result["depth_distribution"] == {0: 1, 1: 2, 2: 1}
        assert result["unreachable_from_homepage"] == ["https://x.com/orphan"]
        assert result["anchor_quality"]["generic_anchor_count"] == 1

    def test_layout_positions_all_reachable(self):
        graph = link_graph_render.layout(CRAWL_FIXTURE)
        roles = {n["url"]: n["role"] for n in graph["nodes"]}
        assert roles["https://x.com"] == "home"
        # a page with zero inlinks is unreachable from home by definition
        assert roles["https://x.com/orphan"] == "unreachable"
        home = next(n for n in graph["nodes"] if n["role"] == "home")
        assert home["x"] == link_graph_render.CX
        assert home["y"] == link_graph_render.CY
        depth1 = [n for n in graph["nodes"] if n["depth"] == 1]
        assert all(n["x"] != link_graph_render.CX for n in depth1)

    def test_svg_contains_nodes_and_edges(self):
        graph = link_graph_render.layout(CRAWL_FIXTURE)
        svg = link_graph_render.render_svg(graph)
        assert svg.count("<circle") >= len(CRAWL_FIXTURE["pages"])
        assert "<line" in svg
        assert "<svg" in svg

    def test_render_html_keeps_svg_unescaped(self):
        graph = link_graph_render.layout(CRAWL_FIXTURE)
        analysis = link_graph.analyse(CRAWL_FIXTURE["pages"], "https://x.com")
        html = link_graph_render.render_html(CRAWL_FIXTURE, analysis, graph)
        assert "<svg" in html
        assert "&lt;svg" not in html
        assert '<div class="legend">' in html
        assert "&lt;div" not in html

SAMPLE_LOG = (
    '1.1.1.1 - - [18/Jul/2026:10:00:01 +0000] "GET /a HTTP/1.1" 200 1 "-" '
    '"Mozilla/5.0 (compatible; Googlebot/2.1)"\n'
    '1.1.1.1 - - [18/Jul/2026:10:00:02 +0000] "GET /b?utm=x HTTP/1.1" 404 1 "-" '
    '"Mozilla/5.0 (compatible; Googlebot/2.1)"\n'
    '1.1.1.1 - - [18/Jul/2026:10:00:03 +0000] "GET /c HTTP/1.1" 200 1 "-" '
    '"Mozilla/5.0 (compatible; GPTBot/1.2)"\n'
    '1.1.1.1 - - [18/Jul/2026:10:00:04 +0000] "GET /d HTTP/1.1" 200 1 "-" '
    '"Mozilla/5.0 Chrome/120"\n'
)


class TestLogAnalyzer:
    def test_bot_detection(self):
        assert log_analyzer.detect_bot("... Googlebot/2.1 ...") == "Googlebot"
        assert log_analyzer.detect_bot("... gptbot/1.0") == "GPTBot"
        assert log_analyzer.detect_bot("Mozilla/5.0 Chrome") is None

    def test_parse(self):
        result, paths = log_analyzer.parse_lines(SAMPLE_LOG.splitlines())
        assert result["lines_total"] == 4
        assert result["bot_requests_total"] == 3  # Chrome line ignored
        assert result["bots"]["Googlebot"]["hits"] == 2
        assert result["bots"]["Googlebot"]["parameter_url_pct"] == 50.0
        assert result["bots"]["Googlebot"]["status_distribution"]["404"] == 1


# ---------------------------------------------------------------------------
# report_build
# ---------------------------------------------------------------------------

class TestReportBuild:
    def test_template_uses_self_contained_font_stack(self):
        # Client PDFs are rendered from local files; remote web fonts can
        # produce blank glyphs in headless browser PDF output.
        assert "fonts.bunny.net" not in report_build.SHELL
        assert "Arial, Helvetica, sans-serif" in report_build.SHELL

    def test_decimal_score_extraction_does_not_drop_integer_part(self):
        score, _ = report_build._extract_score(
            "Overall SEO health: 60.6/100, up 3.6 points.")
        assert score == 60.6
        section = report_build._build_score_section(score, "", {})
        assert "60.6/100" in section
        assert "--score-deg:218.16deg" in section
        assert 'class="score-value decimal"' in section

    def test_heading_and_bold(self):
        body, _ = report_build.md_to_html("## Hello\n\nSome **bold** text")
        assert "<h2 id=\"hello\">Hello</h2>" in body
        assert "<strong>bold</strong>" in body

    def test_table(self):
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        body, _ = report_build.md_to_html(md)
        assert "<th>A</th>" in body and "<td>2</td>" in body

    def test_severity_badge(self):
        md = "| Severity | Issue |\n|---|---|\n| Critical | Broken |\n| Low | Polish |"
        body, _ = report_build.md_to_html(md)
        assert 'class="badge"' in body
        assert report_build.ORANGE in body   # critical colour
        assert report_build.EMERALD in body  # low colour

    def test_toc_collected(self):
        md = "## Alpha\n\nx\n\n## Beta\n\ny\n\n## Gamma\n\nz"
        _, toc = report_build.md_to_html(md)
        assert [t[2] for t in toc] == ["Alpha", "Beta", "Gamma"]

    def test_donut_chart(self):
        html = report_build.render_chart(
            '{"type": "donut", "title": "Score", "value": 64, "max": 100}')
        assert "<svg" in html and ">64<" in html
        assert "#F59E0B" in html  # 64% -> amber band

    def test_donut_score_bands(self):
        good = report_build.render_chart('{"type":"donut","value":80,"max":100}')
        bad = report_build.render_chart('{"type":"donut","value":20,"max":100}')
        assert report_build.EMERALD in good
        assert report_build.ORANGE in bad

    def test_bar_chart(self):
        html = report_build.render_chart(
            '{"type": "bar", "title": "Pillars", "data": [["Technical", 74]], "max": 100}')
        assert "bar-fill" in html and "Technical" in html

    def test_line_chart(self):
        html = report_build.render_chart(
            '{"type": "line", "title": "Clicks", "data": [["Mar", 1], ["Apr", 2]]}')
        assert "<polyline" in html

    def test_stats_cards(self):
        html = report_build.render_chart(
            '{"type": "stats", "data": [["Ref domains", "312", "+18"]]}')
        assert "stat-card" in html and "+18" in html

    def test_invalid_chart_falls_back(self):
        html = report_build.render_chart("not json")
        assert "chart-unparsed" in html

    def test_yaml_spec_accepted(self):
        yaml_block = ('type: bar\n'
                      'title: Pillars\n'
                      'data:\n'
                      '  - [Technical, 74]\n'
                      '  - [Content, 81]\n')
        spec = report_build.normalise_spec(yaml_block)
        assert spec["type"] == "bar"
        assert spec["data"] == [["Technical", 74], ["Content", 81]]

    def test_single_key_unwrap_and_label_value_dicts(self):
        # the exact shape weaker models emit: bare type word + YAML list
        block = ('donut\n'
                 '- label: "Overall"\n'
                 '  value: 33\n'
                 '- label: "Technical"\n'
                 '  value: 40\n')
        spec = report_build.normalise_spec(block)
        assert spec["type"] == "donut"
        assert spec["data"] == [["Overall", 33], ["Technical", 40]]

    def test_multi_segment_donut(self):
        html = report_build.render_chart(
            '{"type": "donut", "title": "Pillars",'
            ' "data": [["Technical", 40], ["Content", 25], ["Authority", 20]]}')
        assert "legend-item" in html
        assert html.count("stroke-dasharray") == 3

    def test_bare_list_becomes_bar(self):
        spec = report_build.normalise_spec('[["A", 1], ["B", 2]]')
        assert spec["type"] == "bar"

    def test_name_score_keys_normalised(self):
        spec = report_build.normalise_spec(
            '{"type": "bar", "data": [{"name": "X", "score": 5}]}')
        assert spec["data"] == [["X", 5]]

    def test_build_writes_file(self, tmp_path):
        md = tmp_path / "r.md"
        md.write_text("# My Report\n\nBody text", encoding="utf-8")
        out = report_build.build(md, tmp_path / "r.html", brand="Lee Beirne",
                                 title=None, footer=report_build.DEFAULT_FOOTER)
        html = out.read_text(encoding="utf-8")
        assert "My Report" in html
        assert "Lee Beirne" in html
        assert "leebeirne.com" in html

    def test_compare_chart(self):
        html = report_build.render_chart(
            '{"type": "compare", "title": "vs last", "max": 100,'
            ' "data": [["Technical", 70, 76], ["Content", 80, 72]]}')
        assert "cmp-before" in html and "cmp-after" in html
        assert "+6" in html and "-8" in html
        assert "previous" in html and "current" in html

    def test_onepager_extract(self):
        md = (
            "# Audit\n\n"
            "## Executive summary\n\nSolid base, weak links.\n\n"
            "## Scorecard\n\n| P | S |\n|---|---|\n| T | 74 |\n\n"
            "```chart\n{\"type\": \"donut\", \"title\": \"Score\", "
            "\"value\": 64, \"max\": 100}\n```\n\n"
            "## Findings by severity\n\n| Severity | F |\n|---|---|\n| Critical | x |\n\n"
            "## Recommendations and actions\n\n"
            "| # | Action | Priority |\n|---|---|---|\n"
            "| 1 | a | Critical |\n| 2 | b | High |\n| 3 | c | High |\n"
            "| 4 | d | Medium |\n| 5 | e | Medium |\n| 6 | f | Low |\n\n"
            "## Appendix\n\nraw data\n"
        )
        one = report_build.extract_onepager(md)
        assert "Executive summary" in one
        assert "Solid base, weak links." in one
        assert "```chart" in one
        assert "Recommendations" in one
        assert "| 5 | e |" in one and "| 6 | f |" not in one  # capped at 5
        assert "Appendix" not in one and "Findings by severity" not in one

    def test_onepager_build(self, tmp_path):
        md = tmp_path / "r.md"
        md.write_text(
            "# Audit\n\n## Executive summary\n\nText.\n\n"
            "## Recommendations\n\n| # | A |\n|---|---|\n| 1 | x |\n\n"
            "## Appendix\n\nstuff\n", encoding="utf-8")
        out = report_build.build(md, tmp_path / "one.html", brand="Lee Beirne",
                                 title=None, footer=report_build.DEFAULT_FOOTER,
                                 onepager=True)
        html = out.read_text(encoding="utf-8")
        assert 'class="onepager"' in html
        assert "Executive summary" in html
        assert "Appendix" not in html


# ---------------------------------------------------------------------------
# citation_score
# ---------------------------------------------------------------------------

CITATION_BASE = {
    "url": "https://x.com/guide", "status": 200, "noindex": False,
    "title": "Guide", "meta_description": "d", "canonical": "https://x.com/guide",
    "h1": ["Guide"], "h1_count": 1, "h2": [], "h2_count": 0, "list_count": 0,
    "time_elements": 0, "jsonld_has_dates": False, "meta_author": "",
    "has_rel_author": False, "number_density": 0.0, "word_count": 0,
    "images_total": 0, "images_missing_alt": 0, "schema_blocks": 0,
    "schema_types": [], "internal_link_count": 3, "external_link_count": 0,
    "first_h2_para_words": 0, "first_h2_para_text": "", "has_viewport": True,
    "html_lang": "en", "title_length": 5, "meta_description_length": 1,
}

CITATION_GOOD = {**CITATION_BASE,
    "h2": ["What is pour over coffee?", "How does it taste?", "Which is best?"],
    "h2_count": 3, "list_count": 2, "word_count": 1800,
    "first_h2_para_words": 60, "meta_author": "Lee Beirne",
    "jsonld_has_dates": True, "schema_types": ["Article", "BreadcrumbList"],
    "external_link_count": 3, "number_density": 12.0,
}


class TestCitationScore:
    def _crit(self, result, name):
        return next(c for c in result["criteria"] if c["criterion"] == name)

    def test_perfect_page_scores_high(self):
        result = citation_score.score_page(CITATION_GOOD)
        assert result["score"] >= 95
        assert result["grade"] == "Strong citation candidate"
        assert all(c["status"] == "pass" for c in result["criteria"])

    def test_noindex_gate(self):
        result = citation_score.score_page({**CITATION_GOOD, "noindex": True})
        assert result["score"] == 0
        assert "noindex" in result["gate"]

    def test_status_gate(self):
        result = citation_score.score_page({**CITATION_GOOD, "status": 404})
        assert result["score"] == 0
        assert "404" in result["gate"]

    def test_empty_page_scores_low(self):
        result = citation_score.score_page(CITATION_BASE)
        assert result["score"] < 40
        assert result["grade"] == "Not ready"

    def test_answer_block_tiers(self):
        thin = citation_score.score_page({**CITATION_BASE, "first_h2_para_words": 20})
        ideal = citation_score.score_page({**CITATION_BASE, "first_h2_para_words": 60})
        long = citation_score.score_page({**CITATION_BASE, "first_h2_para_words": 250})
        assert self._crit(thin, "Answer block")["points"] == 8
        assert self._crit(ideal, "Answer block")["points"] == 20
        assert self._crit(long, "Answer block")["points"] == 12

    def test_question_heading_detection(self):
        with_q = citation_score.score_page(
            {**CITATION_BASE, "h2": ["How does it work?"], "h2_count": 1})
        without_q = citation_score.score_page(
            {**CITATION_BASE, "h2": ["Overview"], "h2_count": 1})
        assert self._crit(with_q, "Question-form headings")["status"] == "pass"
        assert self._crit(without_q, "Question-form headings")["status"] == "fail"

    def test_partial_credit(self):
        one_link = citation_score.score_page({**CITATION_BASE, "external_link_count": 1})
        assert self._crit(one_link, "Outbound sourcing")["points"] == 6
        assert self._crit(one_link, "Outbound sourcing")["status"] == "partial"

    def test_failing_criteria_have_recommendations(self):
        result = citation_score.score_page(CITATION_BASE)
        for c in result["criteria"]:
            if c["status"] in ("fail", "partial"):
                assert c.get("recommendation"), f"{c['criterion']} missing recommendation"

    def test_disclaimer_present(self):
        result = citation_score.score_page(CITATION_GOOD)
        assert "cannot guarantee citation" in result["disclaimer"]

class TestSeoFix:
    PAGE = {
        "url": "https://acme.example/gear/best-grinders",
        "title": "",
        "h1": ["Best Grinders Guide"],
        "first_h2_para_text": "The best grinder for most people is a burr "
                              "grinder with consistent particle size.",
        "h2_count": 1, "word_count": 400, "has_viewport": False,
        "html_lang": "", "canonical": "", "schema_blocks": 0,
        "schema_types": [], "images_missing_alt": 0, "noindex": False,
        "internal_link_count": 5, "external_link_count": 1,
        "title_length": 0, "meta_description": "",
        "meta_description_length": 0, "h1_count": 1, "images_total": 0,
        "status": 200, "first_h2_para_words": 14,
    }

    def test_breadcrumb_json(self):
        crumb = seo_fix.build_breadcrumb_json("https://acme.example/gear/best-grinders")
        items = crumb["itemListElement"]
        assert items[0]["name"] == "Home"
        assert items[1]["name"] == "Gear"
        assert items[2]["item"] == "https://acme.example/gear/best-grinders"
        assert crumb["@type"] == "BreadcrumbList"

    def test_meta_draft_truncation(self):
        page = {"first_h2_para_text": " ".join(["word"] * 60), "title": "T"}
        draft = seo_fix.make_meta_draft(page)
        assert 50 <= len(draft) <= 155
        assert not draft.endswith(" ")

    def test_meta_draft_fallback_to_title(self):
        assert seo_fix.make_meta_draft({"first_h2_para_text": "",
                                        "title": "Hello"}) == "Hello"

    def test_derive_title_falls_back_to_draft(self):
        values = seo_fix.derive_values(self.PAGE, "", "en")
        assert values["title"] == "Best Grinders Guide | acme.example"

    def test_resolve_ready_and_skipped(self):
        rules = rule_engine.load_rules()
        by_id = {r["id"]: r for r in rules}
        values = seo_fix.derive_values(self.PAGE, "", "en")
        canonical = seo_fix.resolve_patch(by_id["missing-canonical"], values)
        assert canonical["status"] == "ready"
        assert "https://acme.example/gear/best-grinders" in canonical["content"]
        no_url = seo_fix.resolve_patch(by_id["missing-canonical"],
                                       {**values, "url": ""})
        assert no_url["status"] == "skipped"
        assert "missing required values" in no_url["reason"]

    def test_collect_patches_only_fired_rules(self):
        rules = rule_engine.load_rules()
        patches = seo_fix.collect_patches(self.PAGE, rules, "", "en")
        ids = {p["rule_id"] for p in patches}
        assert "missing-title" in ids and "missing-canonical" in ids
        assert "images-missing-alt" not in ids  # rule fired? no, alt is fine
        assert "page-noindex" not in ids        # rule not fired

    def test_apply_and_idempotency(self):
        html = ('<html><head></head><body><h1>Best Grinders Guide</h1>'
                "<h2>Which one?</h2><p>"
                + " ".join(["word"] * 60) + "</p></body></html>")
        rules = rule_engine.load_rules()
        page = seo_lint.parse_html(html, "https://acme.example/p")
        patches = seo_fix.collect_patches(page, rules, "https://acme.example/p", "en")
        ready = [p for p in patches if p["status"] == "ready"]
        assert ready
        new_html, applied = seo_fix.apply_patches(html, ready)
        assert "missing-canonical" in applied
        assert "missing-title" in applied
        assert "missing-viewport" in applied
        assert 'lang="en"' in new_html
        assert "<title>Best Grinders Guide | acme.example</title>" in new_html
        # idempotency: a second pass has nothing to do
        page2 = seo_lint.parse_html(new_html, "https://acme.example/p")
        patches2 = seo_fix.collect_patches(page2, rules, "https://acme.example/p", "en")
        assert patches2 == []

    def test_html_escaping_in_attributes(self):
        page = {**self.PAGE, "h1": ['Best "Quoted" Grinders']}
        values = seo_fix.derive_values(page, "", "en")
        rules = rule_engine.load_rules()
        by_id = {r["id"]: r for r in rules}
        patch = seo_fix.resolve_patch(by_id["missing-title"], values)
        assert "&quot;" in patch["content"]

class TestProjectMemory:
    def test_client_path(self, tmp_path):
        path = project_memory.client_path("Acme Ltd", start=tmp_path)
        assert path.name == "acme_ltd.yml"
        assert path.parent.name == "clients"

    def test_list_clients(self, tmp_path, monkeypatch):
        clients = tmp_path / "clients"
        clients.mkdir()
        (clients / "acme.yml").write_text("site:\n  url: https://acme.com\n")
        monkeypatch.chdir(tmp_path)
        assert project_memory.list_clients() == ["acme"]

    ENTITY_YAML = (
        "site:\n  url: https://acme.example\n"
        "entities:\n"
        "  - name: Acme Corp Ltd\n"
        "    type: Organization\n"
        "    description: Grinder maker\n"
        "    sameAs: [https://x.com/acme, https://linkedin.com/company/acme]\n"
        "  - name: Jane Doe\n"
        "    type: Person\n"
        "    role: Founder\n"
        "  - name: ''\n"          # malformed entry, should be skipped
    )

    def test_get_entities_normalises(self, tmp_path, monkeypatch):
        import yaml
        project = yaml.safe_load(self.ENTITY_YAML)
        entities = project_memory.get_entities(project)
        assert len(entities) == 2            # malformed entry skipped
        org = entities[0]
        assert org["type"] == "Organization"
        assert org["aliases"] == []
        person = entities[1]
        assert person["role"] == "Founder"

    def test_entities_cli(self, tmp_path, monkeypatch, capsys):
        clients = tmp_path / "clients"
        clients.mkdir()
        (clients / "acme.yml").write_text(self.ENTITY_YAML)
        monkeypatch.chdir(tmp_path)
        rc = project_memory.main(["entities", "--client", "acme"])
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out["count"] == 2


class TestSchemaFromMemory:
    def test_organization_from_memory(self, tmp_path, monkeypatch):
        clients = tmp_path / "clients"
        clients.mkdir()
        (clients / "acme.yml").write_text(TestProjectMemory.ENTITY_YAML)
        monkeypatch.chdir(tmp_path)
        fields = schema_gen.fields_from_memory("acme", "organization")
        assert fields["name"] == "Acme Corp Ltd"
        assert fields["url"] == "https://acme.example"
        assert fields["sameAs"] == ["https://x.com/acme",
                                    "https://linkedin.com/company/acme"]

    def test_person_from_memory(self, tmp_path, monkeypatch):
        clients = tmp_path / "clients"
        clients.mkdir()
        (clients / "acme.yml").write_text(TestProjectMemory.ENTITY_YAML)
        monkeypatch.chdir(tmp_path)
        fields = schema_gen.fields_from_memory("acme", "person")
        assert fields["jobTitle"] == "Founder"

    def test_missing_entity_type_raises(self, tmp_path, monkeypatch):
        clients = tmp_path / "clients"
        clients.mkdir()
        (clients / "acme.yml").write_text("site:\n  url: https://x.example\n")
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ValueError, match="No Organization entity"):
            schema_gen.fields_from_memory("acme", "organization")

    def test_unknown_client_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ValueError, match="No profile"):
            schema_gen.fields_from_memory("ghost", "organization")


# ---------------------------------------------------------------------------
# accessibility parsing
# ---------------------------------------------------------------------------

class TestAccessibilityParsing:
    def _page(self, html):
        return seo_lint.parse_html(html, "https://x.com")

    def test_label_for_counts_as_labelled(self):
        page = self._page('<input type="text" id="e"><label for="e">Email</label>')
        assert page["form_inputs_unlabelled"] == 0

    def test_wrapped_input_labelled(self):
        page = self._page('<label>Email <input type="text"></label>')
        assert page["form_inputs_unlabelled"] == 0

    def test_aria_label_counts(self):
        page = self._page('<input type="text" aria-label="Search">')
        assert page["form_inputs_unlabelled"] == 0

    def test_placeholder_is_not_a_label(self):
        page = self._page('<input type="text" placeholder="Search">')
        assert page["form_inputs_unlabelled"] == 1

    def test_hidden_and_submit_ignored(self):
        page = self._page('<input type="hidden" name="a"><input type="submit" value="Go">')
        assert page["form_inputs_unlabelled"] == 0

    def test_skip_link_detected(self):
        page = self._page('<a href="#main">Skip to main content</a><main>x</main>')
        assert page["has_skip_link"] is True
        assert page["has_main"] is True

    def test_heading_skip_detected(self):
        page = self._page("<h1>A</h1><h3>B</h3>")
        assert page["heading_skips"] == 1
        page2 = self._page("<h1>A</h1><h2>B</h2><h3>C</h3>")
        assert page2["heading_skips"] == 0

    def test_duplicate_ids(self):
        page = self._page('<div id="x"></div><span id="x"></span><p id="y"></p>')
        assert page["duplicate_ids"] == 1

    def test_empty_and_generic_links(self):
        page = self._page('<a href="/a"></a><a href="/b">click here</a>'
                          '<a href="/c">Our pricing</a>')
        assert page["empty_links"] == 1
        assert page["generic_link_texts"] == 1

    def test_empty_button_and_aria_button(self):
        page = self._page('<button></button><button aria-label="Close">×</button>')
        assert page["empty_buttons"] == 1

    def test_table_and_iframe(self):
        page = self._page('<table><tr><td>1</td></tr></table>'
                          '<table><tr><th>H</th></tr></table>'
                          '<iframe src="https://x.com"></iframe>'
                          '<iframe title="Map" src="https://y.com"></iframe>')
        assert page["tables_without_th"] == 1
        assert page["iframes_missing_title"] == 1

    def test_positive_tabindex(self):
        page = self._page('<a tabindex="2" href="/a">A</a><a tabindex="0" href="/b">B</a>')
        assert page["positive_tabindex"] == 1

    def test_wcag_passthrough_in_findings(self):
        rules = rule_engine.load_rules()
        a11y = [r for r in rules if r["category"] == "accessibility"]
        page = self._page('<input type="text" placeholder="Search">')
        outcome = rule_engine.run(page, a11y)
        finding = next(f for f in outcome["findings"]
                       if f["id"] == "form-input-unlabelled")
        assert finding["wcag"] == "1.3.1 + 4.1.2"
        assert finding["wcag_level"] == "A"


# ---------------------------------------------------------------------------
# CRO signal parsing
# ---------------------------------------------------------------------------

class TestCroParsing:
    def _page(self, html):
        return seo_lint.parse_html(html, "https://x.com")

    def test_cta_detection_anchor_and_button(self):
        page = self._page('<a href="/quote">Get a quote</a>'
                          '<button>Buy now</button>'
                          '<a href="/about">About us</a>')
        assert page["cta_count"] == 2
        assert "Get a quote" in page["cta_texts"]
        assert "Buy now" in page["cta_texts"]

    def test_cta_above_fold_position(self):
        early = self._page('<a href="/q">Get started</a>' + "<p>x</p>" * 40)
        assert early["cta_above_fold"] == 1
        late = self._page("<p>x</p>" * 40 + '<a href="/q">Get started</a>')
        assert late["cta_above_fold"] == 0

    def test_generic_primary_cta(self):
        page = self._page('<form><button>Submit</button></form>')
        assert page["primary_cta_generic"] is True
        page2 = self._page('<form><button>Get my quote</button></form>')
        assert page2["primary_cta_generic"] is False

    def test_form_friction_and_captcha(self):
        page = self._page('<form>' + "<input>" * 7 + '</form>'
                          '<script src="https://google.com/recaptcha/api.js"></script>')
        assert page["form_fields_max"] == 7
        assert page["form_has_captcha"] is True

    def test_tel_links(self):
        page = self._page('<a href="tel:+442071234567">Call us</a>')
        assert page["tel_links"] == 1

    def test_trust_and_urgency_counts(self):
        page = self._page('<p>Rated 5 stars, money-back guarantee, '
                          'trusted by 2,000 customers. Sale ends soon.</p>')
        assert page["trust_signal_count"] >= 3
        assert page["urgency_signal_count"] >= 1

    def test_faq_detection(self):
        by_heading = self._page('<h2>Frequently asked questions</h2><p>x</p>')
        assert by_heading["faq_present"] is True
        none_page = self._page('<h2>Our services</h2><p>x</p>')
        assert none_page["faq_present"] is False

    def test_live_chat_marker(self):
        page = self._page('<p>Chat with us</p><div id="intercom-container"></div>')
        assert page["live_chat"] is True


# ---------------------------------------------------------------------------
# spa_detect + render diff
# ---------------------------------------------------------------------------

SPA_SHELL = ('<html><head><title>App</title>'
             '<script src="/_next/static/chunks/main.js"></script>'
             '<script src="/_next/static/chunks/react.js"></script>'
             '<script id="__NEXT_DATA__" type="application/json">{}</script>'
             '</head><body><div id="root"></div></body></html>')

STATIC_PAGE = ("<html><head><title>Guide</title></head><body><h1>Guide</h1>"
               "<p>" + " ".join(["word"] * 300) + "</p>"
               '<a href="/a">A</a><a href="/b">B</a><a href="/c">C</a>'
               "</body></html>")


class TestSpaDetect:
    def test_spa_shell_detected(self):
        result = spa_detect.detect(SPA_SHELL, "https://spa.example")
        assert result["verdict"] == "spa"
        assert result["should_render"] is True
        signals = {s["signal"] for s in result["signals"]}
        assert "app_shell" in signals
        assert "framework_markers" in signals

    def test_static_page_not_spa(self):
        result = spa_detect.detect(STATIC_PAGE, "https://x.com")
        assert result["verdict"] == "static"
        assert result["should_render"] is False
        assert result["stats"]["visible_words"] >= 300

    def test_framework_markers_alone_maybe(self):
        html = ("<html><head></head><body><h1>Hi</h1><p>"
                + " ".join(["word"] * 200)
                + '</p><script id="__NEXT_DATA__" type="application/json">{}</script>'
                + "</body></html>")
        result = spa_detect.detect(html, "https://x.com")
        assert result["score"] >= 1


class TestRenderDiff:
    def test_diff_computes_ratio_and_verdict(self):
        import render_page
        raw = "<html><body><p>" + " ".join(["word"] * 50) + "</p></body></html>"
        rendered = ("<html><body><p>" + " ".join(["word"] * 50)
                    + " " + " ".join(["more"] * 150) + "</p></body></html>")
        diff = render_page.diff(raw, rendered, "https://x.com")
        assert diff["word_count"]["raw"] == 50
        assert diff["word_count"]["rendered"] == 200
        assert diff["js_content_ratio"] == 4.0
        assert "significant" in diff["verdict"]

    def test_js_content_gap_rule(self):
        rules = [r for r in rule_engine.load_rules()
                 if r["id"] == "js-content-gap"]
        fired = rule_engine.run({"js_content_ratio": 2.1}, rules)
        assert fired["failed"] == 1
        passed = rule_engine.run({"js_content_ratio": 1.1}, rules)
        assert passed["failed"] == 0


# ---------------------------------------------------------------------------
# seo_lint --format github
# ---------------------------------------------------------------------------

class TestGithubFormat:
    def _results(self):
        html = ("<html><head><title>T</title></head>"
                "<body><h1>Hi</h1></body></html>")
        rules = rule_engine.load_rules()
        page = seo_lint.parse_html(html, "dist/page.html")
        outcome = rule_engine.run(
            page, seo_lint.filter_rules(rules, None, local=True))
        outcome["url"] = "dist/page.html"
        return [outcome]

    def test_annotations_and_notice(self):
        out = seo_lint.render_github(self._results())
        assert "::notice file=dist/page.html,title=SEO score " in out
        # no title tag of length >= 30 -> findings exist; critical/high map
        # to ::error, medium/low to ::warning
        levels = {line.split(" ")[0] for line in out.splitlines()
                  if line.startswith("::")}
        assert "::error" in levels or "::warning" in levels
        assert "file=dist/page.html" in out

    def test_escaping(self):
        assert seo_lint._gh_escape("100%\nline2") == "100%25%0Aline2"
        assert seo_lint._gh_escape_prop("a:b,c") == "a%3Ab%2Cc"

    def test_main_github_format(self, tmp_path, capsys):
        page = tmp_path / "p.html"
        page.write_text("<html><head></head><body></body></html>",
                        encoding="utf-8")
        rc = seo_lint.main(["--file", str(page), "--format", "github"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "::error file=" in out          # missing-title is critical
        assert "title=missing-title" in out


# ---------------------------------------------------------------------------
# seo_pr_check
# ---------------------------------------------------------------------------

GOOD_HTML = ('<html lang="en"><head>'
             '<title>Best Coffee Grinders Guide 2026</title>'
             '<meta name="description" content="'
             + " ".join(["word"] * 25) + '">'
             '<link rel="canonical" href="https://x.com/g">'
             '<meta name="viewport" content="width=device-width">'
             '</head><body><h1>Best coffee grinders</h1><h2>Our top pick</h2>'
             "<p>" + " ".join(["word"] * 50) + "</p></body></html>")
BAD_HTML = ("<html><head></head><body><h1>Best grinders</h1></body></html>")


def _mh_rules():
    """Metadata + headings rules: fixtures score distinctly without needing
    a page that satisfies all 54 rules (CRO/a11y floors every tiny page)."""
    return [r for r in rule_engine.load_rules()
            if r["category"] in ("metadata", "headings")]


class TestSeoPrCheck:
    def test_lint_text_and_compare(self):
        rules = _mh_rules()
        before = seo_pr_check.lint_text(BAD_HTML, "p.html", rules)
        after = seo_pr_check.lint_text(GOOD_HTML, "p.html", rules)
        row = seo_pr_check.compare(before, after)
        assert row["delta"] == 54                     # 46 -> 100
        assert "missing-title" in row["fixed"]
        assert row["new"] == []

    def test_compare_new_file(self):
        rules = _mh_rules()
        after = seo_pr_check.lint_text(BAD_HTML, "p.html", rules)
        row = seo_pr_check.compare(None, after)
        assert row["before_score"] is None and row["delta"] is None
        assert len(row["new"]) == len(after["findings"])  # all "new"

    def test_gate_failures(self):
        rules = _mh_rules()
        bad = seo_pr_check.lint_text(BAD_HTML, "p.html", rules)
        good = seo_pr_check.lint_text(GOOD_HTML, "p.html", rules)
        regressed = seo_pr_check.compare(good, bad)     # 100 -> 46
        improved = seo_pr_check.compare(bad, good)      # got better
        reasons = seo_pr_check.gate_failures([regressed], None, None)
        assert any("new critical/high" in r for r in reasons)
        assert any("min-score 80" in r for r in
                   seo_pr_check.gate_failures([regressed], 80, None))
        assert any("max-drop 5" in r for r in
                   seo_pr_check.gate_failures([regressed], None, 5))
        assert seo_pr_check.gate_failures([improved], 80, 5) == []
        assert seo_pr_check.gate_failures([regressed], None, None,
                                          fail_on_new=False) == []

    def test_summarise_shape(self):
        rules = _mh_rules()
        bad = seo_pr_check.lint_text(BAD_HTML, "p.html", rules)
        good = seo_pr_check.lint_text(GOOD_HTML, "p.html", rules)
        row = seo_pr_check.compare(good, bad)
        failures = seo_pr_check.gate_failures([row], 80, 5)
        md = seo_pr_check.summarise([row], failures, 80, 5)
        assert md.startswith(seo_pr_check.MARKER)
        assert "`p.html`" in md and "**FAIL**" in md
        assert "missing-title" in md                # new-findings section
        clean = seo_pr_check.summarise(
            [seo_pr_check.compare(bad, good)], [], 80, 5)
        assert "**PASS**" in clean

    @pytest.mark.skipif(not shutil.which("git"), reason="git required")
    def test_main_against_real_repo(self, tmp_path, monkeypatch, capsys):
        def git(*args):
            subprocess.run(["git", *args], check=True, capture_output=True)

        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
        git("init", "-q", "-b", "main")
        (tmp_path / "page.html").write_text(GOOD_HTML, encoding="utf-8")
        (tmp_path / "note.txt").write_text("x", encoding="utf-8")
        git("add", ".")
        git("-c", "user.email=t@t", "-c", "user.name=t",
            "commit", "-qm", "v1")
        # regression commit: title/meta/canonical stripped
        (tmp_path / "page.html").write_text(BAD_HTML, encoding="utf-8")
        git("add", ".")
        git("-c", "user.email=t@t", "-c", "user.name=t",
            "commit", "-qm", "v2")
        rc = seo_pr_check.main(["--all-changed", "--base", "HEAD~1",
                                "--out", "summary.md"])
        assert rc == 1
        out = capsys.readouterr().out
        assert "::error file=page.html" in out
        assert "note.txt" not in out                # extension filter
        summary = (tmp_path / "summary.md").read_text(encoding="utf-8")
        assert "**FAIL**" in summary and "`page.html`" in summary
        # fix commit: gate passes again and reports the fix
        (tmp_path / "page.html").write_text(GOOD_HTML, encoding="utf-8")
        git("add", ".")
        git("-c", "user.email=t@t", "-c", "user.name=t",
            "commit", "-qm", "v3")
        rc = seo_pr_check.main(["--all-changed", "--base", "HEAD~1",
                                "--out", "summary2.md"])
        assert rc == 0
        summary = (tmp_path / "summary2.md").read_text(encoding="utf-8")
        assert "**PASS**" in summary


# ---------------------------------------------------------------------------
# sxo_analyser
# ---------------------------------------------------------------------------

class TestSxoAnalyser:
    @pytest.fixture(autouse=True)
    def temp_stores(self, monkeypatch, tmp_path):
        monkeypatch.setattr(recommend_store, "RECS_DIR", tmp_path / "recs")
        monkeypatch.setattr(event_log, "EVENTS_DIR", tmp_path / "events")
        yield

    @staticmethod
    def product_page():
        return {
            "url": "https://shop.example.com/products/grinder",
            "title": "Buy a Coffee Grinder", "h1": ["Coffee Grinder"],
            "h2": [], "schema_types": ["Product", "Offer"],
            "tables_total": 0, "cta_count": 1, "form_count": 0,
            "word_count": 450, "tel_links": 0,
        }

    @staticmethod
    def article_page():
        return {
            "url": "https://example.com/blog/grinder-guide",
            "title": "Coffee Grinder Guide", "h1": ["Coffee Grinder Guide"],
            "h2": ["How to choose"], "schema_types": ["Article"],
            "tables_total": 0, "cta_count": 0, "form_count": 0,
            "word_count": 1200, "tel_links": 0,
            "time_elements": ["2026-01-01"], "meta_author": "Lee",
        }

    @staticmethod
    def product_serp():
        items = []
        for n in range(6):
            items.append({"type": "organic",
                          "url": f"https://shop{n}.example.com/products/grinder",
                          "title": "Buy Coffee Grinder - Shop"})
        for n in range(2):
            items.append({"type": "organic",
                          "url": f"https://guide{n}.example.com/blog/grinder-guide",
                          "title": "Coffee Grinder Guide"})
        items.append({"type": "people_also_ask", "title": "What grinder?"})
        return {"result": [[{"items": items}]]}

    def test_classifies_product_and_hybrid(self):
        product = sxo_analyser.classify_page(self.product_page())
        assert product["primary"] == "product"
        assert product["confidence"] == "high"

        hybrid = self.article_page()
        hybrid.update({"cta_count": 2, "form_count": 1, "word_count": 700})
        classified = sxo_analyser.classify_page(hybrid)
        assert classified["primary"] == "hybrid"
        assert "strong editorial and conversion signals" in classified["evidence"]

    def test_serp_consensus_and_alignment(self):
        consensus = sxo_analyser.serp_consensus(self.product_serp())
        assert consensus["organic_results"] == 8
        assert consensus["dominant_type"] == "product"
        assert consensus["dominant_share"] == 0.75
        assert consensus["verdict"] == "strong_consensus"
        assert consensus["features"]["people_also_ask"] == 1

        target = sxo_analyser.classify_page(self.article_page())
        fit = sxo_analyser.alignment(target, consensus)
        assert fit["status"] == "mismatch"
        assert fit["score"] == 35

    def test_analysis_labels_missing_first_party_evidence(self):
        result = sxo_analyser.analyse(self.article_page(),
                                      "coffee grinder", self.product_serp())
        assert result["serp_fit"]["status"] == "mismatch"
        assert result["experience_baseline"]["conversion_readiness"]["rules"] == 10
        assert result["evidence_coverage"]["first_party_outcomes"] is False

    def test_file_cli_saves_high_confidence_mismatch(self, tmp_path, capsys):
        page = tmp_path / "guide.html"
        page.write_text(
            "<html><head><script type=\"application/ld+json\">"
            '{"@context":"https://schema.org","@type":"Article"}'
            "</script></head><body><h1>Coffee Grinder Guide</h1>"
            "<time>2026-01-01</time></body></html>", encoding="utf-8")
        serp = tmp_path / "serp.json"
        serp.write_text(json.dumps(self.product_serp()), encoding="utf-8")

        rc = sxo_analyser.main(["--file", str(page), "--serp-file", str(serp),
                                "--domain", "example.com", "--save"])
        assert rc == 0
        output = json.loads(capsys.readouterr().out)
        assert output["serp_fit"]["status"] == "mismatch"
        assert output["recommendation_saved"]["status"] == "open"
        recs = recommend_store.list_recs("example.com")
        assert len(recs) == 1
        assert recs[0]["source"] == "workflow:sxo"

    def test_keyword_candidate_is_not_a_confirmed_keyword(self):
        result = sxo_analyser.analyse(self.article_page())
        assert result["keyword"] is None
        assert result["keyword_candidate"] == "coffee grinder"
        assert result["keyword_confirmation_required"] is True

"""Test suite for the OpenCode SEO Suite scripts.

Run:  python -m pytest tests/ -v
All tests are offline — no API calls.
"""

from __future__ import annotations

import json
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
import indexnow  # noqa: E402
import ai_visibility  # noqa: E402
import link_graph  # noqa: E402
import link_graph_render  # noqa: E402
import log_analyzer  # noqa: E402
import project_memory  # noqa: E402
import report_build  # noqa: E402
import report_pdf  # noqa: E402
import report_publish  # noqa: E402
import rule_engine  # noqa: E402
import schema_gen  # noqa: E402
import seo_config  # noqa: E402
import seo_fix  # noqa: E402
import seo_lint  # noqa: E402


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
                + "<h1>Topic</h1><h2>Section</h2><p>"
                + " ".join(["word"] * 350)
                + '</p><img src="a.jpg" alt="descriptive">'
                + '<a href="/one">1</a><a href="/two">2</a>'
                + '<a href="/three">3</a>'
                + '<a href="https://source.example/study">source</a>'
                + "</body></html>")
        page = seo_lint.parse_html(good, "https://x.com/p")
        rules = rule_engine.load_rules()
        results = seo_lint.lint_pages([page], rules, None)
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
        assert report_build.PINK in body   # critical colour
        assert report_build.TEAL in body   # low colour

    def test_toc_collected(self):
        md = "## Alpha\n\nx\n\n## Beta\n\ny\n\n## Gamma\n\nz"
        _, toc = report_build.md_to_html(md)
        assert [t[2] for t in toc] == ["Alpha", "Beta", "Gamma"]

    def test_donut_chart(self):
        html = report_build.render_chart(
            '{"type": "donut", "title": "Score", "value": 64, "max": 100}')
        assert "<svg" in html and ">64<" in html
        assert report_build.YELLOW in html  # 64% -> amber band

    def test_donut_score_bands(self):
        good = report_build.render_chart('{"type":"donut","value":80,"max":100}')
        bad = report_build.render_chart('{"type":"donut","value":20,"max":100}')
        assert report_build.TEAL in good
        assert report_build.PINK in bad

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

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
import cost_ledger  # noqa: E402
import dfs_client  # noqa: E402
import drift_store  # noqa: E402
import log_analyzer  # noqa: E402
import project_memory  # noqa: E402
import report_build  # noqa: E402
import schema_gen  # noqa: E402
import seo_config  # noqa: E402


# ---------------------------------------------------------------------------
# schema_gen
# ---------------------------------------------------------------------------

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
# log_analyzer
# ---------------------------------------------------------------------------

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
        assert "<pre" in html

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
# project_memory
# ---------------------------------------------------------------------------

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

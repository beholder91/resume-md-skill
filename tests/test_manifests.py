import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
PLUGIN = ROOT / "plugins" / "resume-md"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_plugin_manifests_have_matching_identity():
    codex = load(PLUGIN / ".codex-plugin" / "plugin.json")
    claude = load(PLUGIN / ".claude-plugin" / "plugin.json")

    assert codex["name"] == claude["name"] == "resume-md"
    assert codex["version"] == claude["version"] == "0.1.0"
    assert codex["skills"] == "./skills/"
    assert (PLUGIN / "skills" / "resume-md" / "SKILL.md").is_file()


def test_marketplaces_point_to_local_plugin():
    codex = load(ROOT / ".agents" / "plugins" / "marketplace.json")
    claude = load(ROOT / ".claude-plugin" / "marketplace.json")

    assert codex["plugins"][0]["source"]["path"] == "./plugins/resume-md"
    assert claude["plugins"][0]["source"] == "./plugins/resume-md"


def test_skill_frontmatter_contains_only_required_fields():
    text = (PLUGIN / "skills" / "resume-md" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    frontmatter = text.split("---", 2)[1]

    assert "name:" in frontmatter
    assert "description:" in frontmatter
    assert "version:" not in frontmatter


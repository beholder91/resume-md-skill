import importlib.util
from pathlib import Path


ROOT = Path(__file__).parents[1]
INSTALLER = (
    ROOT
    / "plugins"
    / "resume-md"
    / "skills"
    / "resume-md"
    / "scripts"
    / "install.py"
)


def load_installer():
    spec = importlib.util.spec_from_file_location("resume_md_installer", INSTALLER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_installer_prefers_bundled_plugin_source():
    installer = load_installer()
    assert Path(installer.default_source()).resolve() == (
        ROOT / "plugins" / "resume-md"
    ).resolve()


def test_installer_has_actionable_dependency_hint():
    installer = load_installer()
    hint = installer.dependency_hint()
    assert "pango" in hint.casefold() or "WSL" in hint


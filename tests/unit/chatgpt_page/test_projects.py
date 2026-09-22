"""One scratch project, exact ChatGPT origin, and path containment."""

from __future__ import annotations

from pathlib import Path

from kronika.bridge.store import Store
from kronika.paths import state_dir
from kronika.projects import resolve


def test_development_default_uses_framenest_state_name(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    assert state_dir() == tmp_path / "framenest-chatgpt-page"
    assert state_dir("/var/lib/framenest/chatgpt-page") == Path(
        "/var/lib/framenest/chatgpt-page"
    )


def test_exactly_one_contained_project_resolves(tmp_path) -> None:
    store = Store(tmp_path)
    store.save_config(
        {
            "projects": {
                "analysis": {
                    "name": "analysis",
                    "url": "https://chatgpt.com/g/g-p-analysis/project",
                }
            }
        }
    )
    assert resolve(state_dir=store) == {
        "name": "analysis",
        "url": "https://chatgpt.com/g/g-p-analysis/project",
    }
    assert resolve("other", state_dir=store) is None


REJECTED_URLS = (
    "http://chatgpt.com/g/g-p-analysis",
    "https://chatgpt.com.evil/g/g-p-analysis",
    "https://user:pw@chatgpt.com/g/g-p-analysis",
    "https://chatgpt.com/g/g-p-analysis?x=1",
    "https://chatgpt.com/c/not-a-project",
    "https://chatgpt.com/g/g-p-analysis/../../etc",
)


def test_urls_outside_the_project_do_not_resolve(tmp_path) -> None:
    store = Store(tmp_path)
    for url in REJECTED_URLS:
        store.save_config({"projects": {"analysis": {"name": "analysis", "url": url}}})
        assert resolve(state_dir=store) is None


def test_zero_or_two_projects_do_not_resolve(tmp_path) -> None:
    store = Store(tmp_path)
    store.save_config({"projects": {}})
    assert resolve(state_dir=store) is None
    store.save_config(
        {
            "projects": {
                "one": {"url": "https://chatgpt.com/g/g-p-one"},
                "two": {"url": "https://chatgpt.com/g/g-p-two"},
            }
        }
    )
    assert resolve(state_dir=store) is None

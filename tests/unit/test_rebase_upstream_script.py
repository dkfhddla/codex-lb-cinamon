from pathlib import Path


def test_rebase_upstream_script_documents_safe_defaults() -> None:
    script = Path("scripts/rebase-upstream.ps1")

    assert script.exists()

    text = script.read_text(encoding="utf-8")
    assert "param(" in text
    assert "[switch]$Push" in text
    assert "https://github.com/CINEV/codex-lb-cinamon.git" in text
    assert "git fetch upstream" in text
    assert "git rebase upstream/main" in text
    assert "git push --force-with-lease origin $CurrentBranch" in text
    assert "git status --porcelain" in text

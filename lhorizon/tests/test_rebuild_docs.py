"""tests verifying freshness of documentation"""

import pytest

pytest.importorskip("sh")
pytest.importorskip("pydoc_markdown")

import sh


# TODO, maybe: figure out why docs render in a different order on github
#  runners, or, alternatively, never think about it ever again
def test_docs_freshness():
    """
    verify that api.md is up-to-date. warning: this test will fail if it is
    not run from the repository root directory. this is because I have built
    its paths in a very fragile way, because I want it to be runnable in a
    very minimal environment that cannot even import lhorizon.
    """
    # simplest to just run this as a subprocess
    test_docs = sh.pydoc_markdown(
        "--render-toc", "docs/pydoc-markdown.yml"
    ).stdout.decode().splitlines(True)
    with open("docs/api.md") as docfile:
        repo_docs = docfile.readlines()
    for line in test_docs:
        assert line in repo_docs

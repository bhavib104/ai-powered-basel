"""Chunking tests: page/section metadata and overlap behaviour."""

from __future__ import annotations

from app.services.chunking import chunk_pages


def test_headings_become_sections() -> None:
    pages = [
        (1, "1. Introduction\nBanks must hold capital proportional to risk."),
        (1, "2. Definitions\nCredit risk is the risk of loss from a borrower default."),
    ]
    drafts = chunk_pages(pages, max_chars=500)
    assert len(drafts) == 2
    assert drafts[0].section == "1. Introduction"
    assert drafts[0].page_number == 1
    assert drafts[1].section == "2. Definitions"
    assert [d.index for d in drafts] == [0, 1]


def test_long_paragraph_is_split_into_ordered_chunks() -> None:
    paragraph = ("lorem " * 300).strip()
    drafts = chunk_pages([(3, paragraph)], max_chars=200, overlap_chars=25)
    assert len(drafts) > 1
    for draft in drafts:
        assert draft.page_number == 3
        assert draft.text
        assert len(draft.text) <= 200


def test_page_number_flow_across_pages() -> None:
    pages = [(1, "first page text " * 20), (2, "second page text " * 20)]
    drafts = chunk_pages(pages, max_chars=80)
    numbers = {d.page_number for d in drafts}
    assert numbers == {1, 2}
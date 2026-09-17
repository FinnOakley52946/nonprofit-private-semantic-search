from content_visibility import SearchContext, visibility_filter


def test_donor_search_keeps_other_private_records_out() -> None:
    access = visibility_filter(SearchContext(donor_id="donor-1042"))

    assert access == {
        "$or": [
            {"content_type": "campaign_report", "visibility": "public"},
            {
                "content_type": "donor_receipt",
                "donor_id": "donor-1042",
            },
        ]
    }


def test_anonymous_search_only_requests_public_reports() -> None:
    access = visibility_filter(SearchContext())

    assert access == {
        "$or": [{"content_type": "campaign_report", "visibility": "public"}]
    }

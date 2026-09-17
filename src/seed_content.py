from nonprofit_search import InfraiClient


DOCUMENTS = [
    {
        "id": "receipt-donor-1042",
        "text": "Receipt for donor 1042: 75 USD received for the community clinic fund.",
        "metadata": {
            "content_type": "donor_receipt",
            "donor_id": "donor-1042",
            "visibility": "private",
            "title": "Community clinic donation receipt",
        },
    },
    {
        "id": "reminder-clinic-2026-09",
        "text": "Volunteer reminder: clinic intake shift starts Saturday at 08:30.",
        "metadata": {
            "content_type": "volunteer_reminder",
            "program_id": "clinic-intake",
            "visibility": "program",
            "title": "September clinic intake shift",
        },
    },
    {
        "id": "report-clinic-q2",
        "text": "Campaign report: the community clinic fund served 312 patients in Q2.",
        "metadata": {
            "content_type": "campaign_report",
            "visibility": "public",
            "title": "Community clinic Q2 report",
        },
    },
]


def main() -> None:
    client = InfraiClient()
    vectors = []
    for document in DOCUMENTS:
        vectors.append(
            {
                "id": document["id"],
                "embedding": client.embed(document["text"]),
                "metadata": document["metadata"],
            }
        )
    client.create_collection(len(vectors[0]["embedding"]))
    client.upsert(vectors)
    print(f"Indexed {len(vectors)} nonprofit records.")


if __name__ == "__main__":
    main()

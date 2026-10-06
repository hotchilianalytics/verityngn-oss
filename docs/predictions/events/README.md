# Event catalog schema

Each `{lane}/{entity}.json` is a list-or-object catalog:

```json
{
  "schema_version": "1.0",
  "lane": "video | text | fomc",
  "speaker_id": "ceo_pltr_karp",
  "ticker": "PLTR",
  "events": [
    {
      "event_id": "pltr-2026-05-04",
      "event_date": "2026-05-04",
      "kind": "earnings",
      "window": "pre",
      "source_id": "xe84cwQJKaE",
      "source_url": "https://www.youtube.com/watch?v=xe84cwQJKaE",
      "recorded": "2026-03-12",
      "outcome_kind": "equity_car"
    }
  ]
}
```

Populate with `scripts/build_event_catalog.py`. Outcome join via `verityngn.services.timeseries.outcomes.outcome_for`.

# Wear-Time and Valid-Day Protocols

This file is the placeholder for executable protocol definitions. Do not add MVPA or sedentary thresholds until their metric, device placement, unit and validation source are explicit.

## Protocol fields

Each protocol version should record:

- protocol identifier
- protocol label
- source citation or documentation URL
- source version/date
- device
- device placement
- metric
- unit
- epoch length
- wear-time rule
- valid-day rule
- minimum number of valid days
- applicability constraints
- implementation function

## Initial protocol candidates

| Protocol ID | Purpose | Status |
|---|---|---|
| `wake_wear_10h_min4` | Baseline wake-wear completeness comparison using `PAXWWMD >= 600` and at least 4 valid days | Implemented as candidate |
| `wake_wear_12h_min4` | Stricter wake-wear completeness comparison using `PAXWWMD >= 720` and at least 4 valid days | Implemented as candidate |
| `valid_minutes_20h_min4` | 24-hour completeness comparison using `PAXVMD >= 1200` and at least 4 valid days | Implemented as candidate |



## Review Status

The current executable protocols have been reviewed by the project lead and accepted as completeness/sensitivity rules only.

Review artifacts:

```text
docs/protocols/protocol_review_sheet.csv
docs/protocols/protocol_review_sheet.md
reports/protocol_review_status.json
```

Current policy:

```text
Approved protocols are data completeness/sensitivity rules only; do not claim MVPA or sedentary classification.
```


Review outcome:

```text
wake_wear_10h_min4: accepted as baseline completeness rule
wake_wear_12h_min4: accepted as stricter sensitivity completeness rule
valid_minutes_20h_min4: accepted as 24-hour completeness rule
```

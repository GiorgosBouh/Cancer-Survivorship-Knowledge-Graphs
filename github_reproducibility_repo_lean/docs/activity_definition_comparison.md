# Activity Definition Comparison Experiment

This experiment is the centre of the project: two researchers may analyse the same accelerometer data and reach different conclusions about whether a cancer survivor appears physically inactive, highly sedentary, or meeting an activity definition. The framework makes each classification traceable to the cut-points, wear-time rules, bout definitions, semantic assumptions, and provenance that produced it.

## Data Scope

- Source: NHANES 2003-2006 hip-worn ActiGraph PAM raw minute data.
- Participants with self-reported cancer history and PAM records: 768.
- Daily rows with derived threshold features: 5,367.
- These rules are applied only to hip ActiGraph counts. They are not applied to 2011-2014 wrist MIMS.

## What Is Being Compared

- Valid-day inclusion: >=10 hours versus >=12 hours of reliable/in-calibration minutes.
- Intensity cut-points: >=760 versus >=2020 counts/min.
- Bout rule: any qualifying minute versus strict uninterrupted 10-minute bouts.
- Demonstration classification: mean >=30 min/day among participants with >=4 valid 10-hour days. This is a methodological threshold for comparing definitions, not an autonomous clinical decision rule.

## Central Research Claim

The same person can change category when the accelerometry definition changes. The person did not biologically change; the processing rule changed. The knowledge graph preserves that rule so the result can be audited instead of treated as a context-free activity label.

## Main Result

- valid_day_10h_vs_12h_min4: denominator 768; left true 722; right true 722; discordant 0. This source has near-complete valid PAM days, so this wear-time sensitivity did not change eligibility here.
- mvpa_760_vs_2020_any_ge30min_day: denominator 722; left true 457; right true 58; discordant 399. Changing the MVPA cut-point changes who crosses the same demonstration activity threshold.
- mvpa_2020_any_vs_10min_bout_ge30min_day: denominator 722; left true 58; right true 11; discordant 47. Adding a bout rule changes who crosses the same demonstration activity threshold.
- mvpa_760_any_vs_10min_bout_ge30min_day: denominator 722; left true 457; right true 50; discordant 407. Adding a bout rule has a larger effect when the lower intensity cut-point is used.

## Interpretation Boundary

The result supports the paper's core claim: semantic harmonisation preserves the rule that produced each activity label, so researchers can see whether a difference is biological/clinical or caused by processing choices. It does not convert wrist MIMS to steps, does not infer MVPA from MIMS, and does not prescribe rehabilitation.

## Provenance

- CDC PCD NHANES 2003-2006 ActiGraph processing reference: https://www.cdc.gov/pcd/issues/2016/16_0159.htm
- NHANES accelerometry threshold catalog: https://pmc.ncbi.nlm.nih.gov/articles/PMC3457743/
- Published threshold comparison reference: https://pubmed.ncbi.nlm.nih.gov/25889192/

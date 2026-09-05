# Cover Letter Draft

Dear Editors,

Please consider the manuscript "When Definitions Change Conclusions: An Auditable Knowledge Graph for Accelerometer Use in Cancer Survivorship Research" for the Journal of Web Semantics special issue on Knowledge Engineering Automation.

The manuscript starts from a practical reproducibility problem: the same cancer survivor can be treated differently across studies because accelerometer definitions differ. Valid wear rules, minimum day rules, source metrics, body placement, and activity thresholds can change eligibility and activity interpretation even when the underlying data are unchanged.

The paper presents a reproducible knowledge engineering framework that turns these definitions, provenance records, expert review decisions, and semantic compatibility constraints into auditable knowledge graph artifacts. The use case is cancer survivorship research using public NHANES accelerometry data, with comparison sources from PhysioNet steps and NHANES hip ActiGraph data.

The main contribution is not a clinical physical activity classifier. Instead, the paper demonstrates how Semantic Web methods can make methodological definitions inspectable and can prevent invalid harmonisation claims, such as transferring hip ActiGraph counts per minute thresholds to wrist MIMS or interpreting self reported cancer type codes as histology confirmed diagnoses. The generated pilot graph contains 9,324 triples, passes pySHACL validation, and exposes nine reviewer oriented competency questions. Expert reviewed NCIt mappings are represented only as qualified mappings from self reported source codes.

The work has not been published previously and is not under consideration elsewhere. All authors should confirm the final authorship order, competing interest declaration, funding statement, and data/code availability statement before submission.

Sincerely,

TODO: Corresponding author name
TODO: Corresponding author affiliation
TODO: Corresponding author email

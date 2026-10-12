SAMPLE DOCUMENT FOR DEMONSTRATION PURPOSES ONLY — NOT OFFICIAL REGULATION

1. Introduction

This document is synthetic sample content written for a demonstration platform. It paraphrases common capital-adequacy concepts in plain language. It is not issued by any regulator, does not state legal requirements, and must not be quoted as authoritative. Real deployments should ingest the official texts from the regulator's website using the exact identifiers and versions shown there.

2. Risk-Weighted Assets — Standardised Approach

2.1 Purpose

Under the standardised approach a bank assigns a risk weight to each on-balance-sheet exposure and converts the exposure amount into risk-weighted assets, or RWA. The RWA is the exposure amount after credit-risk mitigation, multiplied by the applicable risk weight. Higher risk weights produce higher capital charges, so correct classification of the counterparty and its rating is critical.

2.2 Counterparty Classification

Exposures are classified into exposure classes. The platform used here supports five classes: sovereign, bank, corporate, retail, and real-estate. Classification determines which rule table applies. Mixing up classes — for example booking a corporate loan as a retail mortgage — changes the assigned risk weight and therefore the resulting RWA. Classifying correctly is a data-quality responsibility, not a modelling choice.

2.3 Illustrative Risk Weight Table

For corporate exposures the following illustrative risk weights apply by external credit assessment, shown here only as sample values:

AAA 20 percent. AA 20 percent. A 60 percent. BBB 90 percent. BB 110 percent. B 130 percent. CCC 150 percent. No external rating 100 percent. Defaulted exposures are treated separately under the defaulted-exposure framework rather than the rating ladder.

3. Credit Risk Mitigation

3.1 Eligible Collateral

A bank may reduce the exposure amount used for RWA purposes with eligible collateral. Not every asset qualifies. The simple approach used in this platform recognises cash and high-quality government bonds as eligible collateral, each with a fixed haircut. Cash has a zero haircut. Government bonds have a five percent haircut. Corporate bonds, real estate and other collateral types are recorded but do not reduce the exposure in this simplified framework — they are ignored rather than guessed.

3.2 Calculation Order

The platform computes the collateral credit as the eligible collateral value after haircuts, capped at the exposure amount. The eligible exposure amount is the original exposure minus the collateral credit. The RWA is the eligible amount multiplied by the risk weight. Each step is recorded in the explanation stored with the calculation result so an auditor can replay the numbers.

4. Unsupported Cases

If a counterparty rating grade, exposure class, or the collateral arrangement does not map to a rule, the platform does not invent a weight. It marks the exposure as unsupported and stores the reason, such as an unsupported exposure class or an unsupported rating grade. Unsupported amounts are excluded from the total RWA and must be reviewed by a risk analyst. Guessing would hide the gap; flagging makes it visible.

5. Limitations

Because this file is sample content, the specific percentages above must not be used for compliance. Always bind the platform to an effective-dated, versioned rule table supplied from the real regulatory texts.
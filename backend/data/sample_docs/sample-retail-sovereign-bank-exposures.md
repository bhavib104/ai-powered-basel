SAMPLE DOCUMENT FOR DEMONSTRATION PURPOSES ONLY — NOT OFFICIAL REGULATION

1. Introduction

This document is synthetic sample content for a demonstration platform. It paraphrases common concepts about retail and sovereign lending in plain language. It is not issued by any regulator, does not state legal requirements, and must not be quoted as authoritative.

2. Retail Exposures

2.1 What Counts as Retail

Retail exposures are loans to individuals or small businesses that meet size and granularity criteria. Personal loans, credit cards and small-business facilities are typical. Because retail portfolios are highly granular and diversified, the standardised framework applies a flat, moderate risk weight across all internal grades in this sample platform.

2.2 Residential Mortgages

Residential real-estate lending to individuals is normally treated more favourably than unsecured retail lending, provided the loan is adequately secured by a first mortgage on the residential property and the loan-to-value relationship is prudent. In the sample rules used here every internal rating grade maps to a thirty-five percent risk weight for real-estate exposures. The real-life treatment considers loan-to-value thresholds and the existence of guarantees, which this demonstration omits for simplicity.

2.3 Data Requirements

Mortgage exposures need accurate maturity, currency and property-linking data. A broken link between the loan and its collateral record would be detected by the data-quality checks, and the underlying exposure flagged rather than silently treated as unsecured.

3. Sovereign and Bank Exposures

3.1 Sovereign Exposures

Sovereign exposures are claims on central governments and the central bank. They are generally perceived as the lowest-risk lending category and therefore attract the lowest risk weights under the sample rule table. Ratings published by external credit assessment institutions are mapped through the same rating ladder used for other classes.

3.2 Bank Exposures

Interbank lending is short-term by design. The sample platform applies the risk weight associated with the bank's external rating, mirroring the corporate ladder but with its own rate schedule. Maturity mismatches and undrawn commitments can change the exposure amount used, so the platform reports drawn, undrawn and total amounts separately.

4. Defaulted Exposures

An exposure is considered defaulted when the obligor is unlikely to pay its obligations in full, or when any amount is past due for a defined number of days. Defaulted exposures are removed from the standard rating ladder and handled under a separate framework with distinctly higher treatment. The platform records a defaulted flag on each exposure so the calculation engine can branch to the correct treatment deterministically.

5. Caveats

Retail, mortgage, sovereign and bank percentages in this sample file are illustrations only. Bind the platform to the real, versioned regulatory texts and an effective-dated rule table for any compliance use.
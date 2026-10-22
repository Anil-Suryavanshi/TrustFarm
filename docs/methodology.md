# Methodology and limitations

Freshness is 0 for timestamps over the configured age threshold. Completeness is 0 when a required value is absent. Validity is 0 outside configured physical limits. Consistency is reduced for a large change or repeated sequence. An incomplete current network produces `INSUFFICIENT_DATA`; a score below the configured action minimum produces `VERIFY_DATA`.

The baseline uses only a soil-moisture threshold. The proposed decision checks quality first. Precision, recall, F1, false-positive rate and confusion matrix are calculated against injected labels only in a controlled experiment. This is an educational simulation, not field validation.

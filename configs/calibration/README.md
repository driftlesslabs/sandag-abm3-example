# Calibration coefficient references

Each adjustable coefficient must affect the model's utility specification.
For tour mode choice, the specification references generic coefficient names;
`tour_mode_choice_coefficients_template.csv` maps those names to coefficients
for each tour purpose. An entry in the template alone does not connect a
coefficient to a utility.

The zero-auto individual-tour calibration row (`util_calib_za`) uses
`coef_calib_base` for `SHARED2`, making it the fixed reference alternative.
Accordingly, the calibration tables omit `coef_calib_za_SHARED2_*` rows for
work, university, school, maintenance, discretionary, and at-work tours.
Adjusting those unused constants cannot change utilities. Connecting all of
them would also remove the existing fixed reference in that calibration row.

The utility specification, coefficient files, template, and survey target data
retain their existing values. The unused template and coefficient entries are
not adjustable calibration targets. Reference-mode counts remain available to
the helper's model/target summaries and reports.

## Empty modeled segments

Tour-mode target rescaling requires modeled tours in each auto-sufficiency /
purpose segment with positive survey targets. If such a segment is empty,
the helper raises an error identifying the segment and its survey target
total. Calibration stops rather than scaling the targets to zero and falsely
reporting convergence. This applies to regular tours and at-work subtours,
including requests for a mode with a zero target inside an unsupported segment.

Resolve missing sample support by increasing the simulation sample or
reconciling population and segment definitions with the survey data before
retrying. A mode with no modeled tours inside an otherwise populated segment
is still calibratable. Segments with zero modeled tours and zero survey targets
continue to return zero targets.

For nonempty segments, the existing scaling policy is unchanged: preserve
transit counts when possible and scale non-transit targets to the remaining
total; if transit targets exceed the modeled total, scale all mode targets.
This change does not resolve the separate modeling question of whether that
fallback policy is appropriate.

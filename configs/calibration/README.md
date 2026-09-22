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

# Tagset: ETCBC-like v1.0 (Project Standard)

This project standardizes morphology using an **ETCBC-like feature model**.

## Token object (source of truth)
Each token is found in `verses[].tokens[]` and includes:
- `surface` — pointed form as written
- `lemma` — pointed dictionary form
- `root` — triliteral root when applicable; else `—`
- `pos` — display POS label
- `features` — machine-readable features (ETCBC-like)
- `morph` — compact display string derived from `features`
- `gloss` — short English gloss

## POS labels
`VERB`, `NOUN`, `ADJ`, `PROPN`, `PRON`, `PREP`, `DET`, `CONJ`, `PARTICLE`

## Feature keys
Common:
- `pos`, `lemma`, `root`
- `prefixes` (array) e.g. `["ו","ה"]`
- `prep_prefixes` (array) e.g. `["ל"]`
- `definite` (bool)
- `suffix` (e.g. `1cs`, `2ms`, `3ms`, `1cp`)
- `number` (`sg|pl|dual`)
- `gender` (`m|f`)
- `state` (`abs|cons|abs?|cons?`)

Verb-specific (when available):
- `stem` (Qal, Hifil, Piel, ...)
- `conjugation` (Perfect, Imperfect, Wayyiqtol, Imperative, InfC, InfA, Participle)
- `mood` (optional; Cohortative, Jussive)
- `person` (1,2,3)
- `object_suffix` (e.g. `1cs`)

## Compact morph examples
- `V;Qal;Imperfect;3ms;Obj=1cs`
- `N;mpl;abs;Suf=2ms`
- `PARTICLE`

`features` is the authoritative representation; `morph` is display-only.

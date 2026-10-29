# AI Memory Boundary Fit: De-identified Study Data

De-identified participant-level data for the manuscript *Remembering or monitoring? Contextual fit of simulated AI memory cues and consumer trust* (Huang, Huang, & Guo; prepared for submission to *Frontiers in Psychology*).

Six interactive scenario experiments (total *N* = 2,140) test how an AI assistant's memory type (no memory / relevant memory / intrusive memory) shapes consumer trust, purchase intention, data-sharing willingness, and loyalty, and whether the effects operate through **Memory Boundary Fit (MBF)** — the degree to which remembered information fits the consumer's contextual boundary for the current interaction.

## Datasets

| File | N | Design | Key measures |
|---|---:|---|---|
| `data/study1_memory_data.csv` | 264 | Memory type (3 cells) | Trust, purchase intention, continued use, MBF |
| `data/study2_memory_data.csv` | 289 | Memory type (3 cells) | Trust, MBF, relational warmth, surveillance concern |
| `data/study3_memory_data.csv` | 410 | Memory type × product sensitivity (6 cells) | Trust |
| `data/study4_memory_data.csv` | 516 | Memory type × control interface (6 cells) | Trust, MBF |
| `data/study5_memory_data.csv` | 318 | Memory type (3 cells) | Transactional, data-sharing, and relational engagement; MBF |
| `data/study6_memory_data.csv` | 343 | Memory type (3 cells) | Privacy trust, loyalty, opt-in intention, platform trust, MBF |
| `validation/mbf_validation_data.csv` | 234 | Item-level validation sample | MBF items, IUIPC privacy concern, relational warmth, surveillance concern, trust |

Additional files:

- `data/demographics_by_participant.csv`: participant-level demographics for the pooled sample (age, gender, student status, testing channel only)
- `data/demographics_summary.csv`: summary demographics by study
- `data/data_dictionary.md`: variable descriptions for every dataset

## Notes on the data

- All multi-item constructs were measured on seven-point scales; item-level responses are provided where available, and composite scores are the mean of their items.
- Data were collected between March and June 2026 under a protocol approved by the Institutional Review Board of Zhejiang Business College (Protocol No. ZJBCSCCT-2026-EXP007). Participants provided electronic informed consent and were debriefed.
- The datasets are fully de-identified: the only person-level fields are age, gender, student status, and testing channel. Raw screening logs and conversation logs are withheld under the IRB's privacy conditions.

## Availability of other materials

The stimulus protocol and supplementary tables accompany the article as Supplementary Material. Analysis code and exact statistics are available from the corresponding author upon reasonable request.

## License and citation

The datasets are released under CC BY 4.0 (see `LICENSE`). If you use these data, please cite the associated article (see `CITATION.cff`).

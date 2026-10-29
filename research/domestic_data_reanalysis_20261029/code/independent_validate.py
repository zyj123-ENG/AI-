#!/usr/bin/env python3
"""Independent point-estimate validation for the archived Study 4 observations.

Requires pandas and numpy. No bootstrap or source-author model is run. Only
aggregate checks are exported; participant keys and local paths are not logged.

Example, from the reanalysis folder:
    python code/independent_validate.py \
        --source source/author_original/data/study4_memory_data.csv \
        --results results

--output optionally selects the JSON destination. The default is the sibling
validation/独立复算.json. Result CSVs and original observations are read only.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd


RAW_COLUMNS = ["Participant_ID", "Age", "Gender", "Grade", "Testing_Channel",
               "Memory_Type", "Control_Interface", "MBF",
               "Trust_Item1", "Trust_Item2", "Trust_Item3"]
ITEMS = ["Trust_Item1", "Trust_Item2", "Trust_Item3"]
METRICS = ["trust_mean", "trust_item1", "trust_item2", "trust_item3",
           "mbf_author_composite"]
MEMORIES = ["No Memory", "Relevant Memory", "Intrusive Memory"]
CONTROLS = ["No Control", "Editable Dashboard"]
CELLS = {
    ("No Memory", "No Control"): "none_no_control",
    ("No Memory", "Editable Dashboard"): "none_dashboard",
    ("Relevant Memory", "No Control"): "relevant_no_control",
    ("Relevant Memory", "Editable Dashboard"): "relevant_dashboard",
    ("Intrusive Memory", "No Control"): "intrusive_no_control",
    ("Intrusive Memory", "Editable Dashboard"): "intrusive_dashboard",
}
CHANNELS = ["Campus session", "Campus resident session", "Online/network test"]
TERMS = ["intercept_none_no_control", "relevant_vs_none_no_control",
         "intrusive_vs_none_no_control", "dashboard_with_no_memory",
         "relevant_dashboard_interaction", "intrusive_dashboard_interaction"]
TOLERANCE = 1e-10


class ValidationError(Exception):
    """A safe error whose message does not contain source paths or records."""


def require(value, message):
    if not bool(value):
        raise ValidationError(message)


def read_csv(path, columns, label):
    try:
        return pd.read_csv(path, usecols=columns)
    except Exception:
        raise ValidationError(f"Cannot read required fields for {label}.") from None


def match_tables(actual, expected, keys, count, label):
    try:
        joined = actual.merge(expected, on=keys, how="outer",
                              validate="one_to_one", indicator=True)
    except Exception:
        raise ValidationError(f"Invalid result keys for {label}.") from None
    require(len(joined) == count and joined["_merge"].eq("both").all(),
            f"Incomplete or unexpected result keys for {label}.")
    return joined


def numeric_comparison(joined, columns):
    """Compare independently calculated *_python columns with reported values."""
    result = {}
    for column in columns:
        error = (joined[f"{column}_python"] - joined[column]).abs()
        result[column] = {"max_absolute_error": float(error.max()),
                          "all_match": bool(error.lt(TOLERANCE).all())}
        joined[f"{column}_absolute_error"] = error
    return result


def load_source(source_file, results):
    try:
        manifest = json.loads((results.parent / "来源与许可.json")
                              .read_text(encoding="utf-8-sig"))
        entry = next(row for row in manifest["files"]
                     if row["file"].endswith("/data/study4_memory_data.csv"))
        digest = hashlib.sha256(source_file.read_bytes()).hexdigest()
    except Exception:
        raise ValidationError("Cannot verify source-file provenance.") from None
    require(digest == entry["sha256"], "Source hash differs from the fixed version.")
    data = read_csv(source_file, RAW_COLUMNS, "original observations")
    require(len(data) == 516, "Unexpected source sample size.")
    require(not data[RAW_COLUMNS].isna().any().any(), "Missing source fields.")
    require(data["Participant_ID"].nunique() == 516, "Duplicate participant key.")
    require(set(data["Memory_Type"]) == set(MEMORIES), "Unexpected memory labels.")
    require(set(data["Control_Interface"]) == set(CONTROLS), "Unexpected interface labels.")
    require(set(data["Testing_Channel"]) == set(CHANNELS), "Unexpected testing channels.")
    require(data["Age"].between(18, 62).all(), "Unexpected age eligibility.")
    require(data[ITEMS].isin(range(1, 8)).all().all(), "Invalid trust-item categories.")
    require(data["MBF"].between(1, 7).all(), "Invalid author MBF composite.")
    data = data.copy()
    data["cell"] = [CELLS[(memory, control)] for memory, control in
                    zip(data["Memory_Type"], data["Control_Interface"])]
    # Retain original positive-item scoring; no reverse transformation.
    data["trust_mean"] = data[ITEMS].mean(axis="columns")
    for index, column in enumerate(ITEMS, 1):
        data[f"trust_item{index}"] = data[column]
    data["mbf_author_composite"] = data["MBF"]
    campus = data["Testing_Channel"].isin(CHANNELS[:2])
    require(int(campus.sum()) == 403, "Unexpected campus sensitivity size.")
    expected_counts = dict(zip(CELLS.values(), [88, 88, 84, 84, 86, 86]))
    require(data["cell"].value_counts().to_dict() == expected_counts,
            "Unexpected full-sample cell sizes.")
    samples = {"all_516": data, "campus_403": data.loc[campus].copy()}
    identity = {"original_repo_path": "data/study4_memory_data.csv",
                "sha256": digest, "matches_fixed_source": True,
                "source_commit": manifest["pinned_commit"]}
    integrity = {
        "participants": 516, "unique_anonymous_keys": 516,
        "exact_duplicate_rows": int(data[RAW_COLUMNS].duplicated().sum()),
        "age_min": int(data["Age"].min()), "age_max": int(data["Age"].max()),
        "under_18": int(data["Age"].lt(18).sum()),
        "missing_required_fields": 0,
        "channel_counts": {key: int(value) for key, value in
                           data["Testing_Channel"].value_counts().items()},
        "trust_items_all_original_integer_1_to_7": True,
        "author_mbf_within_1_to_7": True,
        "participant_values_exported": False,
        "parsed_fields": RAW_COLUMNS,
    }
    return samples, identity, integrity


def cell_estimates(samples):
    rows = []
    for sample, people in samples.items():
        for (memory, _), cell in CELLS.items():
            observations = people.loc[people["cell"].eq(cell)]
            for metric in METRICS:
                if metric == "mbf_author_composite" and memory == "No Memory":
                    continue
                rows.append({"sample": sample, "cell": cell, "metric": metric,
                             "participants_python": int(len(observations)),
                             "estimate_python": float(observations[metric].mean()),
                             "sd_python": float(observations[metric].std(ddof=1))})
    return pd.DataFrame(rows)


def named_contrasts(samples):
    # Standardize both populations to the predeclared full-sample memory mix.
    full_weights = (samples["all_516"]["Memory_Type"].value_counts(normalize=True)
                    .reindex(MEMORIES).to_dict())
    rows = []
    for sample, people in samples.items():
        for metric in METRICS:
            group_means = people.groupby(["Memory_Type", "Control_Interface"])[metric].mean()
            dashboard_difference = {
                memory: float(group_means.loc[(memory, CONTROLS[1])] -
                              group_means.loc[(memory, CONTROLS[0])])
                for memory in MEMORIES
            }
            if metric == "mbf_author_composite":
                definitions = {
                    "dashboard_with_relevant": dashboard_difference["Relevant Memory"],
                    "dashboard_with_intrusive": dashboard_difference["Intrusive Memory"],
                }
            else:
                none, relevant, intrusive = MEMORIES
                no, dash = CONTROLS
                definitions = {
                    "primary_intrusive_gap_change":
                        dashboard_difference[intrusive] - dashboard_difference[none],
                    "dashboard_average_standardized":
                        sum(full_weights[memory] * dashboard_difference[memory]
                            for memory in MEMORIES),
                    "dashboard_with_no_memory": dashboard_difference[none],
                    "dashboard_with_relevant": dashboard_difference[relevant],
                    "dashboard_with_intrusive": dashboard_difference[intrusive],
                    "relevant_gap_change":
                        dashboard_difference[relevant] - dashboard_difference[none],
                    "intrusive_penalty_no_dashboard":
                        float(group_means.loc[(none, no)] - group_means.loc[(intrusive, no)]),
                    "intrusive_penalty_dashboard":
                        float(group_means.loc[(none, dash)] - group_means.loc[(intrusive, dash)]),
                    "relevant_vs_none_no_dashboard":
                        float(group_means.loc[(relevant, no)] - group_means.loc[(none, no)]),
                    "relevant_vs_none_dashboard":
                        float(group_means.loc[(relevant, dash)] - group_means.loc[(none, dash)]),
                }
            for name, estimate in definitions.items():
                rows.append({"sample": sample, "contrast": name, "metric": metric,
                             "estimate_python": estimate,
                             "primary_python": bool(sample == "all_516" and
                                 metric == "trust_mean" and
                                 name == "primary_intrusive_gap_change")})
    return pd.DataFrame(rows), {key: float(value) for key, value in full_weights.items()}


def regression_checks(samples):
    coefficients, fits = [], []
    for sample, people in samples.items():
        design = pd.DataFrame(index=people.index)
        design[TERMS[0]] = 1.0
        design[TERMS[1]] = people["Memory_Type"].eq("Relevant Memory").astype(float)
        design[TERMS[2]] = people["Memory_Type"].eq("Intrusive Memory").astype(float)
        design[TERMS[3]] = people["Control_Interface"].eq("Editable Dashboard").astype(float)
        design[TERMS[4]] = design[TERMS[1]] * design[TERMS[3]]
        design[TERMS[5]] = design[TERMS[2]] * design[TERMS[3]]
        outcome = people["trust_mean"].to_numpy(dtype=float)
        matrix = design.to_numpy(dtype=float)
        beta, _, rank, _ = np.linalg.lstsq(matrix, outcome, rcond=None)
        additive = matrix[:, :4]
        reduced_beta, _, reduced_rank, _ = np.linalg.lstsq(additive, outcome, rcond=None)
        require(rank == 6 and reduced_rank == 4, "Invalid nested-model ranks.")
        residual = outcome - matrix @ beta
        reduced_residual = outcome - additive @ reduced_beta
        full_sse = float(np.dot(residual, residual))
        reduced_sse = float(np.dot(reduced_residual, reduced_residual))
        residual_df = len(people) - rank
        numerator_df = rank - reduced_rank
        f_value = ((reduced_sse - full_sse) / numerator_df) / (full_sse / residual_df)
        require(f_value >= -TOLERANCE, "Nested residual sums are inconsistent.")
        f_value = max(0.0, f_value)
        # For F(2, nu), the upper tail has this exact closed form.
        # This independently avoids MATLAB betainc and requires no scipy.
        probability = math.exp(-0.5 * residual_df * math.log1p(2 * f_value / residual_df))
        fits.append({"sample": sample, "participants_python": int(len(people)),
                     "full_sse_python": full_sse, "reduced_sse_python": reduced_sse,
                     "residual_df_python": int(residual_df), "numerator_df": int(numerator_df),
                     "interaction_F_2df_python": f_value, "interaction_p_python": probability})
        coefficients.extend({"sample": sample, "term": term,
                             "coefficient_python": float(value)}
                            for term, value in zip(TERMS, beta))
    return pd.DataFrame(coefficients), pd.DataFrame(fits)


def item_frequencies(samples):
    rows = []
    for sample, people in samples.items():
        for cell in CELLS.values():
            selected = people.loc[people["cell"].eq(cell)]
            for index, item in enumerate(ITEMS, 1):
                counts = selected[item].value_counts().reindex(range(1, 8), fill_value=0)
                rows.extend({"sample": sample, "cell": cell,
                             "item": f"trust_item{index}", "value": int(value),
                             "participants_python": int(count)}
                            for value, count in counts.items())
    return pd.DataFrame(rows)


def source_summary(full):
    rows = []
    for label, level, author_mean, author_sd in [
        ("dashboard", "Editable Dashboard", 4.49, 0.91),
        ("no_control", "No Control", 4.30, 1.00),
    ]:
        values = full.loc[full["Control_Interface"].eq(level), "trust_mean"]
        rows.append({"condition": label, "participants_python": int(len(values)),
                     "computed_mean_python": float(values.mean()),
                     "computed_sd_python": float(values.std(ddof=1)),
                     "article_mean_expected": author_mean, "article_sd_expected": author_sd,
                     "raw_mean_rounds_to_article": round(float(values.mean()), 2) == author_mean,
                     "raw_sd_rounds_to_article": round(float(values.std(ddof=1)), 2) == author_sd})
    return pd.DataFrame(rows)


def validate(source_file, results):
    samples, identity, integrity = load_source(source_file, results)
    points = cell_estimates(samples)
    cells = match_tables(points, read_csv(results / "cell_estimates.csv",
        ["sample", "cell", "metric", "participants", "estimate", "sd"], "cell estimates"),
        ["sample", "cell", "metric"], 56, "cell estimates")
    cell_checks = numeric_comparison(cells, ["participants", "estimate", "sd"])

    comparisons, weights = named_contrasts(samples)
    contrasts = match_tables(comparisons, read_csv(results / "contrasts.csv",
        ["sample", "contrast", "metric", "estimate", "primary_in_full_sample"], "contrasts"),
        ["sample", "contrast", "metric"], 84, "contrasts")
    contrast_checks = numeric_comparison(contrasts, ["estimate"])
    flags = contrasts["primary_in_full_sample"].astype(str).str.lower().map(
        {"true": True, "false": False})
    primary_flags_match = bool(flags.notna().all() and flags.eq(contrasts["primary_python"]).all())

    coefficients, models = regression_checks(samples)
    coefficients = match_tables(coefficients, read_csv(results / "ols_coefficients.csv",
        ["sample", "term", "coefficient"], "OLS coefficients"),
        ["sample", "term"], 12, "OLS coefficients")
    coefficient_checks = numeric_comparison(coefficients, ["coefficient"])
    models = match_tables(models, read_csv(results / "model_checks.csv",
        ["sample", "participants", "full_sse", "residual_df", "interaction_F_2df", "interaction_p"],
        "nested model checks"), ["sample"], 2, "nested model checks")
    model_checks = numeric_comparison(models,
        ["participants", "full_sse", "residual_df", "interaction_F_2df", "interaction_p"])

    frequencies = match_tables(item_frequencies(samples),
        read_csv(results / "trust_item_frequencies.csv",
            ["sample", "cell", "item", "value", "participants"], "item frequencies"),
        ["sample", "cell", "item", "value"], 252, "item frequencies")
    frequency_checks = numeric_comparison(frequencies, ["participants"])

    summary = match_tables(source_summary(samples["all_516"]),
        read_csv(results / "source_summary_comparison.csv",
            ["condition", "participants", "computed_mean", "computed_sd",
             "article_mean_rounded", "article_sd_rounded"], "source summary"),
        ["condition"], 2, "source summary")
    source_checks = numeric_comparison(summary, ["participants", "computed_mean", "computed_sd"])
    source_rounding_ok = bool(summary["raw_mean_rounds_to_article"].all() and
        summary["raw_sd_rounds_to_article"].all() and
        summary["article_mean_expected"].eq(summary["article_mean_rounded"]).all() and
        summary["article_sd_expected"].eq(summary["article_sd_rounded"]).all())

    def export(frame):
        return frame.drop(columns=["_merge"], errors="ignore").to_dict(orient="records")

    report = {
        "date": datetime.now(timezone.utc).date().isoformat(),
        "validator": "Independent original-CSV pandas/numpy computation; no MATLAB intermediates",
        "versions": {"pandas": pd.__version__, "numpy": np.__version__},
        "absolute_tolerance": TOLERANCE,
        "input_identity": identity, "source_integrity": integrity,
        "cell_estimates": {"rows_checked": 56, "checks": cell_checks, "comparisons": export(cells)},
        "contrasts": {"rows_checked": 84, "checks": contrast_checks,
                      "primary_flags_match": primary_flags_match,
                      "full_sample_memory_weights_used_for_both_samples": weights,
                      "comparisons": export(contrasts)},
        "ols_coefficients": {"rows_checked": 12, "checks": coefficient_checks,
                             "comparisons": export(coefficients)},
        "nested_interaction_models": {"rows_checked": 2, "checks": model_checks,
            "p_method": "F(2, nu) survival = exp[-nu/2 * log1p(2F/nu)]; no scipy",
            "comparisons": export(models)},
        "trust_item_frequencies": {"rows_checked": 252, "checks": frequency_checks},
        "source_summary": {"rows_checked": 2, "checks": source_checks,
                           "article_rounded_values_match": source_rounding_ok,
                           "comparisons": export(summary)},
        "not_checked": [
            "No bootstrap replicate or confidence-bound recomputation.",
            "No reconstruction of unpublished MBF items or source-author models.",
            "No audit of screening logs, session dependence, or actual randomization execution.",
            "No test of budget revision, reason withdrawal, interface use, or normative autonomy.",
        ],
        "participant_values_exported": False,
    }
    all_check_groups = [cell_checks, contrast_checks, coefficient_checks, model_checks,
                        frequency_checks, source_checks]
    report["within_scope_pass"] = bool(identity["matches_fixed_source"] and
        all(check["all_match"] for group in all_check_groups for check in group.values()) and
        primary_flags_match and source_rounding_ok)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Fixed original Study 4 CSV.")
    parser.add_argument("--results", type=Path, required=True, help="Aggregate result CSV directory.")
    parser.add_argument("--output", type=Path, help="Optional aggregate validation JSON destination.")
    args = parser.parse_args()
    try:
        report = validate(args.source, args.results)
        payload = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)
        destination = args.output or (args.results.parent / "validation" / "独立复算.json")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(payload, encoding="utf-8")
    except ValidationError as exc:
        print(f"Validation error: {exc}", file=sys.stderr)
        return 2
    except Exception:
        print("Validation failed; no paths or participant records are reported.", file=sys.stderr)
        return 2
    print(json.dumps({"within_scope_pass": report["within_scope_pass"],
                      "cell_estimates_checked": 56, "contrasts_checked": 84,
                      "ols_coefficients_checked": 12, "interaction_tests_checked": 2,
                      "item_frequency_cells_checked": 252,
                      "source_summary_groups_checked": 2, "bootstrap_rerun": False}))
    return 0 if report["within_scope_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

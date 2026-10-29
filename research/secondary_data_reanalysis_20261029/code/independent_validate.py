#!/usr/bin/env python3
"""Validate observed-data aggregates independently of MATLAB.

Requires pandas. No bootstrap, model estimation, or individual-record export.
The data root is the original replication folder containing data_for_cbc_est.
Only aggregate statistics and source-file hashes are written. Local paths and
platform participant identifiers are never included in the report or errors.

Usage:
    python independent_validate.py --data-root ORIGINAL_REPLICATION --results RESULTS

The optional --output selects a JSON report. The default is a new
validation/独立复算_脚本复核.json next to the results directory; existing numerical
result CSVs and the earlier 独立复算.json are not modified.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd


ARMS = [
    "regular_control", "regular_regulator", "treat_control", "treat_regulator"
]
METRICS = [
    "ingredient_choice_share", "no_purchase_share",
    "selected_price_unconditional_usd", "pre_harmful_bin_share",
    "post_harmful_bin_share", "belief_lower_share", "belief_same_share",
    "belief_higher_share", "purchase_share",
    "selected_price_purchase_conditional_usd",
]
CONTRASTS = [
    "debunk_with_misinfo", "debunk_with_regular", "misinfo_without_debunk",
    "misinfo_with_debunk", "interaction_debunk_differences",
]
DEM_COLUMNS = ["user", "adtreatment", "debunktreatment", "belieffl", "postbelieffl"]
CHOICE_COLUMNS = [
    "user", "question", "option", "price_numeric", "has_ingredient", "selected"
]
TOLERANCE = 1e-12


class ValidationError(Exception):
    """A validation failure with a path-free message."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def read_required_csv(path: Path, columns: list[str], label: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path, usecols=columns)
    except Exception:
        # Do not propagate parser or operating-system errors containing paths.
        raise ValidationError(f"Cannot read required columns for {label}.") from None


def records(frame: pd.DataFrame, columns: list[str]) -> list[dict]:
    return frame[columns].to_dict(orient="records")


def match_keys(left: pd.DataFrame, right: pd.DataFrame,
               keys: list[str], expected_rows: int, label: str) -> pd.DataFrame:
    try:
        result = left.merge(right, on=keys, how="outer", validate="one_to_one",
                            indicator=True)
    except Exception:
        raise ValidationError(f"Invalid or duplicate keys in {label}.") from None
    require(len(result) == expected_rows and result["_merge"].eq("both").all(),
            f"Incomplete or unexpected result keys in {label}.")
    return result


def source_hashes(source: Path, manifest_path: Path) -> list[dict]:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        known = manifest["hashes"]
        result = []
        for name in ("cleaned_demographics.csv", "cleaned_cbc.csv"):
            suffix = f"/toothpaste_beliefs/{name}"
            expected = next(item["sha256"] for item in known
                            if item["original_relative_path"].endswith(suffix))
            digest = hashlib.sha256((source / name).read_bytes()).hexdigest()
            result.append({
                "file": f"data_for_cbc_est/toothpaste_beliefs/{name}",
                "sha256": digest,
                "matches_recorded_original": digest == expected,
            })
        return result
    except Exception:
        raise ValidationError("Cannot verify source files against the hash manifest.") from None


def load_observations(source: Path):
    dem = read_required_csv(source / "cleaned_demographics.csv", DEM_COLUMNS,
                            "demographic observations")
    cbc = read_required_csv(source / "cleaned_cbc.csv", CHOICE_COLUMNS,
                            "choice observations")
    require(not dem[DEM_COLUMNS].isna().any().any() and
            not cbc[CHOICE_COLUMNS].isna().any().any(),
            "Required observations contain missing fields.")
    dem["arm"] = dem["adtreatment"].str.cat(dem["debunktreatment"], sep="_")
    require(set(dem["arm"]) == set(ARMS), "Unexpected original treatment arms.")
    require(not dem["user"].duplicated().any(), "Duplicate participant key.")
    try:
        choice = cbc.merge(dem[["user", "arm"]], on="user", how="left",
                           validate="many_to_one")
    except Exception:
        raise ValidationError("Cannot match observations by participant.") from None
    selected = choice.loc[choice["selected"].eq(1)].copy()
    checks = {
        "participants": int(len(dem)),
        "distinct_user_keys": int(dem["user"].nunique()),
        "option_rows": int(len(cbc)),
        "selected_tasks": int(len(selected)),
        "no_duplicate_option_keys": not bool(
            cbc.duplicated(["user", "question", "option"]).any()),
        "all_four_options_per_task": bool(
            cbc.groupby(["user", "question"]).size().eq(4).all()),
        "one_selection_per_task": bool(
            cbc.groupby(["user", "question"])["selected"].sum().eq(1).all()),
        "ten_tasks_per_participant": bool(
            cbc.groupby("user")["question"].nunique().eq(10).all()),
        "no_choice_orphan_keys": bool(choice["arm"].notna().all()),
        "selected_binary": bool(cbc["selected"].isin([0, 1]).all()),
        "ingredient_binary": bool(cbc["has_ingredient"].isin([0, 1]).all()),
        "original_option_codes": bool(cbc["option"].isin([1, 2, 3, 4]).all()),
        "belief_categories_complete": bool(
            dem[["belieffl", "postbelieffl"]].isin(range(1, 6)).all().all()),
        "no_purchase_selected_prices_are_zero": bool(
            selected.loc[selected["option"].eq(4), "price_numeric"].eq(0).all()),
        "all_product_prices_in_original_menu": bool(
            cbc.loc[cbc["option"].ne(4), "price_numeric"]
            .isin([0.99, 1.99, 2.99]).all()),
        "arm_counts": {key: int(value) for key, value in
                       dem["arm"].value_counts().sort_index().items()},
        "parsed_demographic_fields": DEM_COLUMNS,
        "parsed_choice_fields": CHOICE_COLUMNS,
    }
    require(len(dem) == 5050 and len(cbc) == 202000,
            "Unexpected source version or sample size.")
    require(all(value for value in checks.values() if isinstance(value, bool)),
            "Source integrity checks failed.")
    return dem, choice, selected, checks


def arm_points(dem: pd.DataFrame, selected: pd.DataFrame) -> pd.DataFrame:
    rows = []
    # Direct observed-task means are participant-equivalent because each has ten.
    for arm in ARMS:
        people = dem.loc[dem["arm"].eq(arm)]
        observed = selected.loc[selected["arm"].eq(arm)]
        purchased = observed.loc[observed["option"].ne(4)]
        require(not purchased.empty, "An arm has no observed purchase tasks.")
        values = {
            "ingredient_choice_share": observed["has_ingredient"].mean(),
            "no_purchase_share": observed["option"].eq(4).mean(),
            "selected_price_unconditional_usd": observed["price_numeric"].mean(),
            "pre_harmful_bin_share": people["belieffl"].isin([4, 5]).mean(),
            "post_harmful_bin_share": people["postbelieffl"].isin([4, 5]).mean(),
            "belief_lower_share": people["postbelieffl"].lt(people["belieffl"]).mean(),
            "belief_same_share": people["postbelieffl"].eq(people["belieffl"]).mean(),
            "belief_higher_share": people["postbelieffl"].gt(people["belieffl"]).mean(),
            "purchase_share": observed["option"].ne(4).mean(),
            "selected_price_purchase_conditional_usd": purchased["price_numeric"].mean(),
        }
        for metric, value in values.items():
            rows.append({"arm": arm, "metric": metric,
                         "participants_python": int(len(people)),
                         "estimate_python": float(value)})
    return pd.DataFrame(rows)


def contrast_points(points: pd.DataFrame) -> pd.DataFrame:
    wide = points.pivot(index="metric", columns="arm", values="estimate_python")
    rows = []
    for metric in METRICS:
        regular_control, regular_regulator, treat_control, treat_regulator = (
            float(wide.loc[metric, arm]) for arm in ARMS)
        definitions = {
            "debunk_with_misinfo": treat_regulator - treat_control,
            "debunk_with_regular": regular_regulator - regular_control,
            "misinfo_without_debunk": treat_control - regular_control,
            "misinfo_with_debunk": treat_regulator - regular_regulator,
            "interaction_debunk_differences":
                (treat_regulator - treat_control) -
                (regular_regulator - regular_control),
        }
        rows.extend({"contrast": name, "metric": metric,
                     "estimate_python": value}
                    for name, value in definitions.items())
    return pd.DataFrame(rows)


def compare_additional(dem: pd.DataFrame, choice: pd.DataFrame,
                       selected: pd.DataFrame, results: Path) -> dict:
    full = pd.MultiIndex.from_product(
        [ARMS, range(1, 6), range(1, 6)],
        names=["arm", "belieffl", "postbelieffl"])
    transitions = (dem.groupby(["arm", "belieffl", "postbelieffl"]).size()
                   .rename("python_count").reindex(full, fill_value=0)
                   .reset_index().rename(columns={"belieffl": "pre_bin",
                                                  "postbelieffl": "post_bin"}))
    reported = read_required_csv(results / "belief_transitions.csv",
                                ["arm", "pre_bin", "post_bin", "participants"],
                                "belief transitions")
    transition_check = match_keys(transitions, reported,
                                 ["arm", "pre_bin", "post_bin"], 100,
                                 "belief transitions")

    by_person = selected.groupby("user")["has_ingredient"].agg(["sum", "size"])
    joint = dem[["user", "arm", "belieffl", "postbelieffl"]].merge(
        by_person, on="user", validate="one_to_one")
    joint["belief_direction"] = "higher"
    joint.loc[joint["postbelieffl"].eq(joint["belieffl"]), "belief_direction"] = "same"
    joint.loc[joint["postbelieffl"].lt(joint["belieffl"]), "belief_direction"] = "lower"
    joint["observed_choice_pattern"] = "mixed"
    joint.loc[joint["sum"].eq(0), "observed_choice_pattern"] = "never_ingredient"
    joint.loc[joint["sum"].eq(joint["size"]),
              "observed_choice_pattern"] = "always_ingredient"
    keys = ["arm", "belief_direction", "observed_choice_pattern"]
    grid = pd.MultiIndex.from_product(
        [ARMS, ["lower", "same", "higher"],
         ["never_ingredient", "mixed", "always_ingredient"]], names=keys)
    joint_counts = (joint.groupby(keys).size().rename("python_count")
                    .reindex(grid, fill_value=0).reset_index())
    reported = read_required_csv(results / "joint_belief_choice.csv",
                                keys + ["participants"], "joint counts")
    joint_check = match_keys(joint_counts, reported, keys, 36, "joint counts")

    menu = (choice.loc[choice["option"].ne(4)].groupby("arm")
            .agg(offered_ingredient_share_python=("has_ingredient", "mean"),
                 offered_price_mean_usd_python=("price_numeric", "mean"))
            .reset_index())
    reported = read_required_csv(results / "offered_menu_balance.csv",
                                ["arm", "offered_ingredient_share",
                                 "offered_price_mean_usd"], "offered menu")
    menu_check = match_keys(menu, reported, ["arm"], 4, "offered menu")
    ingredient_error = (menu_check["offered_ingredient_share_python"] -
                        menu_check["offered_ingredient_share"]).abs()
    price_error = (menu_check["offered_price_mean_usd_python"] -
                   menu_check["offered_price_mean_usd"]).abs()
    return {
        "belief_transitions": {"rows_checked": 100, "keys_complete": True,
            "all_counts_match": bool(transition_check["python_count"]
                                     .eq(transition_check["participants"]).all())},
        "joint_belief_choice": {"rows_checked": 36, "keys_complete": True,
            "all_counts_match": bool(joint_check["python_count"]
                                     .eq(joint_check["participants"]).all())},
        "offered_menu_balance": {"rows_checked": 4, "keys_complete": True,
            "max_ingredient_absolute_error": float(ingredient_error.max()),
            "max_price_absolute_error": float(price_error.max())},
    }


def validate(data_root: Path, results: Path) -> dict:
    source = data_root / "data_for_cbc_est" / "toothpaste_beliefs"
    identities = source_hashes(source, results.parent / "来源与原件哈希.json")
    dem, choice, selected, integrity = load_observations(source)
    points = arm_points(dem, selected)
    reported = read_required_csv(results / "arm_estimates.csv",
                                ["arm", "metric", "participants", "estimate"],
                                "arm estimates")
    arms = match_keys(points, reported, ["arm", "metric"], 40, "arm estimates")
    arms["absolute_error"] = (arms["estimate_python"] - arms["estimate"]).abs()
    arms["participants_match"] = arms["participants_python"].eq(arms["participants"])
    arms["point_match"] = arms["absolute_error"].lt(TOLERANCE)
    contrasts = contrast_points(points)
    reported = read_required_csv(results / "contrasts.csv",
                                ["contrast", "metric", "estimate"], "contrasts")
    diffs = match_keys(contrasts, reported, ["contrast", "metric"], 50, "contrasts")
    diffs["absolute_error"] = (diffs["estimate_python"] - diffs["estimate"]).abs()
    diffs["point_match"] = diffs["absolute_error"].lt(TOLERANCE)
    additional = compare_additional(dem, choice, selected, results)
    report = {
        "date": datetime.now(timezone.utc).date().isoformat(),
        "review_kind": "Independent pandas point-estimate and aggregate-count validation; no bootstrap rerun",
        "python_pandas_version": pd.__version__,
        "absolute_tolerance": TOLERANCE,
        "input_identity": identities,
        "source_integrity_checks": integrity,
        "arm_estimates": {
            "rows_checked": 40, "keys_complete": True,
            "all_point_estimates_match": bool(arms["point_match"].all()),
            "all_participant_counts_match": bool(arms["participants_match"].all()),
            "max_absolute_error": float(arms["absolute_error"].max()),
            "comparisons": records(arms, ["arm", "metric", "participants_python",
                "participants", "estimate_python", "estimate", "absolute_error",
                "participants_match", "point_match"]),
        },
        "contrasts": {
            "rows_checked": 50, "keys_complete": True,
            "all_point_estimates_match": bool(diffs["point_match"].all()),
            "max_absolute_error": float(diffs["absolute_error"].max()),
            "comparisons": records(diffs, ["contrast", "metric", "estimate_python",
                "estimate", "absolute_error", "point_match"]),
        },
        "additional_tables": additional,
        "not_checked": [
            "Bootstrap replicate values and confidence bounds were not independently rerun.",
            "Random-assignment implementation, payouts, and complete recruitment/exclusion logs were not audited.",
            "Original conditional-logit WTP and equilibrium models were not estimated.",
            "AI shopping, budget revisions, autonomy, and unobserved R-by-C interventions were not tested.",
        ],
        "raw_identifier_values_exported": False,
        "methodology_notes": {
            "post_belief_timing": "Posterior beliefs follow assigned messages and conjoint choices; no mediation claim.",
            "analysis_population": "5050 participants in the public cleaned toothpaste_beliefs files; not certified as complete intention-to-treat.",
            "resampling_scope": "Only MATLAB indexing was reviewed previously; this script does not resample observations.",
        },
    }
    report["within_scope_pass"] = all([
        all(item["matches_recorded_original"] for item in identities),
        report["arm_estimates"]["all_point_estimates_match"],
        report["arm_estimates"]["all_participant_counts_match"],
        report["contrasts"]["all_point_estimates_match"],
        additional["belief_transitions"]["all_counts_match"],
        additional["joint_belief_choice"]["all_counts_match"],
        additional["offered_menu_balance"]["max_ingredient_absolute_error"] < TOLERANCE,
        additional["offered_menu_balance"]["max_price_absolute_error"] < TOLERANCE,
    ])
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path,
                        help="Original replication folder containing data_for_cbc_est.")
    parser.add_argument("--results", required=True, type=Path,
                        help="Directory containing the MATLAB aggregate result CSVs.")
    parser.add_argument("--output", type=Path,
                        help="Optional JSON destination; local paths are not recorded.")
    args = parser.parse_args()
    try:
        report = validate(args.data_root, args.results)
        output = args.output or (args.results.parent / "validation" /
                                 "独立复算_脚本复核.json")
        payload = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    except ValidationError as exc:
        print(f"Validation error: {exc}", file=sys.stderr)
        return 2
    except Exception:
        print("Validation failed; no local paths or individual records are reported.",
              file=sys.stderr)
        return 2
    print(json.dumps({
        "within_scope_pass": report["within_scope_pass"],
        "arm_estimates_checked": 40, "contrasts_checked": 50,
        "additional_count_rows_checked": 136, "menu_arms_checked": 4,
        "bootstrap_rerun": False,
    }))
    return 0 if report["within_scope_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path
from collections import Counter


WORD_RE = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]*")


def words(text: str) -> set[str]:
    return {w.lower() for w in WORD_RE.findall(text)}


def load_cases(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_description(text: str) -> str:
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return text
    frontmatter = parts[1].splitlines()
    for line in frontmatter:
        if line.strip().startswith("description:"):
            return line.split(":", 1)[1].strip().strip("'\"")
    return text


def score_prompt(description_words: set[str], prompt: str) -> float:
    prompt_words = words(prompt)
    if not prompt_words:
        return 0.0
    overlap = description_words & prompt_words
    return len(overlap) / len(prompt_words)


def token_frequencies(cases: dict, buckets: tuple[str, ...]) -> Counter:
    freq: Counter = Counter()
    for bucket in buckets:
        for prompt in cases.get(bucket, []):
            freq.update(words(prompt))
    return freq


def compile_negative_patterns(cases: dict) -> list[re.Pattern[str]]:
    return [re.compile(pattern, re.IGNORECASE) for pattern in cases.get("negative_patterns", [])]


def score_prompt_weighted(description_words: set[str], prompt: str, positive_freq: Counter, negative_freq: Counter, negative_patterns: list[re.Pattern[str]]) -> tuple[float, dict]:
    prompt_words = words(prompt)
    if not prompt_words:
        return 0.0, {"matched_positive_tokens": [], "matched_negative_tokens": [], "matched_negative_patterns": []}

    overlap = description_words & prompt_words
    base_score = len(overlap) / len(prompt_words)

    weighted_bonus = 0.0
    matched_positive_tokens = []
    matched_negative_tokens = []
    for token in overlap:
        pos = positive_freq.get(token, 0)
        neg = negative_freq.get(token, 0)
        if pos > neg:
            weighted_bonus += 0.06
            matched_positive_tokens.append(token)

    weighted_penalty = 0.0
    for token in prompt_words:
        neg = negative_freq.get(token, 0)
        pos = positive_freq.get(token, 0)
        if neg > pos and token not in overlap:
            weighted_penalty += 0.04
            matched_negative_tokens.append(token)

    matched_negative_patterns = [pattern.pattern for pattern in negative_patterns if pattern.search(prompt)]
    pattern_penalty = 0.18 * len(matched_negative_patterns)

    score = max(0.0, min(1.0, base_score + weighted_bonus - weighted_penalty - pattern_penalty))
    return score, {
        "matched_positive_tokens": sorted(set(matched_positive_tokens)),
        "matched_negative_tokens": sorted(set(matched_negative_tokens)),
        "matched_negative_patterns": matched_negative_patterns,
        "base_score": round(base_score, 3),
        "weighted_bonus": round(weighted_bonus, 3),
        "weighted_penalty": round(weighted_penalty + pattern_penalty, 3),
    }


def classify_bucket(bucket: str) -> bool:
    return bucket == "should_trigger"


def evaluate(description: str, cases: dict, threshold: float) -> dict:
    desc_words = words(description)
    positive_freq = token_frequencies(cases, ("should_trigger",))
    negative_freq = token_frequencies(cases, ("should_not_trigger", "near_neighbor"))
    negative_patterns = compile_negative_patterns(cases)
    results = {"should_trigger": [], "should_not_trigger": [], "near_neighbor": []}
    fp = 0
    fn = 0
    bucket_stats = {}
    misfires = []

    for bucket in ("should_trigger", "should_not_trigger", "near_neighbor"):
        expected = classify_bucket(bucket)
        total = 0
        passed_count = 0
        for prompt in cases.get(bucket, []):
            score, score_detail = score_prompt_weighted(desc_words, prompt, positive_freq, negative_freq, negative_patterns)
            predicted = score >= threshold
            passed = predicted == expected
            total += 1
            if passed:
                passed_count += 1
            if not passed and expected:
                fn += 1
            if not passed and not expected:
                fp += 1
            record = {
                "prompt": prompt,
                "score": round(score, 3),
                "predicted_trigger": predicted,
                "expected_trigger": expected,
                "passed": passed,
                "score_detail": score_detail,
            }
            if 0.75 * threshold <= score <= 1.25 * threshold:
                record["boundary_case"] = True
            results[bucket].append(record)
            if not passed:
                misfires.append(
                    {
                        "bucket": bucket,
                        "prompt": prompt,
                        "score": round(score, 3),
                        "reason": "false_negative" if expected else "false_positive",
                        "matched_negative_patterns": score_detail["matched_negative_patterns"],
                    }
                )
        bucket_stats[bucket] = {
            "total": total,
            "passed": passed_count,
            "pass_rate": round(passed_count / total, 3) if total else None,
        }

    tp = sum(1 for item in results["should_trigger"] if item["predicted_trigger"])
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None

    return {
        "threshold": threshold,
        "threshold_explanation": "Prompts at or above the threshold are treated as trigger matches. Final scores combine token overlap, positive-token bonuses, negative-token penalties, and explicit negative-pattern penalties. Scores near the threshold should be reviewed as boundary cases.",
        "false_positives": fp,
        "false_negatives": fn,
        "precision": round(precision, 3) if precision is not None else None,
        "recall": round(recall, 3) if recall is not None else None,
        "bucket_stats": bucket_stats,
        "misfires": misfires,
        "results": results,
    }


def compare_reports(baseline: dict, improved: dict) -> dict:
    return {
        "baseline_false_positives": baseline["false_positives"],
        "baseline_false_negatives": baseline["false_negatives"],
        "improved_false_positives": improved["false_positives"],
        "improved_false_negatives": improved["false_negatives"],
        "false_positive_delta": improved["false_positives"] - baseline["false_positives"],
        "false_negative_delta": improved["false_negatives"] - baseline["false_negatives"],
        "baseline_precision": baseline["precision"],
        "improved_precision": improved["precision"],
        "baseline_recall": baseline["recall"],
        "improved_recall": improved["recall"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Heuristic trigger quality evaluator.")
    parser.add_argument("--description", help="Description string to evaluate")
    parser.add_argument("--description-file", help="Read description text from file")
    parser.add_argument("--baseline-description", help="Baseline description string to compare against")
    parser.add_argument("--baseline-description-file", help="Read baseline description from file")
    parser.add_argument("--cases", required=True, help="JSON file with should_trigger and should_not_trigger arrays")
    parser.add_argument("--threshold", type=float, default=None, help="Trigger threshold override")
    args = parser.parse_args()

    description = args.description
    if args.description_file:
        description = extract_description(Path(args.description_file).read_text(encoding="utf-8"))
    if not description:
        raise SystemExit("Provide --description or --description-file")

    cases = load_cases(Path(args.cases))
    threshold = args.threshold if args.threshold is not None else cases.get("recommended_threshold", 0.35)
    report = evaluate(description, cases, threshold)

    baseline = args.baseline_description
    if args.baseline_description_file:
        baseline = extract_description(Path(args.baseline_description_file).read_text(encoding="utf-8"))
    if baseline:
        report["comparison"] = compare_reports(evaluate(baseline, cases, threshold), report)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["false_positives"] > 2:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


WORD_RE = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)
DEFAULT_CONFIG_PATH = Path("evals/semantic_config.json")


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\u4e00-\u9fff]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def words(text: str) -> set[str]:
    return {w.lower() for w in WORD_RE.findall(text)}


def load_json(path: Path) -> dict:
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


def iter_case_items(cases: dict, bucket: str) -> list[dict]:
    items = []
    for raw in cases.get(bucket, []):
        if isinstance(raw, str):
            items.append({"text": raw, "family": "default"})
        else:
            item = dict(raw)
            item.setdefault("family", "default")
            items.append(item)
    return items


def phrase_present(text: str, phrase: str) -> bool:
    phrase = normalize(phrase)
    if not phrase:
        return False
    if re.search(r"[\u4e00-\u9fff]", phrase):
        return phrase in text
    return f" {phrase} " in f" {text} "


def load_semantic_config(path: Path | None) -> dict:
    config_path = path or DEFAULT_CONFIG_PATH
    if not config_path.exists():
        raise SystemExit(f"Semantic config not found: {config_path}")
    return load_json(config_path)


def collect_concept_hits(text: str, concepts: dict[str, dict]) -> dict[str, dict]:
    normalized = normalize(text)
    hits: dict[str, dict] = {}
    for name, spec in concepts.items():
        matched = []
        for phrase in spec.get("phrases", []):
            if phrase_present(normalized, phrase):
                matched.append(phrase)
        if matched:
            hits[name] = {
                "weight": spec["weight"],
                "matched_phrases": matched,
                "exclusive": bool(spec.get("exclusive")),
            }
    return hits


def lexical_support(description_words: set[str], prompt: str) -> float:
    prompt_words = words(prompt)
    if not prompt_words:
        return 0.0
    return len(description_words & prompt_words) / len(prompt_words)


def desired_positive_concepts(description: str, config: dict) -> list[str]:
    description_hits = collect_concept_hits(description, config["positive_concepts"])
    names = list(description_hits)
    if names:
        return names
    return config.get("fallback_positive_concepts", [])


def score_prompt_semantic(description: str, prompt: str, config: dict) -> tuple[float, dict]:
    positive_concepts = config["positive_concepts"]
    negative_concepts = config["negative_concepts"]
    desired = desired_positive_concepts(description, config)
    desired_weight_total = sum(positive_concepts[name]["weight"] for name in desired) or 1.0

    prompt_positive_hits = collect_concept_hits(prompt, positive_concepts)
    prompt_negative_hits = collect_concept_hits(prompt, negative_concepts)

    matched_desired = sorted([name for name in desired if name in prompt_positive_hits])
    extra_positive = sorted([name for name in prompt_positive_hits if name not in matched_desired])
    semantic_coverage = sum(positive_concepts[name]["weight"] for name in matched_desired) / desired_weight_total
    support_score = sum(positive_concepts[name]["weight"] for name in extra_positive)

    exclusive_negative = sorted([name for name, hit in prompt_negative_hits.items() if hit["exclusive"]])
    negative_penalty = sum(hit["weight"] for hit in prompt_negative_hits.values())
    lexical = lexical_support(words(description), prompt)

    coverage_boost = 0.0
    if len(matched_desired) >= 2:
        coverage_boost += 0.04
    if len(matched_desired) >= 3:
        coverage_boost += 0.02

    score = (semantic_coverage * 0.92) + min(0.12, support_score * 0.25) + min(0.06, lexical * 0.08) + coverage_boost
    score -= negative_penalty
    if exclusive_negative and semantic_coverage < 0.9:
        score -= 0.15
    score = max(0.0, min(1.0, score))

    score_detail = {
        "mode": "semantic-intent",
        "desired_positive_concepts": desired,
        "matched_desired_concepts": matched_desired,
        "extra_positive_concepts": extra_positive,
        "matched_negative_concepts": sorted(prompt_negative_hits),
        "exclusive_negative_concepts": exclusive_negative,
        "semantic_coverage": round(semantic_coverage, 3),
        "support_score": round(support_score, 3),
        "lexical_support": round(lexical, 3),
        "negative_penalty": round(negative_penalty, 3),
        "coverage_boost": round(coverage_boost, 3),
        "concept_evidence": {
            "positive": {
                name: prompt_positive_hits[name]["matched_phrases"]
                for name in sorted(prompt_positive_hits)
            },
            "negative": {
                name: prompt_negative_hits[name]["matched_phrases"]
                for name in sorted(prompt_negative_hits)
            },
        },
    }
    return score, score_detail


def classify_bucket(bucket: str) -> bool:
    return bucket == "should_trigger"


def evaluate(description: str, cases: dict, threshold: float, config: dict) -> dict:
    results = {"should_trigger": [], "should_not_trigger": [], "near_neighbor": []}
    fp = 0
    fn = 0
    bucket_stats = {}
    family_stats: dict[str, dict] = {}
    misfires = []

    for bucket in ("should_trigger", "should_not_trigger", "near_neighbor"):
        expected = classify_bucket(bucket)
        items = iter_case_items(cases, bucket)
        total = 0
        passed_count = 0
        for item in items:
            prompt = item["text"]
            family = item.get("family", "default")
            score, score_detail = score_prompt_semantic(description, prompt, config)
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
                "family": family,
                "score": round(score, 3),
                "predicted_trigger": predicted,
                "expected_trigger": expected,
                "passed": passed,
                "score_detail": score_detail,
            }
            if 0.75 * threshold <= score <= 1.25 * threshold:
                record["boundary_case"] = True
            results[bucket].append(record)

            family_bucket = family_stats.setdefault(
                family,
                {"total": 0, "passed": 0, "false_positives": 0, "false_negatives": 0},
            )
            family_bucket["total"] += 1
            if passed:
                family_bucket["passed"] += 1
            elif expected:
                family_bucket["false_negatives"] += 1
            else:
                family_bucket["false_positives"] += 1

            if not passed:
                misfires.append(
                    {
                        "bucket": bucket,
                        "family": family,
                        "prompt": prompt,
                        "score": round(score, 3),
                        "reason": "false_negative" if expected else "false_positive",
                        "matched_desired_concepts": score_detail["matched_desired_concepts"],
                        "matched_negative_concepts": score_detail["matched_negative_concepts"],
                    }
                )

        bucket_stats[bucket] = {
            "total": total,
            "passed": passed_count,
            "pass_rate": round(passed_count / total, 3) if total else None,
        }

    for family, stats in family_stats.items():
        stats["pass_rate"] = round(stats["passed"] / stats["total"], 3) if stats["total"] else None

    tp = sum(1 for item in results["should_trigger"] if item["predicted_trigger"])
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None

    return {
        "threshold": threshold,
        "threshold_explanation": (
            "Prompts at or above the threshold are treated as trigger matches. "
            "Scores are driven primarily by semantic intent coverage: packaging intent, "
            "workflow-to-skill transformation intent, reuse/distribution intent, and eval intent. "
            "Explicit exclusions such as summary-only, translation-only, one-off, document-only, "
            "or do-not-build directives apply direct penalties and can override otherwise similar wording."
        ),
        "false_positives": fp,
        "false_negatives": fn,
        "precision": round(precision, 3) if precision is not None else None,
        "recall": round(recall, 3) if recall is not None else None,
        "bucket_stats": bucket_stats,
        "family_stats": family_stats,
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
    parser = argparse.ArgumentParser(description="Semantic trigger quality evaluator.")
    parser.add_argument("--description", help="Description string to evaluate")
    parser.add_argument("--description-file", help="Read description text from file")
    parser.add_argument("--baseline-description", help="Baseline description string to compare against")
    parser.add_argument("--baseline-description-file", help="Read baseline description from file")
    parser.add_argument("--cases", required=True, help="JSON file with trigger cases")
    parser.add_argument("--semantic-config", default=str(DEFAULT_CONFIG_PATH), help="Semantic config JSON")
    parser.add_argument("--threshold", type=float, default=None, help="Trigger threshold override")
    args = parser.parse_args()

    description = args.description
    if args.description_file:
        description = extract_description(Path(args.description_file).read_text(encoding="utf-8"))
    if not description:
        raise SystemExit("Provide --description or --description-file")

    cases = load_json(Path(args.cases))
    config = load_semantic_config(Path(args.semantic_config))
    threshold = args.threshold if args.threshold is not None else cases.get("recommended_threshold", 0.48)
    report = evaluate(description, cases, threshold, config)

    baseline = args.baseline_description
    if args.baseline_description_file:
        baseline = extract_description(Path(args.baseline_description_file).read_text(encoding="utf-8"))
    if baseline:
        report["comparison"] = compare_reports(evaluate(baseline, cases, threshold, config), report)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["false_positives"] > 0 or report["false_negatives"] > 0:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.evaluation import run_rag_search_evaluation


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local RAG retrieval evaluation without calling DeepSeek.")
    parser.add_argument("--dataset", default="data/eval/rag_eval_cases.json")
    parser.add_argument("--output-json", default="data/eval/latest_rag_evaluation.json")
    parser.add_argument("--output-md", default="data/eval/latest_rag_evaluation.md")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--score-threshold", type=float, default=None)
    args = parser.parse_args()

    result = run_rag_search_evaluation(
        settings=get_settings(),
        dataset_path=Path(args.dataset),
        output_json_path=Path(args.output_json),
        output_md_path=Path(args.output_md),
        limit=args.limit,
        score_threshold=args.score_threshold,
    )
    print(
        "RAG evaluation complete: "
        f"hit_rate={result['hit_rate']:.4f}, "
        f"page_hit_rate={result['page_hit_rate']:.4f}, "
        f"keyword_hit_rate={result['keyword_hit_rate']:.4f}"
    )


if __name__ == "__main__":
    main()

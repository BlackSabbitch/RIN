from __future__ import annotations

import argparse
from typing import Literal

from core import (
    MODEL,
    RIN_SYSTEM_PROMPT,
    TEST_CATEGORIES,
    TestCase,
    TestCategory,
    append_event,
    new_session_id,
)
from runtime import ask_model, make_messages


TestRunMode = Literal["raw", "guided", "both"]
ConcreteTestMode = Literal["raw", "guided"]


def expand_modes(mode: TestRunMode) -> list[ConcreteTestMode]:
    if mode == "both":
        return ["raw", "guided"]

    return [mode]


def build_test_prompt(case: TestCase, mode: ConcreteTestMode) -> str:
    if mode == "raw" or not case.guidance:
        return case.user_prompt

    return (
        f"{case.user_prompt}\n\n"
        "Test guidance for Rin. This guidance is not part of the field user message; "
        "it is an evaluation instruction for this test run:\n"
        f"{case.guidance}"
    )


def get_category(category_key: str) -> TestCategory:
    try:
        return TEST_CATEGORIES[category_key]
    except KeyError as error:
        available = ", ".join(TEST_CATEGORIES)
        raise ValueError(
            f"Unknown category: {category_key}. Available categories: {available}"
        ) from error


def resolve_categories(category_key: str | None) -> list[tuple[str, TestCategory]]:
    if category_key is None:
        return list(TEST_CATEGORIES.items())

    return [(category_key, get_category(category_key))]


def list_categories() -> None:
    print("Available categories:")

    for key, category in TEST_CATEGORIES.items():
        print(f"  {category.number}. {category.name}  [{key}]")


def list_tests(category_key: str | None = None) -> None:
    categories = resolve_categories(category_key)

    for key, category in categories:
        print()
        print(f"Category: {category.number}. {category.name} [{key}]")

        for case in category.cases:
            print(f"  Question: {case.number}")


def print_test_header(
    category: TestCategory,
    question_number: int,
    mode: ConcreteTestMode,
) -> None:
    print()
    print("=" * 80)
    print(f"Category: {category.number}. {category.name}")
    print(f"Question: {question_number}")
    print(f"Mode: {mode}")
    print("-" * 80)


def print_test_prompt(
    case: TestCase,
    final_prompt: str,
    *,
    mode: ConcreteTestMode,
    show_final_prompt: bool,
) -> None:
    print("User prompt:")
    print(case.user_prompt)
    print()

    if mode == "guided":
        print("Guidance:")
        print(case.guidance or "<empty>")
        print()

    if show_final_prompt:
        print("Final prompt sent to model:")
        print(final_prompt)
        print()


def select_cases(
    category: TestCategory,
    question_number: int | None,
) -> list[TestCase]:
    if question_number is None:
        return category.cases

    selected = [case for case in category.cases if case.number == question_number]

    if not selected:
        available = ", ".join(str(case.number) for case in category.cases)
        raise ValueError(
            f"Question {question_number} is not found in category "
            f"{category.name}. Available: {available}"
        )

    return selected


def run_single_test(
    *,
    model: str,
    session_id: str,
    category_key: str,
    category: TestCategory,
    case: TestCase,
    mode: ConcreteTestMode,
    show_final_prompt: bool = False,
    num_predict: int | None = None,
) -> None:
    final_prompt = build_test_prompt(case, mode)
    messages = make_messages(RIN_SYSTEM_PROMPT, final_prompt)

    print_test_header(category, case.number, mode)
    print_test_prompt(
        case,
        final_prompt,
        mode=mode,
        show_final_prompt=show_final_prompt,
    )

    answer, elapsed = ask_model(
        messages,
        model=model,
        num_predict=num_predict,
    )

    print("Rin:")
    print(answer)
    print()
    print(f"[{elapsed:.2f} seconds]")
    print()

    append_event(
        "persona_test",
        session_id=session_id,
        model=model,
        category_key=category_key,
        category_number=category.number,
        category_name=category.name,
        question_number=case.number,
        mode=mode,
        user_prompt=case.user_prompt,
        guidance=case.guidance,
        final_prompt=final_prompt,
        answer=answer,
        elapsed_seconds=round(elapsed, 3),
        num_predict=num_predict,
    )


def run_tests(
    *,
    model: str = MODEL,
    session_id: str | None = None,
    category_key: str | None = None,
    question_number: int | None = None,
    mode: TestRunMode = "raw",
    show_final_prompt: bool = False,
    num_predict: int | None = None,
) -> str:
    if session_id is None:
        session_id = new_session_id()

    categories = resolve_categories(category_key)
    modes = expand_modes(mode)

    append_event(
        "test_run_start",
        session_id=session_id,
        model=model,
        category_key=category_key,
        question_number=question_number,
        mode=mode,
        num_predict=num_predict,
    )

    try:
        for current_category_key, category in categories:
            print()
            print("#" * 80)
            print(f"Category: {category.number}. {category.name} [{current_category_key}]")
            print("#" * 80)

            selected_cases = select_cases(category, question_number)

            for case in selected_cases:
                for current_mode in modes:
                    run_single_test(
                        model=model,
                        session_id=session_id,
                        category_key=current_category_key,
                        category=category,
                        case=case,
                        mode=current_mode,
                        show_final_prompt=show_final_prompt,
                        num_predict=num_predict,
                    )

    finally:
        append_event(
            "test_run_end",
            session_id=session_id,
            model=model,
            category_key=category_key,
            question_number=question_number,
            mode=mode,
            num_predict=num_predict,
        )

    return session_id


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run RIN Stage 0 persona / behavior tests."
    )

    parser.add_argument(
        "--model",
        default=MODEL,
        help=f"Ollama model name. Default: {MODEL}",
    )

    parser.add_argument(
        "--mode",
        choices=["raw", "guided", "both"],
        default="raw",
        help=(
            "Test mode. raw = field prompt only; "
            "guided = prompt + guidance; "
            "both = raw then guided."
        ),
    )

    parser.add_argument(
        "--category",
        default=None,
        help="Run only one category by key, e.g. family, voice, failure_modes.",
    )

    parser.add_argument(
        "--question",
        type=int,
        default=None,
        help="Run only one question number inside the selected category.",
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List categories and questions, then exit.",
    )

    parser.add_argument(
        "--show-final-prompt",
        action="store_true",
        help="Print the exact final prompt sent to the model.",
    )

    parser.add_argument(
        "--num-predict",
        type=int,
        default=384,
        help="Maximum number of tokens to generate per test answer. Use 0 to disable the limit. Default: 384.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.list:
        list_categories()
        list_tests(args.category)
        return

    if args.question is not None and args.category is None:
        raise ValueError("--question requires --category")

    session_id = new_session_id()

    print("RIN Stage 0 persona / behavior tests")
    print(f"Model: {args.model}")
    print(f"Session: {session_id}")
    print(f"Mode: {args.mode}")

    if args.category:
        print(f"Category: {args.category}")

    if args.question is not None:
        print(f"Question: {args.question}")

    num_predict = args.num_predict if args.num_predict > 0 else None

    print()

    run_tests(
        model=args.model,
        session_id=session_id,
        category_key=args.category,
        question_number=args.question,
        mode=args.mode,
        show_final_prompt=args.show_final_prompt,
        num_predict=num_predict,
    )


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import shlex
from typing import Any

from core import MODEL, STAGE0_LOG_PATH, append_event, new_session_id
from runtime import (
    Message,
    ask_model,
    ask_model_stream_to_stdout,
    build_bootstrap_context,
    build_system_prompt,
    load_recent_chat_events,
)
from test import list_categories, list_tests, run_tests


def print_help() -> None:
    print(
        """
Commands:
  /help                                      show this help
  /bye                                       exit
  /reset                                     clear current session history
  /history                                   show current visible session messages

  /categories                                list test categories
  /tests                                     list all test categories and questions
  /tests --category family                   list questions in one category

  /test                                      run all tests in raw mode
  /test --mode raw                           run all tests in raw mode
  /test --mode guided                        run all tests in guided mode
  /test --mode both                          run raw and guided tests
  /test --category family                    run one category
  /test --category family --question 2       run one question in a category
  /test --category family --mode both        run one category in both modes
  /test --category voice --mode both --num-predict 256 run tests with generation length limit
  /test --category voice --mode both --num-predict 256 run tests with explicit generation limit
  /tests 2                                  list questions in category 2
  /test --category 2 --question 4           run question 2.4
  /test 2 --question 4                      same shorthand

Normal text is sent to Rin.

Note:
  Tests are intentionally isolated. They do not use current chat history or bootstrap context.
""".strip()
    )


def show_history(messages: list[Message]) -> None:
    visible_messages = [message for message in messages if message["role"] != "system"]

    if not visible_messages:
        print("History is empty.")
        return

    for index, message in enumerate(visible_messages, start=1):
        role = message["role"]
        content = message["content"].replace("\n", " ")

        if len(content) > 180:
            content = content[:177] + "..."

        print(f"{index}. {role}: {content}")


def parse_option_command(command: str) -> dict[str, Any]:
    tokens = shlex.split(command)

    result: dict[str, Any] = {
        "category": None,
        "question": None,
        "mode": "raw",
        "show_final_prompt": False,
        "num_predict": None,
    }

    index = 1

    while index < len(tokens):
        token = tokens[index]

        if token == "--category":
            index += 1

            if index >= len(tokens):
                raise ValueError("--category requires a value")

            result["category"] = tokens[index]

        elif token == "--question":
            index += 1

            if index >= len(tokens):
                raise ValueError("--question requires a value")

            try:
                result["question"] = int(tokens[index])
            except ValueError as error:
                raise ValueError("--question must be an integer") from error

        elif token == "--mode":
            index += 1

            if index >= len(tokens):
                raise ValueError("--mode requires a value")

            mode = tokens[index]

            if mode not in {"raw", "guided", "both"}:
                raise ValueError("--mode must be one of: raw, guided, both")

            result["mode"] = mode

        elif token == "--show-final-prompt":
            result["show_final_prompt"] = True

        elif token == "--num-predict":
            index += 1

            if index >= len(tokens):
                raise ValueError("--num-predict requires a value")

            try:
                result["num_predict"] = int(tokens[index])
            except ValueError as error:
                raise ValueError("--num-predict must be an integer") from error

        else:
            # Convenience shorthand:
            #   /test family
            #   /tests family
            if result["category"] is None:
                result["category"] = token
            else:
                raise ValueError(f"Unknown argument: {token}")

        index += 1

    return result


def handle_tests_command(command: str) -> None:
    try:
        options = parse_option_command(command)
        list_tests(options["category"])
    except ValueError as error:
        print(f"Command error: {error}")


def handle_test_command(command: str, *, model: str, session_id: str) -> None:
    try:
        options = parse_option_command(command)

        if options["question"] is not None and options["category"] is None:
            raise ValueError("--question requires --category")

        raw_num_predict = options["num_predict"]

        if raw_num_predict is None:
            num_predict = None
            adaptive = True
        elif raw_num_predict <= 0:
            num_predict = None
            adaptive = False
        else:
            num_predict = raw_num_predict
            adaptive = False

        run_tests(
            model=model,
            session_id=session_id,
            category_key=options["category"],
            question_number=options["question"],
            mode=options["mode"],
            show_final_prompt=options["show_final_prompt"],
            num_predict=num_predict,
            adaptive=adaptive,
        )

    except ValueError as error:
        print(f"Command error: {error}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interactive RIN Stage 0 local chat.")

    parser.add_argument(
        "--model",
        default=MODEL,
        help=f"Ollama model name. Default: {MODEL}",
    )

    parser.add_argument(
        "--bootstrap-last",
        type=int,
        default=0,
        help=(
            "Load the last N previous chat events from logs/rin_stage0.jsonl "
            "as raw bootstrap context. Default: 0."
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    session_id = new_session_id()

    bootstrap_events = load_recent_chat_events(args.bootstrap_last)
    bootstrap_context = build_bootstrap_context(bootstrap_events)
    system_prompt = build_system_prompt(bootstrap_context)

    messages: list[Message] = [
        {"role": "system", "content": system_prompt},
    ]

    append_event(
        "session_start",
        session_id=session_id,
        model=args.model,
        bootstrap_last=args.bootstrap_last,
        bootstrap_events=len(bootstrap_events),
    )

    print("RIN local chat prototype")
    print(f"Model: {args.model}")
    print(f"Session: {session_id}")
    print(f"Log: {STAGE0_LOG_PATH}")

    if bootstrap_events:
        print(f"Bootstrap: loaded {len(bootstrap_events)} previous chat events")

    print("Type /help for commands.")
    print()

    while True:
        try:
            user_input = input("You > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")

            append_event(
                "session_end",
                session_id=session_id,
                model=args.model,
                reason="keyboard_interrupt_or_eof",
            )
            break

        if not user_input:
            continue

        if user_input == "/bye":
            print("Bye.")

            append_event(
                "session_end",
                session_id=session_id,
                model=args.model,
                reason="/bye",
            )
            break

        if user_input == "/help":
            print_help()
            continue

        if user_input == "/categories":
            list_categories()
            continue

        if user_input == "/tests" or user_input.startswith("/tests "):
            handle_tests_command(user_input)
            continue

        if user_input == "/test" or user_input.startswith("/test "):
            handle_test_command(
                user_input,
                model=args.model,
                session_id=session_id,
            )
            continue

        if user_input == "/reset":
            messages = [{"role": "system", "content": system_prompt}]
            print("Session history cleared.")

            append_event(
                "command",
                session_id=session_id,
                model=args.model,
                command="/reset",
                bootstrap_restored=bool(bootstrap_context),
            )
            continue

        if user_input == "/history":
            show_history(messages)
            continue

        if user_input.startswith("/"):
            print(f"Unknown command: {user_input}")
            print("Type /help for commands.")
            continue

        messages.append({"role": "user", "content": user_input})

        print()
        print("Rin > ", end="", flush=True)

        answer, elapsed = ask_model_stream_to_stdout(messages, model=args.model)

        messages.append({"role": "assistant", "content": answer})

        print()
        # print(f"Rin > {answer}")
        print()
        print(f"[{elapsed:.2f} seconds]")
        print()

        append_event(
            "chat",
            session_id=session_id,
            model=args.model,
            user=user_input,
            answer=answer,
            elapsed_seconds=round(elapsed, 3),
            session_messages=len(messages),
            bootstrap_events=len(bootstrap_events),
        )


if __name__ == "__main__":
    main()

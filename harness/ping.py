"""Step 1 smoke: one request through the full logging path.

    python -m harness.ping --profile profiles/local-heretic.yaml "привет"

Writes logs/stage2/<run_id>.jsonl with run_start (full conditions snapshot),
turn (request, answer, timing) and run_end (GPU placement). No card yet: the
card + prompt builder is step 2.
"""

from __future__ import annotations

import argparse
import sys

from harness.backend_meta import check_expected, gpu_placement, model_meta
from harness.config import load_profile
from harness.events import EventWriter, git_state
from harness.runner import GenerationError, GenerationInterrupted, chat


def main() -> int:
    ap = argparse.ArgumentParser(description="RinST harness smoke: one logged request.")
    ap.add_argument("message", help="user message")
    ap.add_argument("--profile", required=True, help="profiles/<name>.yaml")
    ap.add_argument("--system", default=None, help="optional system message (no card in step 1)")
    ap.add_argument("--seed", type=int, default=1000)
    args = ap.parse_args()

    profile = load_profile(args.profile)
    log = EventWriter()

    meta = model_meta(profile)
    problems = check_expected(profile, meta)
    log.write(
        "run_start",
        kind="ping",
        profile=profile.to_log(),
        runner=meta["runner"],
        model=meta["model"],
        meta_notes=meta["notes"],
        preflight_problems=problems,
        git=git_state(),
        host={"label": profile.host_label},
    )
    if problems:
        print("PREFLIGHT FAILED (Modelfile does not match profile):", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        log.write("run_end", status="aborted_preflight")
        print(f"log: {log.path}", file=sys.stderr)
        return 2

    messages = []
    if args.system:
        messages.append({"role": "system", "content": args.system})
    messages.append({"role": "user", "content": args.message})

    print(f"[{profile.model} @ {profile.runner.base_url}]  run {log.run_id}\n")
    status = "ok"
    try:
        gen = chat(profile, messages, seed=args.seed,
                   echo=lambda s: print(s, end="", flush=True))
        print("\n")
        event_type, extra = "turn", {}
    except GenerationInterrupted as err:
        gen, status = err.partial, "interrupted"
        print(f"\n\n[interrupted: {err.reason}]")
        event_type, extra = "turn_interrupted", {"interruption_reason": err.reason}
    except GenerationError as err:
        print(f"\n[ERROR] {err}", file=sys.stderr)
        log.write("turn_error", http_status=err.status, error=err.body,
                  timing={"elapsed_s": round(err.elapsed_s, 3)},
                  request={"messages": messages})
        log.write("run_end", status="error")
        print(f"log: {log.path}", file=sys.stderr)
        return 1

    log.write(
        event_type,
        test=None,
        dialog={"turn_index": 1, "context_messages": len(messages)},
        request={"messages": messages, "seed": args.seed},
        response={"text": gen.text, "reasoning_text": gen.reasoning_text or None,
                  "finish_reason": gen.finish_reason},
        usage=gen.usage,
        timing={"elapsed_s": gen.elapsed_s, "ttft_s": gen.ttft_s, "tok_per_s": gen.tok_per_s},
        **extra,
    )

    placement = gpu_placement(profile)
    warnings = []
    if gen.reasoning_text:
        warnings.append("model returned reasoning text: thinking is NOT off (check reasoning_effort)")
    if placement and placement.get("on_gpu_fully") is False:
        warnings.append(f"model not fully on GPU: {placement.get('gpu_fraction')} in VRAM")
    log.write("run_end", status=status, gpu=placement, warnings=warnings)

    print(f"ttft {gen.ttft_s}s | {gen.tok_per_s} tok/s | finish: {gen.finish_reason}")
    if placement and "error" not in placement:
        print(f"GPU: {placement['gpu_fraction']:.0%} in VRAM, ctx {placement.get('context_length')}")
    for w in warnings:
        print(f"WARNING: {w}")
    print(f"log: {log.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

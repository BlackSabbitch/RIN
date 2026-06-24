# RIN src refactor proposal

This folder contains a refactored version of the current `src/` files.

Main changes:

- `core.py` is reduced to a deprecated compatibility shim.
- Configuration moved to `config.py`.
- Prompt constants moved to `prompts.py`.
- Logging/session helpers moved to `logging_utils.py`.
- Persona test dataclasses moved to `persona_tests/schema.py`.
- Persona test categories moved into one module per category under `persona_tests/`.
- `persona_tests/registry.py` assembles `TEST_CATEGORIES`.
- `test.py` remains the CLI/runner and keeps `TEST_SUBSETS`.
- `chat.py` and `runtime.py` import from the new modules directly.

Suggested local use:

1. Copy the new files into your project `src/`.
2. Run:
   `python -m py_compile src/*.py src/persona_tests/*.py`
3. Run:
   `python src/test.py --list`
4. Run:
   `python src/test.py --category voice --question 2 --mode raw --num-predict 128`
5. Run:
   `python src/chat.py`

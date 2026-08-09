# HumanEval submission validator

Validate HumanEval Excel workbooks named `Human Eval <language>_<country>.xlsx`.

```sh
uv run python validate_humaneval_submission.py /path/to/HumanEval
```

The validator checks required columns on the first two sheets and requires a
non-empty `Validator Note` whenever `Error Type` is an "Other (add note)"
value. It writes diagnostic logs beside the input folder.

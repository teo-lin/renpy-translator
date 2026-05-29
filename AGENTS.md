# Agent Guidelines

## Character encoding

- Never use Unicode arrows, symbols, or emoji in source code strings, comments, or print statements.
- Use only ASCII characters in code: `->` not `->` (U+2192), `>=` not `>=`, `...` not `...`, etc.
- This project runs on Windows with cp1252 as the default console encoding. Non-ASCII characters in print/log output will raise UnicodeEncodeError at runtime.
- The same rule applies to test files, scripts, config files, and any other text written to disk.

## No emojis

- Do not add emojis anywhere: source files, comments, commit messages, YAML, markdown docs.
- The user has not requested them and they cause encoding issues on this system.

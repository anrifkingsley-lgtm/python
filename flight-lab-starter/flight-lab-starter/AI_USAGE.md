# AI Usage Disclosure

<!--
Fill in this file before you submit. Submissions without it are not graded.
If you used no AI tools, delete everything below and write only:
No AI tools were used.
-->

## Tools used

- Tool and version (e.g. ChatGPT GPT-5, Claude, GitHub Copilot):Gemini 3

## Conversation links

- Link 1:https://share.gemini.google/Gjwep7iMqCKT
- Link 2:

## What I used them for

-  debugging and explain some notion like : paths,strptime ....

## Which parts of the code were AI-generated or substantially AI-assisted

| File | Function or part | How (generated / modified / explained) |
| validator.py | strptime-strpftime | i asked ia |
| query.py |  78-95|i used a prompt by copilot  |
|flight_perser| function logging| i asked ia|
## Key prompts

1.comment eviter le piège des booléens en Python (isinstance(True, int)) et des nombres non finis=> english(How to avoid the pitfalls of booleans in Python (`isinstance(True, int)`) and non-finite numbers)
2.j'arrive pas a eviter ce probleme de regrex voici ma syntax:def _parse_datetime(text):
    try:
        return datetime.strptime(text, "%Y-%m-%d %H:%M")
    except ValueError:
        return None

## What I changed or verified myself

Verification of file locations and repository structure, ensuring that the necessary files are at the project root and that generated items are correctly ignored by .gitignore.
 i do the structure of the code.
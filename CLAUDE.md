<!-- wrappit:start -->
## Wrappit: this repo explains itself

Every file has a short note in `.wrappit/files/<path>.md`. The project summary is `.wrappit/PROJECT.md`.

- Before you change a file, read its note: `wrappit show <file>`.
- After you create a file, run `wrappit new <file>` and fill in every section.
- After you change a file, update its note so it's still true, then run `wrappit stamp <file>`.
  If the change doesn't affect anything the note says: `wrappit stamp --unchanged <file>`.
- Renamed or deleted a file: `wrappit mv <old> <new>` or `wrappit prune`.
- Notes are short and plain: What it is, How to navigate it, What it interacts with,
  Why it exists, Helpful notes. A few sentences each, written for a person who has
  never seen the code.
- Commit with plain git: stage the files you changed and their notes by name
  (`git add <file> .wrappit/files/<file>.md`), then `git commit`. Never `git add -A` or `git add .`.
  The commit check runs by itself and blocks commits while notes are missing or out of date.
<!-- wrappit:end -->

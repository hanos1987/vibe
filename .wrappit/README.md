# How this repo documents itself (Wrappit)

Every file in this repository has a short note in .wrappit/files/, at the same
path plus ".md". .wrappit/PROJECT.md is the summary of the whole project. Start
there, then read the note for any file before you open it.

Rules for anyone changing code here, human or AI:

1. When you add a file, run "wrappit new <file>" and fill in every section.
2. When you change a file, update its note so it's still true.
3. Then run "wrappit stamp <file>". This records which version of the file the
   note describes. If the change doesn't affect the note, use
   "wrappit stamp --unchanged <file>".
4. Keep notes short and plain: a few sentences per section. Say what someone
   needs to find their way, not everything the code does.
5. Commit with "wrappit save \"message\"", or add the .wrappit folder to your
   commit. Commits are blocked while a changed file's note is missing,
   empty, or out of date.

"wrappit status" shows what needs work. Files listed in .wrappit/ignore don't
need notes.

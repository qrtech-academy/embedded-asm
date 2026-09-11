# The Book
The course typeset as a book: one chapter per lecture, built with LuaLaTeX into
[`embedded-asm.pdf`](./embedded-asm.pdf). The lectures are the source of truth and the book follows
them, so a correction goes into the lecture first and is then carried into its chapter.

---

## Layout

```text
book.tex        The top-level document: front matter, the six chapters, the appendix.
asmbook.sty     The design: page, fonts, headings, code blocks, tables, figures, exercises.
front/          Title and copyright pages, and the preface.
chapters/NN/    Chapter N, from lectures/LNN: chapter.tex, then one file per section.
back/           Appendix A, the short answers to the hand-calculation exercises.
figures.py      Renders the figures as vector PDFs by reusing the builders in diagrams/.
Makefile        Figures first, then two LuaLaTeX passes so the cross-references resolve.
build/          Everything the build writes. Generated, and not committed.
```

Each chapter mirrors its lecture. Appendices A, B, C become sections N.1, N.2, N.3; the README's
outcomes, questions and next lecture become the Review section; and the exercises appendix is the
last section. LaTeX labels carry the chapter as a prefix (`c3:sec:table`, `c5:ex:crosscheck`), so
two chapters never collide.

---

## Building
You need LuaLaTeX with the usual packages, the TeX Gyre and DejaVu fonts, and the Python
environment the figures are drawn with. On Ubuntu or WSL:

```bash
sudo apt -y install texlive-luatex texlive-latex-extra texlive-fonts-recommended fonts-dejavu-core
python3 -m venv .venv
.venv/bin/pip install -r diagrams/requirements.txt
```

Then, from the repository root:

```bash
make -C book          # build book/embedded-asm.pdf
make -C book clean    # remove everything the build writes
```

The figures are rendered on demand from [`diagrams/`](../diagrams/README.md), so the book's are the
course's own drawings as vectors rather than copies of the PNGs. A figure too wide for the page
gets a book-only layout in `BOOK_LAYOUTS` in `figures.py`, built from the same data; the course's
PNGs are never changed for the book's sake. A new figure is added to `FIGURES` in the Makefile.

The build ends by listing any `Overfull`, `Underfull` or `Warning` lines from the LaTeX log. A
clean build lists none. `PYTHON=... make -C book` points it at another Python environment.

---

## Releasing a new edition
An edition is a git tag, and the book names it: readers are told to clone that tag, so the code
and test suites they get are exactly the ones the text describes.

1. **Correct the lecture, then the chapter.** Run `make lint` at the root for the lecture.
2. **Name the edition.** `front/title.tex` names it twice, on the title page and the copyright
   page, as edition, version and date, and the copyright page and the clone command in
   `front/preface.tex` name the tag.
3. **Build and read it.** `make -C book` should list no warnings, and every page you changed is
   worth looking at: a paragraph that grew can push a figure or a code block onto the next page.
4. **Commit the sources and `embedded-asm.pdf` together**, so the PDF on any commit is the one its
   sources build.
5. **Tag that commit and push both:**

   ```bash
   git tag -a v1.1.0 -m "Embedded Assembly for the ATmega328P, second edition"
   git push origin main v1.1.0
   ```

6. Optionally, attach the PDF to a GitHub release for the tag.

**A published tag is never moved.** It names what a copy of the book already in someone's hands
describes. A correction goes out as a new tag instead: a patch release (`v1.0.1`) for errata, a
minor release (`v1.1.0`) for additions, and a major one for a restructured course.

**The worked solutions are the first addition waiting.** The first edition says they are
published later, in `front/title.tex`, `front/preface.tex`, `back/answers.tex` and every
`chapters/NN/exercises.tex`. Publishing them changes that wording, and so is a new edition.

---

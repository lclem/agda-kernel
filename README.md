[![Agda](https://img.shields.io/badge/agda-2.5.4.2-blue.svg)](https://github.com/agda/agda/releases/tag/v2.5.4.2)
[![agda-stdlib](https://img.shields.io/badge/agda--stdlib-0.17-blue.svg)](https://github.com/agda/agda-stdlib/releases/tag/v0.17)
[![agda2html](https://img.shields.io/badge/agda2html-0.2.3.0-blue.svg)](https://github.com/wenkokke/agda2html/releases/tag/v0.2.3.0)


# agda-kernel
An experimental Agda kernel for Jupyter.

Installation
------------

    pip install agda_kernel
    python -m agda_kernel.install

Functionality
-------------

Each code cell must begin with a line of the  form ``module A.B.C where``.
For instance:

```agda
module A.B.C where

id : {A : Set} → A → A
id x = x
```

Upon execution, the file `A/B/C.agda` is created containing the cell's contents,
and it is fed to the Agda interpreter (via `agda --interact`).
The result of typechecking the cell are then displayed.

After a cell has been evaluated, one can

- Infer the type of a closed expression,
by putting the cursor near the expression and hitting SHIFT-TAB.
If the expression is in parentheses ``(...)``, then the cursor should be near one of the two parentheses.
If the expression is just a literal, then the cursor should be inside, or in the vicinity of the literal.

- Normalise a closed expression,
by putting the cursor near the expression and hitting TAB.
Expression localisation follows the same rules as in the previous point.

Editing
-------

Inputting common UNICODE characters is facilitated by the code-completion feature of Jupyter.

- When the cursor is immediately to the right of one of the `base form` symbols
hitting TAB will replace it by the corresponding `alternate form`.
Hitting TAB again will go back to the base form.

| base form | alternate form |
|:---------:|:----------------:|
| -> | → |
| \ | λ |
| < | ⟨ |
| B | 𝔹 |
| > | ⟩ |
| = | ≡ |
| top | ⊤ |
| /= | ≢ |
| bot | ⊥ |
| alpha | α |
| /\ | ∧ |
| e | ε |
| \/ | ∨ |
| emptyset | ∅ |
| neg | ¬ |
| qed | ∎ |
| forall | ∀ |
| Sigma | Σ |
| exists | ∃ |
| Pi | Π |
| \[= | ⊑ |
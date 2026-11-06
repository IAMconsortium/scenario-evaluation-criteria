"""mkdocs-gen-files script: generate the "Summary" section pages.

Criteria are added/removed independently of the docs, so these pages are
generated at build time (as virtual files, never written under
``docs/summary/``) instead of being hand-maintained there. See
``summary_pages.py`` for the shared rendering logic and ``mkdocs_nav.py``
for the matching sidebar nav, generated from the same data.
"""

import mkdocs_gen_files
from summary_pages import (
    criterion_page_slug,
    criterion_type_dir,
    load_summary_context,
    render_criteria_type,
    render_criterion,
    render_summary_tree,
)

ctx = load_summary_context()

with mkdocs_gen_files.open("summary/index.md", "w") as f:
    f.write("# Summary\n\n")
    f.write(render_summary_tree(ctx))
    f.write("\n")

for crit_type, criteria in ctx["criteria_by_type"].items():
    if not criteria:
        continue
    type_dir = criterion_type_dir(crit_type)

    with mkdocs_gen_files.open(f"summary/{type_dir}/index.md", "w") as f:
        f.write(f"# {crit_type}\n\n")
        f.write(render_criteria_type(crit_type, ctx))
        f.write("\n")

    for criterion in criteria:
        slug = criterion_page_slug(criterion)
        with mkdocs_gen_files.open(f"summary/{type_dir}/{slug}.md", "w") as f:
            f.write(f"# {criterion}\n\n")
            f.write(render_criterion(criterion, ctx, "../../../components/"))
            f.write("\n")

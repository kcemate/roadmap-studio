# Roadmap Studio

Roadmap Studio supports portfolio owners and executives preparing reviews of Savings and Avoidance initiatives. Users organize work into pillars/workstreams, maintain approvals and schedules, compare alternatives, and download executive presentations.

The product must make every reported value explainable, preserve work across edits/scenario switches/releases, and keep private project data on the user's device. It is an operational tool, not a marketing site.

## Constraints

- No backend, external runtime calls, CDN scripts, or audit log.
- No CSV or Excel file import, intentionally. Rows copied from a spreadsheet can be pasted from the clipboard (tab-separated cells only).
- Local autosave, local recovery versions, and portable JSON project files.
- Keep Savings, Avoidance, approvals, and actual realization distinct.
- Preserve existing project compatibility and the user's approved executive presentation composition.
- Generate a self-contained HTML app plus the existing vendored PowerPoint runtime from maintainable source fragments.

## Visual Authority

The current application is the design authority: restrained white/near-white surfaces, system typography, compact operating controls, green Savings and blue Avoidance. Roadmap marks use the value-type colour with a darker realized share on the web, in PNG, in Present mode, and on slides; status is a labelled pill beside each mark (never colour alone), and an amber outline marks At Risk or Blocked work. The Executive Summary, on the web and as the first content slide, has two centered prominent blocks above one continuous bar of six segments (Realized, Active remaining, Proposed remaining, each split Savings/Avoidance), rounded only at its outer ends, with the same key on both. Readability and accurate financial meaning outrank decorative changes.

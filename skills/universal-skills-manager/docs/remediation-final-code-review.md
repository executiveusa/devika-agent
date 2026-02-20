# Code Review: security/scan-skill-remediation branch

Reviewed by Claude Code v2.1.38 backed by Opus 4.6

18 commits reviewed across 4 phases against the 18 findings in
docs/scan_skill-security-analysis.md.

---
Phase 1 — Critical (C1, C2, C3): APPROVED

All three critical findings fully closed.

- C1 (symlinks): Triple-layer defense — followlinks=False, is_symlink()
rejection, resolve().relative_to() path containment. No exfiltration possible.
- C2 (unclosed HTML comments): Post-loop in_comment check emits critical
finding. No silent suppression.
- C3 (ANSI injection): Comprehensive regex + control-character stripping in
_add_finding(). Terminal output cannot be hijacked.

---
Phase 2 — High (H1-H5): APPROVED

All five high findings fully closed.

- H1 (file size): 10 MB limit enforced before content read. DoS prevented.
- H2 (file types): Three frozensets cover scripts, configs, and build files.
No trivial evasion via extension.
- H3 (multi-line): Continuation-line joining + dedup prevents both missed
detections and duplicate findings.
- H4 (credentials): 19 new env-var patterns + 10 hardcoded-secret patterns
(AWS keys, GitHub PATs, JWTs, Slack tokens, private keys).
- H5 (URI schemes): data:, javascript:, and // protocol-relative URLs all
detected.

---
Phase 3 — Medium (M1-M5): APPROVED with one important gap

- M1 (path leakage): Username leakage is prevented, but the fix returns
path.name (bare basename) rather than a proper relative path. Usability loss —
  reports for nested structures lose directory context. Not a security gap, but
  diverges from the plan's intent.
- M2 (unicode/homoglyphs): Partial fix. Homoglyphs are detected (good), and
NFC normalization handles combining diacritics. However, homoglyphs are not
translated to ASCII before pattern matching, so "ignorе previous instructions"
  (Cyrillic е) triggers homoglyph_detected but still bypasses the
instruction_override check. The test passes only because it accepts either
finding. The semantic evasion is not fully neutralized.
- M3 (state clearing): Fully fixed — findings and files_scanned reset at top
of scan_path().
- M4 (regex compilation): All patterns moved to module level. Clean refactor,
no regressions.
- M5 (dotfiles): Blanket dotfile skip removed; only .git, .svn, .hg,
__pycache__, node_modules directories excluded. Correct.

---
Phase 4 — Low (L1-L5): APPROVED

All five low findings effectively addressed.

- L1 (unreadable files): Separate handling for binary (UnicodeDecodeError) and
  permission errors. Info-level findings emitted.
- L2 (depth/file limits): MAX_DIR_DEPTH=10, MAX_FILE_COUNT=1000. File limit
emits a warning. Minor suggestion: also emit a finding when depth limit causes
  directory skip (currently silent).
- L3 (TOCTOU): O_NOFOLLOW + fstat() on the open fd completely eliminates the
check-use gap. Proper fd cleanup in finally.
- L4 (multiple HTML comments): while True loop scans remainder of each line.
Dedup key expanded to file+line+category+description to allow multiple
distinct comments per line.
- L5 (role hijacking FPs): Negative lookahead expanded with 8 additional safe
continuations. True positives preserved.

---

## Recommended Follow-ups

Priority: Important
Issue: M2 homoglyph bypass
Detail: Homoglyphs are detected but not translated before semantic pattern
  matching. "ignorе previous instructions" (Cyrillic е) evades
  instruction_override. Add ASCII transliteration pass before running
  _check_* methods.
────────────────────────────────────────
Priority: Minor
Issue: M1 path semantics
Detail: path.name loses directory structure. Consider actual relative-path
  computation.
────────────────────────────────────────
Priority: Minor
Issue: L2 silent depth skip
Detail: Emit info-level finding when MAX_DIR_DEPTH causes directories to be
  pruned.
Bottom Line

17 of 18 findings are fully closed. The M2 homoglyph fix detects the attack
but doesn't neutralize the evasion — homoglyph-laden text still bypasses the
semantic checks it's meant to protect. This is the one gap worth addressing
before considering the remediation complete.

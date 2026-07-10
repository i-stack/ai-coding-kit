<!-- last-verified: 2026-06 -->
# Git Workflow (iOS Engineering Specialization)

> This is an English mirror of the authoritative Chinese `references/git_workflow.md`.
> In case of discrepancies, the Chinese source takes precedence.

## Table of Contents
- Usage Rules
- iOS-Specific Conflict Governance
- Dependency & Lock File Commit Strategy
- Branch Model & Hotfix
- Commit & PR Granularity
- revert / reset / cherry-pick Selection
- .gitignore Baseline
- Common Anti-Patterns

## Usage Rules
- This file only covers iOS / Xcode project git-specific tactics; general PR splitting, ownership, and Review responsibilities see [team_collaboration.md](team_collaboration.md); build dependency governance see [build_release_and_ci.md](build_release_and_ci.md).
- Triggers: `project.pbxproj` conflicts, storyboard / xib merging, Asset Catalog binary diff, Pods commit strategy, `Package.resolved` conflicts, Hotfix branch strategy, Xcode project file multi-person collaboration.
- Does not trigger: Swift source-only conflicts → follow [team_collaboration.md](team_collaboration.md) PR rules; CI failure / build configuration issues → follow [build_release_and_ci.md](build_release_and_ci.md).
- Any git tactical advice must explicitly state "reversibility of the decision + whether it affects others' local working trees"; must not just give commands without explaining consequences.

## iOS-Specific Conflict Governance

### project.pbxproj Conflicts
- Root cause: pbxproj is a single-file plist; adding files, adjusting Build Phases, modifying Capabilities all write to the same file — most prone to conflicts with parallel work.
- Three-level handling (light to heavy):
  1. **Small conflicts**: manually align by UUID + isa fields; retain both sides' new nodes; use `xcodeproj` Ruby gem or `xUnique`-type tools to organize, then diff-review.
  2. **Medium conflicts**: both sides close Xcode, use `git checkout --ours` / `--theirs` to pick one side, then manually redo the other side's changes (re-drag new files / re-check Target Membership).
  3. **Unresolvable**: as conflict prevention, team agrees "PRs adding files / changing Build Phases merge serially"; long-term solution is migrating to SPM + modularity to reduce root pbxproj changes.
- Mandatory rule: after resolving pbxproj conflicts, **must do a full local build** before pushing; "looks like no conflicts" is not sufficient reason to push.

### storyboard / xib / xcassets Merging
- storyboard / xib are XML but Xcode reorders nodes; diff noise is high; when conflicting, prefer **redoing** UI changes rather than hand-merging XML.
- xcassets internal Contents.json text can be manually merged; binary resources (PNG / PDF in imageset) can only "keep both + delete duplicates in Xcode".
- Team constraint suggestion: limit single storyboard to single Feature owner; multiple people modifying same storyboard must be serial; new pages prefer SwiftUI or standalone xib rather than stuffing into large storyboard.

### Asset Catalog / Binary Resources
- Large images, fonts, videos do not go into git; use Git LFS or separate resource repo + SPM resource bundle; resources entering git must be compressed first and unified in spec (@2x / @3x naming fixed).
- Binary resource conflicts have no "auto-merge"; only strategy: both sides negotiate which to keep, delete the other.

## Dependency & Lock File Commit Strategy

### CocoaPods
- `Podfile.lock` **must** be committed: CI / others' `pod install` can only reproduce same version.
- `Pods/` directory: open-source projects may not commit (rely on CI to rebuild); closed-source / private source / manageable Pod size recommend committing to avoid offline build failures and remote source outages blocking the whole team.
- Once the decision is written into README, all team members stay consistent; switching mid-way requires everyone to clean local Pods + switch .gitignore at once.

### SPM
- `Package.resolved` **must** be committed (under Xcode projects located at `*.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/`). When conflicting, prefer the **newer version** and verify locally with `Resolve Package Versions`; must not hand-merge the file's hashes.
- Private SPM dependencies must use version pinning (exact / from); `branch: "main"` is prohibited; otherwise the lock file cannot guarantee reproducibility.

### Hybrid (Pods + SPM)
- Both sides' versions must be unioned; avoid same lib loaded from dual sources; conflict manifests as "compilation passes but runtime symbol conflict / slow launch".
- Lock file conflicts handled per各自 strategy; not interchangeable.

## Branch Model & Hotfix
- Default trunk-based + short branches: `main` is the releasable mainline; feature branch lifetime ≤ 5 days; over-limit must merge in stages or reduce scope.
- gitflow only used when "maintaining multiple LTS versions simultaneously"; otherwise its `develop` / `release` branches widen the conflict window.
- Hotfix branches must be cut from "production tag" (not `main` HEAD); after fix, merge back to `main` and cherry-pick to all affected release branches; merging only to main and considering it done is not acceptable.
- Any branch strategy must be accompanied by: annotated tag at release points (containing version + commit + modifier); dSYM corresponds one-to-one with tags (see [build_release_and_ci.md](build_release_and_ci.md) Release & Rollout section).

## Commit & PR Granularity
- Single commit has single theme: feature / refactor / style not mixed; commit message first line ≤ 72 characters + verb-starting (add / fix / refactor / chore); body explains **why** not "what was done".
- Commits involving pbxproj changes committed separately for easy revert without touching source code.
- PR splitting granularity synced with team PR rules in [team_collaboration.md](team_collaboration.md) PR rules section; this section only adds iOS-specific points:
  - "New module / Target" as separate PR; not mixed with business changes.
  - "Dependency upgrade" as separate PR; must include changelog and rollback explanation.
  - "Xcode version switch / Swift version upgrade" as separate PR; requires team to sync local toolchain.

## revert / reset / cherry-pick Selection

| Operation | Applicable Scenarios | Risk | Affects Others? |
|------|----------|------|--------------|
| `git revert <sha>` | Undo erroneous changes already merged to mainline | Leaves reverse commit; history intact | No (recommended default) |
| `git reset --soft HEAD~N` | Reorganize local unpushed commits | Local only; safe before push | No |
| `git reset --hard <sha>` | Discard local mistakes completely | **Unrecoverable** uncommitted work | No (premise: not pushed) |
| `git reset --hard` on pushed branch | Almost never should be done | Rewrites history; breaks others' local | **Strong impact**; prohibited for shared branches |
| `git cherry-pick <sha>` | Backport fix to release branch / move single commit | Context loss risk; may introduce implicit dependencies | Does not affect mainline, but cherry-pick chain must be traced |
| `git rebase -i` | Tidy local unpushed commits | Local only safe | No (premise: not pushed) |
| `git push --force-with-lease` | Necessary push after personal branch tidying | Safer than `--force` (only allows if remote unchanged) | Does not affect others' collaborative branches |

Mandatory rule: **any operation that rewrites pushed history** (force-push, reset --hard then push, rebase of pushed branch) is **prohibited** on shared branches; only allowed on personal feature branches with explicit reviewer notification.

## .gitignore Baseline
Must ignore:
```
# Xcode user data
xcuserdata/
*.xcuserstate
*.xcuserdatad/

# DerivedData
DerivedData/
Build/

# Pods (per team strategy, choose one; consistent with dependency governance section)
# Pods/

# SPM resolution cache (keep Package.resolved; ignore local build cache)
.swiftpm/xcode/package.xcworkspace/
.build/

# System & editor
.DS_Store
*.swp
.vscode/
.idea/

# Fastlane / local credentials
fastlane/report.xml
fastlane/Preview.html
fastlane/test_output
*.p12
*.mobileprovision
```

Must **not ignore**: `Podfile.lock`, `Package.resolved`, `*.xcodeproj/project.pbxproj`, `*.xcworkspace/contents.xcworkspacedata`, shared schemes (`*.xcodeproj/xcshareddata/xcschemes/`).

## Common Anti-Patterns
- Pushing pbxproj conflicts without local build; CI goes red for everyone.
- Hand-merging storyboard XML; looks correct but crashes at runtime.
- `Pods/` neither ignored nor fully committed; causes pointless diffs after team members' local `pod install`.
- Hotfix cut directly from `main` HEAD (bringing unreleased dirty changes); pollutes mainline after merge.
- `git push --force` on shared branch; disrupts others' local working trees.
- Single commit changing both pbxproj and business source; painful to revert.
- `Package.resolved` not committed; CI and local versions drift.
- Xcode version upgrade mixed with business changes in same PR; can only roll back everything together.

# Controlled publishing failure checks

Run these after the normal maintained and four-platform native publications
have succeeded. These two workflow runs are **expected to fail**. Acceptance
means they fail at the intended check and their publication/verification jobs
are skipped. An unrelated download, compiler setup or runner error does not
establish the intended result.

These commands create new test tags. The Windows check also creates a local
branch and commit in a separate worktree. They do not replace the published
`native-release-check/v0.1.0` tag or change the main checkout's source. Do not
merge the deliberately broken test commit into main. No publication or model
credentials are needed in your terminal.

## Prepare your terminal

Use an examples checkout whose `origin` is your configured GitHub repository,
with the normal publishing workflows already merged. Use AgentPM CLI 0.1.42 or
a later compatible version. From the repository root, in Bash or zsh:

```bash
export M16_FAILURE_REPO="$PWD"
export M16_FAILURE_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/agentpm-publish-failures.XXXXXX")"
export M16_FAILURE_RUN="$(date -u +%Y%m%d%H%M%S)-$$"
git fetch origin main
```

Keep this terminal open for both checks. The timestamp/process suffix gives
each attempt distinct tag, branch and prerelease-version names.

## 1. Tag version does not match the manifest

Tag the unmodified main commit with an intentionally mismatched version:

```bash
export M16_MISMATCH_TAG="native-release-check/v0.0.0-ci-mismatch.$M16_FAILURE_RUN"
git tag "$M16_MISMATCH_TAG" origin/main
git push origin "refs/tags/$M16_MISMATCH_TAG"
```

Open **Actions → Publish native release example** and select this test tag's run.

Expected:

- `select` fails with `Release tag does not match the selected agent.json name/version`.
- All four build jobs, `publish` and all verification jobs are skipped.
- No test version is published to the Registry.

Record the workflow URL, tested commit and the selection error. A failure in a
later step is not the expected result. Do not rerun this tag expecting success;
it is deliberately invalid.

## 2. A required Windows build fails

Create an isolated checkout from the same main commit:

```bash
git worktree add -b "ci-checks/native-failure-$M16_FAILURE_RUN" \
  "$M16_FAILURE_ROOT/windows-failure" origin/main
cd "$M16_FAILURE_ROOT/windows-failure"
export M16_FAILURE_VERSION="0.0.0-ci-windows-failure.$M16_FAILURE_RUN"
export M16_FAILURE_TAG="native-release-check/v$M16_FAILURE_VERSION"
```

Change only the test version and prepend a Windows-only C compilation error.
The workflow file, required matrix and publication conditions stay unchanged:

```bash
python3 - <<'PY'
import json
import os
from pathlib import Path

root = Path("publishing/native-release-check")
manifest_path = root / "agent.json"
manifest = json.loads(manifest_path.read_text())
manifest["version"] = os.environ["M16_FAILURE_VERSION"]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

source_path = root / "helper.c"
source_path.write_text(
    '#ifdef _WIN32\n#error "Controlled publishing failure: required Windows build"\n#endif\n'
    + source_path.read_text()
)
PY

(cd publishing/native-release-check && agentpm lint --strict)
git diff -- publishing/native-release-check/agent.json publishing/native-release-check/helper.c
```

Review that the diff contains only those two test inputs, then commit and push
the new test tag. The tag makes this test commit available to GitHub without
pushing or merging the local test branch:

```bash
git add publishing/native-release-check/agent.json publishing/native-release-check/helper.c
git commit -m "Test that required Windows build failure blocks publication"
git tag "$M16_FAILURE_TAG"
git push origin "refs/tags/$M16_FAILURE_TAG"
```

Open the new **Publish native release example** run.

Expected:

- `select` passes: this tag matches the test manifest version.
- Apple Silicon macOS, Intel macOS and Linux builds pass and upload bundles.
- Windows compilation fails with `Controlled publishing failure: required Windows build`.
- `publish` is skipped because its required build matrix failed, even though
  three bundles exist. All consumer verification jobs are skipped.
- No version named by `M16_FAILURE_VERSION` is published; the existing 0.1.0
  release and its four artifact digests remain unchanged.

This exercises the normal `needs: [select, build]` dependency using an actual
failed native compiler job. It does not remove Windows from the matrix, force
publication, or weaken signature/attestation verification. The local CLI tests
separately cover missing descriptors and incomplete required target sets.

Record the workflow URL, tested commit, all four build conclusions, the Windows
compiler error and the skipped publish/verify jobs. On the package's Versions
page, confirm the test version is absent. Return to your original checkout:

```bash
cd "$M16_FAILURE_REPO"
```

Keep the expected failed runs/tags as evidence. Do not retag a published version
to clean up these tests. The local worktree can remain until evidence is
recorded; it does not affect main or the existing release.

## Completion evidence

Retain the three successful publication run URLs and exact versions, their
clean-consumer verification results, and both expected failed run URLs. Include
logical release digests and per-target artifact digests where the new release
format applies. Confirm the published README/Security views and the final
artifact scan results separately; a queued scan is not a clean scan result.

Settings and successful publication commands are in the
[publishing guide](README.md). These failure checks require no production
policy changes, new package version publication or deliberately failed code
merged into main.

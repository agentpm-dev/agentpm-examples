# Publishing from GitHub Actions

Two independent maintained examples live in this repository:

| Package | Directory | Release tag | Publication |
| --- | --- | --- | --- |
| summarize-text | tools-python/summarize-text | `summarize-text/v<version>` | Python release with one portable `any` artifact |
| devwork-copilot | agent-packages/devwork-python | `devwork-copilot/v<version>` | One legacy Agent artifact |

`publish-examples.yml` selects only the tagged package, checks its manifest
version, packages without Registry credentials, then signs/publishes in a
separate job. Publishing the Agent does not publish its Tools or change their
versions. Both workflows retain normal manual `agentpm publish` support.

A separate `native-release-check/v<version>` tag runs
`publish-native-example.yml`: four native runners compile a small C helper,
package their concrete-target payloads, and upload build bundles. One final job
requires all four builds and performs one atomic release publication. Native
Python dependencies do not make summarize-text's own source archive native.

The native release matrix is Apple Silicon macOS (`aarch64-apple-darwin`), Intel
macOS (`x86_64-apple-darwin`), Linux x86-64 (`x86_64-unknown-linux-gnu`) and Windows
x64 (`x86_64-pc-windows-msvc`). A missing or failed Windows build blocks the same
final publication as any other required target. The installer verifies the CLI
release checksum before extracting Unix `.tar.gz` or Windows `.zip` assets,
then adds the native executable directory to PATH.

## Setup

Use a released CLI that supports `agentpm package`, `publish --build` and
`--key-file`. CLI 0.1.40 predates these commands. Set repository variables:

- `AGENTPM_CLI_VERSION`: the exact compatible published CLI version, without `v`.
  The setup action downloads that version and verifies its release checksum.
- `AGENTPM_NAMESPACE`: a namespace you may publish into, without `@`.
- `AGENTPM_REGISTRY_URL`: the destination Registry origin. Production is
  `https://api.agentpackagemanager.com`. A development Registry must be reachable
  from hosted runners and have a CLI-trusted signing root; localhost on your
  computer is not reachable from GitHub.

Create a GitHub environment named `agentpm-publishing`, restrict it to your
intended release tags, and configure required reviewers if you want approval
before publication. Put these secrets in that environment:

- `AGENTPM_TOKEN`: a PAT with `packages:publish` for the chosen namespace.
- `AGENTPM_SIGNING_KEY_JSON`: the **encrypted StoredKeyV1 JSON** for an author
  key registered as an active trusted namespace signer. Use `agentpm keys list`
  to locate your encrypted local key record. Do not supply an unencrypted seed
  or the offline Registry root key.
- `AGENTPM_KEY_PASSPHRASE`: its passphrase, stored separately.
- `OPENAI_API_KEY`: needed only for summarize-text's successful post-publication
  verification. That small real call incurs provider usage. Registry signing
  and the native fixture do not need model credentials.

The public namespace must be installable by the verification jobs. Build jobs
receive no Registry/signing/model secrets. Publication materializes the encrypted
key in a private temporary file and removes it when the job exits. Never turn
on shell tracing around secrets. AgentPM OIDC/keyless trusted publishing remains
future work; these examples use a PAT.

## Prepare a maintained release

Update only the intended package's `agent.json.version` (and corresponding
project metadata where applicable). For summarize-text, prepare/review/commit
`agent.lock` before CI; CI replays it and does not refresh dependencies:

```bash
cd tools-python/summarize-text
agentpm publish --dry-run --refresh-python
agentpm lint --strict
```

Review and commit the source, version and lock changes, then push a tag matching
that version. For example, after preparing version `0.1.10`:

```bash
git tag summarize-text/v0.1.10
git push origin summarize-text/v0.1.10
```

That command publishes a real version after the environment permits it. Existing
published versions cannot be replaced; do not tag an unchanged already-published
version. An Agent release uses `devwork-copilot/v<agent-version>` independently.

## What the workflows verify

The build bundle contains an archive and `package-build.json`. Keep them together
when moving outputs between runners. CI validates archive hashes, embedded
manifest/Python metadata, package identity, required build hosts and unique
artifact targets before publication. A missing/failed target prevents the final
job from running. Mixed `any`/concrete matrix claims fail with the contributing
file diagnostics; correct permissions or packaging inputs and rebuild instead
of silently dropping or relabeling outputs.

After publication, a new consumer installs the exact version with
`--require-signature --require-attestation`. The summarizer performs a real Tool
call using managed dependencies. The Agent check verifies its exact installed
version and declared Tool versions without an SDK or model-driven Agent run.
The native fixture installs and executes its compiled helper on all four
supported example runner targets.

A failed verification job does **not** undo an already-finalized publication.
Inspect the failure and publish a corrected new version if necessary. Keep run
links and exact versions as release evidence. Workflow definitions and local
fixture tests alone are not evidence of a successful hosted publication.

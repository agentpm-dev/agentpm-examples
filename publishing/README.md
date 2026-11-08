# Publishing from GitHub Actions

Two independent maintained examples live in this repository:

| Package         | Directory                     | Release tag                  | Publication                                     |
| --------------- | ----------------------------- | ---------------------------- | ----------------------------------------------- |
| summarize-text  | tools-python/summarize-text   | `summarize-text/v<version>`  | Python release with one portable `any` artifact |
| devwork-copilot | agent-packages/devwork-python | `devwork-copilot/v<version>` | One legacy Agent artifact                       |

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

Use released CLI **0.1.41** or a later compatible version supporting
`agentpm package`, `publish --build` and `--key-file`. CLI 0.1.40 predates these
commands. The following setup configures real production publication, but does
not trigger a release. Configure GitHub before pushing any release tag.

### 1. Enable the workflows

Open the [examples repository](https://github.com/agentpm-dev/agentpm-examples).
Make sure the publishing workflows, local setup action and scripts have been
merged into the commit you will tag. Under **Settings → Actions → General**,
ensure the repository's Actions policy permits the actions referenced by the
workflows. They request only `contents: read`; no write-enabled GitHub token or
GitHub PAT is needed for these public repository downloads. An organization
allowlist must permit the referenced `actions/*`, `astral-sh/setup-uv` and the
repository's local setup action.

### 2. Add repository variables

Go to **Settings → Secrets and variables → Actions → Variables**, then use
**New repository variable** for each row:

| Name                   | Production example value                                  |
| ---------------------- | --------------------------------------------------------- |
| `AGENTPM_CLI_VERSION`  | `0.1.41` (no leading `v`)                                 |
| `AGENTPM_NAMESPACE`    | `zack` (no leading `@`; use your own namespace in a fork) |
| `AGENTPM_REGISTRY_URL` | `https://api.agentpackagemanager.com`                     |

Keep these at **repository scope**, because selection and build jobs need them
before entering the publishing environment. The setup action downloads the
exact CLI version and verifies its release checksum. A development Registry
must be reachable from hosted runners and have a CLI-trusted signing root;
localhost on your computer is not reachable from GitHub.

### 3. Create the publishing environment

Go to **Settings → Environments → New environment**, name it exactly
`agentpm-publishing`, then click **Configure environment**. If it already exists,
edit it. Under **Deployment branches and tags**, select **Selected branches and
tags**. Add these three rules, choosing **Tag** as the ref type for each:

```text
summarize-text/v*
devwork-copilot/v*
native-release-check/v*
```

Do not choose branch rules or restrict the environment to `main` alone: these
workflows run from tags. Optionally add yourself as a **Required reviewer**
where your GitHub plan supports it. If you are the only approver and trigger
the release yourself, leave **Prevent self-review** unchecked. Both `publish`
and `verify` jobs use this environment, so either may wait for approval. Approve
waiting jobs from the workflow run's **Review deployments** control.

### 4. Add environment secrets

Inside **Settings → Environments → agentpm-publishing**, use **Add environment
secret** for each row. Store these here rather than as repository variables:

| Name                       | Value to paste                                                                                                                                                                                                                              |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AGENTPM_TOKEN`            | An **AgentPM** Personal Access Token with `packages:publish`, belonging to an account allowed to publish in the selected namespace. Create/copy one from your AgentPM profile's Personal access tokens section. This is not GitHub's token. |
| `AGENTPM_SIGNING_KEY_JSON` | The entire existing **encrypted StoredKeyV1 JSON file** for an author key registered as an active trusted signer in that namespace. Include its outer braces and all fields.                                                                |
| `AGENTPM_KEY_PASSPHRASE`   | The passphrase that decrypts that author key, stored separately from the JSON.                                                                                                                                                              |
| `OPENAI_API_KEY`           | An OpenAI API key for summarize-text's successful post-publication verification. This real Tool call incurs provider usage; Agent installation checks and the native fixture do not need it.                                                |

To choose an existing author key locally:

```bash
agentpm keys list
```

This lists key IDs, labels and creation times, not their filesystem paths. On
macOS, the encrypted record for `<KEY_ID>` is at
`~/Library/Application Support/com.agentpm.AgentPM/keys/<KEY_ID>.json`.
For example, after replacing the placeholder, this copies the complete file
directly to the clipboard for the GitHub secret form without printing it:

```bash
pbcopy < "$HOME/Library/Application Support/com.agentpm.AgentPM/keys/<KEY_ID>.json"
```

Reuse a currently trusted author key if you have one. For a new key, run
`agentpm keys generate --label "GitHub publishing"`; it prints the saved path
on your platform. Export **only its public key** and register it before using
the encrypted record in CI:

```bash
agentpm keys export --key-id <KEY_ID> --out author-public-key.txt
agentpm --base-url https://api.agentpackagemanager.com namespace add-signer \
  --namespace your-namespace --label "GitHub publishing" --pubkey author-public-key.txt
```

`keys export` produces public registration material, not the encrypted JSON
needed by `AGENTPM_SIGNING_KEY_JSON`. Do not use an unencrypted seed, the
Registry attestation private key, or the offline Registry root key. Keep the
encrypted file and passphrase out of commits, workflow YAML and logs.

### 5. Check setup before tagging

Confirm that all three repository variables, the environment's three **tag**
rules and the four environment secret names are present. An empty secret or
untrusted/revoked author key will prevent a successful signed publication.
These workflows have tag triggers, not a manual **Run workflow** button; merging
the files or saving settings alone does not publish anything. The PR workflow
`Publishing example contracts` runs fixture checks without these secrets.

Only after preparing a new package version as described below should you push
its matching release tag. Then watch **Actions → Publish maintained examples**
or **Actions → Publish native release example**, approve any environment waits,
and check both publication and all clean-consumer verification jobs.

For GitHub's current UI and plan-specific environment availability, see
[repository variables](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-variables)
and [environments and secrets](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments).

The public namespace must be installable by the verification jobs. Build jobs
receive no Registry/signing/model secrets. Publication materializes the encrypted
key in a private temporary file and removes it when the job exits. Never turn
on shell tracing around secrets. AgentPM OIDC/keyless trusted publishing remains
future work; these examples use a PAT.

## Prepare a maintained release

The next prepared versions are `summarize-text` **0.1.10** and
`devwork-copilot` **0.1.8**, which pins `@zack/summarize-text@0.1.10`.
Publish and verify the Tool first, then publish the Agent. The native example
starts at **0.1.0** and can be published independently after its source is merged.
Existing consumer workspace locks are updated by a real install after
publication, not by substituting version strings in their installed records.

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
After the Tool workflow's publication and verification jobs pass, release the
prepared Agent version:

```bash
git tag devwork-copilot/v0.1.8
git push origin devwork-copilot/v0.1.8
```

The four-platform native example has its own tag:

```bash
git tag native-release-check/v0.1.0
git push origin native-release-check/v0.1.0
```

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

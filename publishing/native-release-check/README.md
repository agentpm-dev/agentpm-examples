# Native release check

This small publication fixture compiles a C helper on each native runner. Its
Python entrypoint invokes that helper and returns the input integer plus one.
The compiled helper makes each payload target-specific; no target is relabeled.

For a local build, using a CLI with `agentpm package` support:

```bash
python build.py
agentpm lint --strict
agentpm package --machine
```

The `publish-native-example.yml` workflow builds Apple Silicon macOS, Intel
macOS, Linux x86-64 and Windows x64 from one tag, then publishes one complete
signed release.
See [publishing setup](https://github.com/agentpm-dev/agentpm-examples/tree/main/publishing) before creating a release tag. This fixture
is independent of the two maintained package examples.

`build.py` uses `cc` on macOS/Linux and locates the x64 MSVC Build Tools with
Visual Studio's `vswhere.exe` on Windows; see the
[MSVC command-line setup guide](https://learn.microsoft.com/en-us/cpp/build/building-on-the-command-line?view=msvc-170). The Windows build initializes
`vcvars64.bat` and links the C runtime statically (`/MT`); the consumer does not
need a compiler or a separate Visual C++ runtime installation for this helper.
Use Python 3.11+ to build locally; GitHub's Windows runner supplies MSVC.

Every runner packages the same manifest, whose `files` list includes `bin/`.
Only its compiled `bin/native-helper` (Unix) or `bin/native-helper.exe` (Windows)
is placed there; object files remain in temporary storage. The Python entrypoint
selects the platform's filename. All four build outputs are required before
publication, and each platform then performs a strict install and executes its
own selected artifact in a clean consumer. Linux arm64 is not included.

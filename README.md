# PT RNG Lab

A read-only Windows RNG monitor, browser-based shiny legendary predictor, and Journal walkthrough for Platinum Together.

**[Open the guide + predictor + monitor download](https://dr4lera.github.io/platinum-together-rng/)**

The monitor reads your game locally. You explicitly copy a snapshot into the website. Calculations happen in a browser worker; there is no account, snapshot upload, analytics, local server, automatic gameplay input, injection, memory-write API, or save-file access.

## Use

1. Download `PT-RNG-Monitor-Windows.zip` from the page or [latest release](https://github.com/dr4lera/platinum-together-rng/releases/latest).
2. Extract it and run `PT-RNG-Monitor.exe` on Windows x64. Load exactly one game and click **Connect**.
3. Save before interacting with your legendary. Open the Journal, then click **Copy snapshot**.
4. Paste into the page, import it, select the encounter mode, and search.
5. Copy a result using **Track in monitor**, then click **Paste target from predictor** in the monitor.
6. Advance with ordinary Journal inputs. Measure both page directions; some pages give zero, not two. At target, close menus and confirm zero again before interacting.
7. Verify the actual Pokémon and save through the game's normal UI. For roamers, check the generated-roamer table after release.

The tool exposes hidden state. Whether that fits a challenge or community's rules is up to that community. It does not promise every seed or location follows one generation method.

## Compatibility and evidence

Full SHA-256 checks, not version strings alone, select the memory profile.

| Executable | Memory reads | Encounter target evidence |
| --- | --- | --- |
| 0.1.12, SHA-256 `94b851a80c166329d62a410e2374d79b5e8dddfe2c5b4ae24b13a3e9f805c810` | Verified in the original read-only hunt scripts | Repeated natural shiny stationary encounters, Cresselia/Mesprit releases, and an initial three-bird release matched predictions |
| 0.1.13, SHA-256 `863322cad34fef3b1073fb200de92b407e07eb1c53a1d0153fd0b3873fea4949` | Standalone monitor reads verified against the running game | Experimental until fresh encounter calibration; live seed/IDs/lead/roamer layout verification does not establish every encounter model |
| Other builds | Refused | No guesses or fallback scans |

Historical stationary calibration: Uxie, Azelf, Dialga, Palkia, Heatran, Reshiram, Victini, Xerneas, Yveltal and Zekrom. These used Method J, no Synchronize, and zero pre-generation calls. Synchronize arithmetic is implemented, but a native Synchronize hunt has not been independently verified here. Giratina is not validated by this public release.

Cresselia and Mesprit first releases used four pre-generation calls followed by two PID words and two IV words. Oak's birds consume four generation calls per released bird, followed by native route rejection using division by 2260. Re-release predictions use the snapshot's reset states and old route indices, but await an end-to-end re-release test. Different areas, NPC activity, scripts, and menu transitions can add RNG calls. Stop and recalibrate on a mismatch.

**Starters are not supported by this predictor.** Static inspection of 0.1.13 supports normal shiny starters and cached starter identities, but the timing of starter selection needs a separate workflow.

## Run from source

Windows x64, Python 3.11+ x64, standard library only:

```powershell
python monitor/main.py
python monitor/main.py --snapshot
```

The second command prints one snapshot to stdout. It does not write a file. Do not publish its trainer IDs unless you intend to share them.

Preview the website:

```powershell
python serve.py
```

Open `http://127.0.0.1:8765`. ES modules/workers need HTTP(S), not a `file://` URL.

## Tests and Windows packaging

Python 3.11+ and Node 20+:

```powershell
python -m unittest discover -s tests
node --test tests/rng.test.mjs
```

To build the portable ZIP on Windows:

```powershell
python -m pip install -r requirements-build.txt
python package.py
```

Artifacts go to the ignored `artifacts/` directory. The executable is unsigned. Packaging includes CPython, Tcl/Tk and PyInstaller runtime components under their respective licenses; their installed license texts are included in the ZIP. The tool's own code is MIT licensed. No game files are bundled.

## Project layout

- `monitor/`: stdlib-only reader, deterministic RNG arithmetic, and Tk UI.
- `docs/`: static website, JavaScript predictor, and worker.
- `tests/`: golden vectors, cross-language comparison, distance and validation checks.
- `.github/workflows/`: Pages deployment and Windows build checks.

GitHub Pages serves `docs/` through Actions. Monitor downloads link to GitHub release assets on the same project. No permission documents, decompiled functions, game resources, saves, live snapshots, private research, credentials, or user-specific paths belong in this repository.

## Credits

Community tooling by dr4lera, built with OpenAI Codex assistance. RNG models and interoperability offsets were investigated from the user's installed executable and read-only observations. This is an unofficial tool; no affiliation with Nintendo, Game Freak, The Pokémon Company, or Platinum Together's authors is claimed. No game art or audio is included.

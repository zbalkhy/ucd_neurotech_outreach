# Repository Guidelines

## Project Structure & Module Organization

This repository contains a Python/Tkinter application for UC Davis neurotechnology outreach: EEG acquisition, visualization, filtering, classification, and brain-controlled games.

- `src/main.py` launches the application. `View/`, `ViewModel/`, and `Models/` separate widgets, UI coordination, and application state.
- `src/Stream/` implements data sources and processing streams; `src/Classes/` contains filters, features, classifiers, and shared utilities; `src/b2bci/` handles device communication.
- `src/Game/` contains games; `src/Tests/` contains automated tests.
- `src/assets/`, `src/data.mat`, and `data/` hold UI assets and sample EEG data.
- `demo/`, `prototyping/`, and `esp_code/` contain demonstrations, experiments, and firmware. Keep production changes in `src/`.

## Build, Test, and Development Commands

Run setup and build commands from the repository root:

```sh
python3.12 -m venv outreach_env
source outreach_env/bin/activate
python -m pip install -r requirements.txt
python src/main.py
python build_app.py
```

On Windows, activate with `outreach_env\Scripts\activate`. Tkinter must be available; Ubuntu uses `python3-tk`. The build script reuses `outreach_env` when present and writes `dist/B2BCI_APP*`; add `--console` for debugging. Build CI uses Python 3.12, while test CI currently specifies 3.11.

## Coding Style & Naming Conventions

Use four-space indentation, snake_case functions and variables, and uppercase constants. Prefer PascalCase for new classes, while preserving existing public names. Match neighboring module filenames, such as `filterViewModel.py` and `b2bciStream.py`; avoid unrelated renaming. Keep widget logic in views and signal processing in streams or shared classes.

Run `python -m pycodestyle src build_app.py --ignore=E501`. CI uses pycodestyle with line-length warnings disabled; no automatic formatter is configured.

## Testing Guidelines

From `src/`, run `python -m pytest Tests/ --doctest-modules` and `python -m unittest`, matching CI. On headless Linux, prefix GUI-dependent commands with `xvfb-run -a`.

Use `test_*.py` or `*_test.py` filenames and `test_*` functions. Mock serial hardware as in `b2bci_stream_test.py`. No coverage threshold is configured. Keep automated discovery scoped to `Tests/`: `Game/test_week1_game.py` launches an interactive demo.

Back up session data before testing: `save_test.py` deletes `user_save.json` and `user_classifiers/` relative to the working directory.

## Commit & Pull Request Guidelines

History uses short, descriptive subjects without a consistent prefix convention. Use focused, imperative summaries such as `Fix B2BCI stream buffering`. PRs should describe behavior changes, link related issues, list validation performed, and include screenshots for UI changes. Exclude generated bundles, environments, and incidental session-data changes.

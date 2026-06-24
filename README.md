# Weiqi Tournament Pairing

Open-source tournament pairing software for Weiqi/Go and related board games.

The first prototype is a correctness-first Python CLI that stores tournaments as `.tgo.json` files and imports players from CSV.

Stage 4 adds a local web console for the current tournament workflow, including players, pairings, results, standings, exports, and a public display page.

## Stage 1 Commands

Create a tournament:

```powershell
$env:PYTHONPATH = "src"; python -m pairing.cli.main create example.tgo.json --name "Example Weiqi Open" --rounds 5
```

Import players:

```powershell
$env:PYTHONPATH = "src"; python -m pairing.cli.main import-players example.tgo.json players.csv
```

Start the local web console:

```powershell
$env:PYTHONPATH = "src"; python -m pairing.cli.main web example.tgo.json --port 8000
```

## Documentation

- [Design spec](docs/superpowers/specs/2026-06-22-weiqi-tournament-design.md)
- [CSV player import format](docs/csv-format.md)
- [Tournament file format](docs/tournament-file-format.md)

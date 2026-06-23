# Weiqi Tournament Pairing

Open-source tournament pairing software for Weiqi/Go and related board games.

The first prototype is a correctness-first Python CLI that stores tournaments as `.tgo.json` files and imports players from CSV.

## Stage 1 Commands

Create a tournament:

```powershell
$env:PYTHONPATH = "src"; python -m pairing.cli.main create example.tgo.json --name "Example Weiqi Open" --rounds 5
```

Import players:

```powershell
$env:PYTHONPATH = "src"; python -m pairing.cli.main import-players example.tgo.json players.csv
```

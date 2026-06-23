from pairing.import_export.csv_import import import_players_from_csv_text


def test_import_players_from_csv_text():
    csv_text = "name,rank,country,club,school,team,notes\nAlice,3d,SG,Club A,School A,,Captain\nBob,5k,SG,Club B,School B,,\n"

    report = import_players_from_csv_text(csv_text)

    assert report.valid
    assert len(report.players) == 2
    assert report.players[0].display_name == "Alice"
    assert report.players[0].rank == "3d"
    assert report.players[1].rank_sort_value == -5
    assert report.warnings == []


def test_import_reports_missing_name_and_invalid_rank():
    csv_text = "name,rank\n,3d\nCharlie,35k\n"

    report = import_players_from_csv_text(csv_text)

    assert not report.valid
    assert len(report.players) == 0
    assert "Row 2: missing player name." in report.errors
    assert "Row 3: Invalid kyu rank: 35k" in report.errors


def test_import_warns_about_unknown_columns_and_duplicate_names():
    csv_text = "name,rank,extra\nAlice,1d,ignored\nAlice,2d,ignored\n"

    report = import_players_from_csv_text(csv_text)

    assert report.valid
    assert len(report.players) == 2
    assert "Unknown columns ignored: extra." in report.warnings
    assert "Duplicate player name imported: Alice." in report.warnings

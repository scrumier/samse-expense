import pandas as pd
from expense.analyzer import detect_anomalies


def make_df(rows):
    return pd.DataFrame(rows)


def test_detect_large_amount():
    rows = [
        {"date": pd.Timestamp("2025-01-10"), "montant": 100.0, "fournisseur": "A", "categorie": "X", "description": "ok"},
        {"date": pd.Timestamp("2025-01-11"), "montant": 100.0, "fournisseur": "B", "categorie": "X", "description": "ok"},
        {"date": pd.Timestamp("2025-01-12"), "montant": 50000.0, "fournisseur": "INCONNU", "categorie": "X", "description": "mystery"},
    ]
    df = make_df(rows)
    anomalies = detect_anomalies(df)
    large = [a for a in anomalies if a["type"] == "montant_eleve"]
    assert len(large) == 1
    assert large[0]["montant"] == 50000.0


def test_detect_duplicate():
    rows = [
        {"date": pd.Timestamp("2025-03-10"), "montant": 847.5, "fournisseur": "Bureau Vallee", "categorie": "F", "description": "Q1"},
        {"date": pd.Timestamp("2025-03-12"), "montant": 847.5, "fournisseur": "Bureau Vallee", "categorie": "F", "description": "Q1"},
        {"date": pd.Timestamp("2025-04-01"), "montant": 200.0, "fournisseur": "Acme", "categorie": "F", "description": "ok"},
    ]
    df = make_df(rows)
    anomalies = detect_anomalies(df)
    dups = [a for a in anomalies if a["type"] == "doublon"]
    assert len(dups) >= 1


def test_no_anomalies_on_clean_data():
    # weekdays only, amounts well below 20 000 EUR, no duplicates
    rows = [
        {"date": pd.Timestamp(f"2025-02-{i:02d}"), "montant": float(100 + i), "fournisseur": "A", "categorie": "X", "description": "ok"}
        for i in range(3, 22)  # 2025-02-03 (Monday) to 2025-02-21 (Friday)
        if pd.Timestamp(f"2025-02-{i:02d}").dayofweek < 5
    ]
    df = make_df(rows)
    anomalies = detect_anomalies(df)
    assert anomalies == []

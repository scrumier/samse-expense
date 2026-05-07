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
    anomalies = detect_anomalies(df, absolute_threshold=20_000)
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


def test_isolation_forest_flags_outlier():
    # 18 transactions normales + 1 énorme outlier
    rows = [
        {"date": pd.Timestamp(f"2025-02-{i:02d}"), "montant": float(100 + i * 2), "fournisseur": "A", "categorie": "X", "description": "ok"}
        for i in range(3, 21)
        if pd.Timestamp(f"2025-02-{i:02d}").dayofweek < 5
    ]
    rows.append({
        "date": pd.Timestamp("2025-03-03"),
        "montant": 95000.0,
        "fournisseur": "INCONNU SARL",
        "categorie": "X",
        "description": "mystere",
    })
    df = make_df(rows)
    anomalies = detect_anomalies(df, absolute_threshold=200_000)  # seuil haut pour forcer IF
    ml = [a for a in anomalies if a["type"] == "pattern_ml"]
    # L'outlier à 95000 doit être dans les anomalies ML
    flagged_amounts = [a["montant"] for a in ml]
    assert 95000.0 in flagged_amounts

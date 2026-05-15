import pandas as pd
from pathlib import Path

REQUIRED_COLUMNS = {"date", "montant", "fournisseur", "categorie", "description", "statut"}
OPTIONAL_COLUMNS = {"employe", "centre_cout"}


def load_csv(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Fichier introuvable: {path}")
    df = pd.read_csv(p)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"colonnes manquantes: {', '.join(missing)}")
    df["date"] = pd.to_datetime(df["date"])
    df["montant"] = pd.to_numeric(df["montant"], errors="coerce")
    df = df.dropna(subset=["montant", "date"])
    return df

import pytest
import pandas as pd
import tempfile
import os
from expense.loader import load_csv


def test_load_valid_csv():
    content = "date,montant,fournisseur,categorie,description,statut\n2025-01-15,234.50,Acme,Fournitures,Test,valide\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(content)
        path = f.name
    df = load_csv(path)
    os.unlink(path)
    assert len(df) == 1
    assert df.iloc[0]["montant"] == 234.50
    assert pd.api.types.is_datetime64_any_dtype(df["date"])


def test_load_missing_column():
    content = "date,montant,fournisseur\n2025-01-15,100,Acme\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(content)
        path = f.name
    with pytest.raises(ValueError, match="colonnes manquantes"):
        load_csv(path)
    os.unlink(path)


def test_load_nonexistent_file():
    with pytest.raises(FileNotFoundError):
        load_csv("/nonexistent/path.csv")

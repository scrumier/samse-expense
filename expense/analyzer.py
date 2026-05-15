import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


# ── Détection par règles ─────────────────────────────────────────────────────

def _detect_rules(df: pd.DataFrame, absolute_threshold: float, duplicate_window_days: int) -> list[dict]:
    anomalies = []

    # Seuil absolu configurable
    for _, row in df[df["montant"] >= absolute_threshold].iterrows():
        anomalies.append({
            "type": "montant_eleve",
            "date": str(row["date"].date()),
            "montant": row["montant"],
            "fournisseur": row["fournisseur"],
            "categorie": row["categorie"],
            "description": row.get("description", ""),
            "employe": row.get("employe", ""),
            "centre_cout": row.get("centre_cout", ""),
            "detail": f"Montant >= seuil {absolute_threshold:,.0f} EUR",
            "score": None,
        })

    # Doublons (même fournisseur + même montant dans la fenêtre)
    df_sorted = df.sort_values("date").reset_index(drop=True)
    seen = set()
    for i, row in df_sorted.iterrows():
        key = (row["fournisseur"], row["montant"])
        if key in seen:
            continue
        same = df_sorted[
            (df_sorted["fournisseur"] == row["fournisseur"]) &
            (df_sorted["montant"] == row["montant"]) &
            (abs((df_sorted["date"] - row["date"]).dt.days) <= duplicate_window_days) &
            (df_sorted.index != i)
        ]
        if not same.empty:
            seen.add(key)
            anomalies.append({
                "type": "doublon",
                "date": str(row["date"].date()),
                "montant": row["montant"],
                "fournisseur": row["fournisseur"],
                "categorie": row["categorie"],
                "description": row.get("description", ""),
                "employe": row.get("employe", ""),
                "centre_cout": row.get("centre_cout", ""),
                "detail": f"Transaction identique le {same.iloc[0]['date'].date()} ({duplicate_window_days}j)",
                "score": None,
            })

    return anomalies


# ── Détection par Isolation Forest ──────────────────────────────────────────

def _build_features(df: pd.DataFrame) -> pd.DataFrame:
    feat = pd.DataFrame(index=df.index)
    feat["montant_log"] = np.log1p(df["montant"])
    feat["jour_semaine"] = df["date"].dt.dayofweek
    feat["mois"] = df["date"].dt.month
    feat["is_weekend"] = (df["date"].dt.dayofweek >= 5).astype(int)
    feat["montant_rond_1000"] = (df["montant"] % 1000 == 0).astype(int)

    # Ratio montant vs moyenne de la catégorie
    cat_mean = df.groupby("categorie")["montant"].transform("mean")
    feat["ratio_cat"] = df["montant"] / cat_mean.replace(0, 1)

    # Fréquence du fournisseur (fournisseur rare = plus suspect)
    supplier_freq = df["fournisseur"].map(df["fournisseur"].value_counts())
    feat["supplier_freq"] = supplier_freq

    return feat.fillna(0)


def _explain_anomaly(row: pd.Series, feat_row: pd.Series, df: pd.DataFrame) -> str:
    reasons = []
    cat_mean = df[df["categorie"] == row["categorie"]]["montant"].mean()
    if feat_row["ratio_cat"] > 3:
        reasons.append(f"montant {feat_row['ratio_cat']:.1f}x la moyenne de la categorie ({cat_mean:.0f} EUR)")
    if feat_row["is_weekend"]:
        reasons.append("transaction le weekend")
    if feat_row["montant_rond_1000"]:
        reasons.append("montant rond multiple de 1000")
    if feat_row["supplier_freq"] <= 2:
        reasons.append(f"fournisseur peu frequent ({int(feat_row['supplier_freq'])} occurrence(s))")
    return " + ".join(reasons) if reasons else "pattern inhabituel detecte par le modele"


def _detect_isolation_forest(df: pd.DataFrame, contamination: float) -> list[dict]:
    if len(df) < 10:
        return []

    feat = _build_features(df)
    X = StandardScaler().fit_transform(feat)

    model = IsolationForest(contamination=contamination, random_state=42, n_estimators=100)
    labels = model.fit_predict(X)
    raw_scores = model.score_samples(X)

    # Normalise le score anomalie entre 0 et 1 (1 = plus anormal)
    min_s, max_s = raw_scores.min(), raw_scores.max()
    norm_scores = 1 - (raw_scores - min_s) / (max_s - min_s + 1e-9)

    anomalies = []
    for idx in np.where(labels == -1)[0]:
        row = df.iloc[idx]
        feat_row = feat.iloc[idx]
        score = round(float(norm_scores[idx]), 3)
        anomalies.append({
            "type": "pattern_ml",
            "date": str(row["date"].date()),
            "montant": row["montant"],
            "fournisseur": row["fournisseur"],
            "categorie": row["categorie"],
            "description": row.get("description", ""),
            "employe": row.get("employe", ""),
            "centre_cout": row.get("centre_cout", ""),
            "detail": _explain_anomaly(row, feat_row, df),
            "score": score,
        })

    anomalies.sort(key=lambda x: -x["score"])
    return anomalies


# ── Interface publique ───────────────────────────────────────────────────────

def detect_anomalies(
    df: pd.DataFrame,
    absolute_threshold: float = 20_000.0,
    duplicate_window_days: int = 5,
    contamination: float = 0.08,
) -> list[dict]:
    rules = _detect_rules(df, absolute_threshold, duplicate_window_days)
    ml = _detect_isolation_forest(df, contamination)

    # Dédoublonnage: si une transaction est déjà flaggée par les règles, on enrichit plutôt qu'on duplique
    rule_keys = {(a["date"], a["fournisseur"], a["montant"]) for a in rules}
    ml_unique = [a for a in ml if (a["date"], a["fournisseur"], a["montant"]) not in rule_keys]

    return rules + ml_unique


def summarize(df: pd.DataFrame) -> dict:
    s = {
        "total_lignes": len(df),
        "total_depenses": round(df["montant"].sum(), 2),
        "periode": f"{df['date'].min().date()} - {df['date'].max().date()}",
        "par_categorie": df.groupby("categorie")["montant"].sum().round(2).to_dict(),
        "top_fournisseurs": df.groupby("fournisseur")["montant"].sum().nlargest(5).round(2).to_dict(),
    }
    if "employe" in df.columns:
        s["par_employe"] = df.groupby("employe")["montant"].sum().round(2).to_dict()
    if "centre_cout" in df.columns:
        s["par_centre_cout"] = df.groupby("centre_cout")["montant"].sum().round(2).to_dict()
    return s

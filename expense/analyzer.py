import pandas as pd


def detect_anomalies(df: pd.DataFrame) -> list[dict]:
    anomalies = []

    # Montant anormalement elevé: seuil statistique (mean + 3*std) OU absolu (> 20 000 EUR)
    ABSOLUTE_THRESHOLD = 20_000.0
    for cat, group in df.groupby("categorie"):
        mean = group["montant"].mean()
        std = group["montant"].std()
        stat_threshold = (mean + 3 * std) if (not pd.isna(std) and std > 0) else float("inf")
        for _, row in group.iterrows():
            flagged = row["montant"] > stat_threshold or row["montant"] >= ABSOLUTE_THRESHOLD
            if not flagged:
                continue
            detail = (
                f"Seuil categorie {cat}: {stat_threshold:.0f} EUR (moy {mean:.0f} + 3sigma)"
                if row["montant"] > stat_threshold
                else f"Montant >= seuil absolu {ABSOLUTE_THRESHOLD:,.0f} EUR"
            )
            anomalies.append({
                "type": "montant_eleve",
                "date": str(row["date"].date()),
                "montant": row["montant"],
                "fournisseur": row["fournisseur"],
                "categorie": cat,
                "description": row.get("description", ""),
                "detail": detail,
            })

    # Doublons (meme fournisseur, meme montant, < 5 jours d'ecart)
    df_sorted = df.sort_values("date").reset_index(drop=True)
    seen = set()
    for i, row in df_sorted.iterrows():
        key = (row["fournisseur"], row["montant"])
        if key in seen:
            continue
        same = df_sorted[
            (df_sorted["fournisseur"] == row["fournisseur"]) &
            (df_sorted["montant"] == row["montant"]) &
            (abs((df_sorted["date"] - row["date"]).dt.days) <= 5) &
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
                "detail": f"Transaction identique le {same.iloc[0]['date'].date()}",
            })

    # Transactions le weekend
    for _, row in df[df["date"].dt.dayofweek >= 5].iterrows():
        anomalies.append({
            "type": "weekend",
            "date": str(row["date"].date()),
            "montant": row["montant"],
            "fournisseur": row["fournisseur"],
            "categorie": row["categorie"],
            "description": row.get("description", ""),
            "detail": "Transaction un samedi ou dimanche",
        })

    # Montant rond avec description vague
    vague_keywords = {"divers", "misc", "autre", "various", "other"}
    for _, row in df.iterrows():
        desc = str(row.get("description", "")).lower().strip()
        if row["montant"] % 1000 == 0 and desc in vague_keywords:
            anomalies.append({
                "type": "montant_rond_suspect",
                "date": str(row["date"].date()),
                "montant": row["montant"],
                "fournisseur": row["fournisseur"],
                "categorie": row["categorie"],
                "description": row.get("description", ""),
                "detail": f"Montant rond {row['montant']:.0f} EUR avec description vague",
            })

    # Pic mensuel par categorie (> 3x la moyenne mensuelle)
    df2 = df.copy()
    df2["month"] = df2["date"].dt.to_period("M")
    for cat, group in df2.groupby("categorie"):
        monthly = group.groupby("month")["montant"].sum()
        if len(monthly) < 3:
            continue
        mean_month = monthly.mean()
        for month, total in monthly[monthly > mean_month * 3].items():
            anomalies.append({
                "type": "pic_categorie",
                "date": str(month),
                "montant": total,
                "fournisseur": "(multiple)",
                "categorie": cat,
                "description": "Depense mensuelle totale",
                "detail": f"Pic: {total:.0f} EUR vs moy {mean_month:.0f} EUR/mois",
            })

    return anomalies


def summarize(df: pd.DataFrame) -> dict:
    return {
        "total_lignes": len(df),
        "total_depenses": round(df["montant"].sum(), 2),
        "periode": f"{df['date'].min().date()} - {df['date'].max().date()}",
        "par_categorie": df.groupby("categorie")["montant"].sum().round(2).to_dict(),
        "top_fournisseurs": df.groupby("fournisseur")["montant"].sum().nlargest(5).round(2).to_dict(),
    }

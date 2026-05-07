import csv
import random
from datetime import date, timedelta

random.seed(42)

SUPPLIERS = ["Bureau Vallee", "Sodexo", "Total Energies", "Orange Pro", "Staples",
             "La Poste Pro", "AXA Assurances", "SNCF Voyages", "Uber Eats Pro"]
CATEGORIES = {
    "Fournitures": (50, 300),
    "Restauration": (20, 150),
    "Carburant": (60, 200),
    "Telecom": (30, 120),
    "Transport": (40, 400),
    "Assurances": (200, 800),
    "Logiciels": (50, 500),
}

rows = []
start = date(2025, 1, 1)

for i in range(190):
    d = start + timedelta(days=random.randint(0, 364))
    while d.weekday() >= 5:
        d = d + timedelta(days=1)
    cat = random.choice(list(CATEGORIES.keys()))
    low, high = CATEGORIES[cat]
    amount = round(random.uniform(low, high), 2)
    rows.append({
        "date": d.isoformat(),
        "montant": amount,
        "fournisseur": random.choice(SUPPLIERS),
        "categorie": cat,
        "description": f"Achat {cat.lower()} ref {random.randint(1000, 9999)}",
        "statut": "valide",
    })

# ANOMALIE 1: Facture geante fournisseur inconnu
rows.append({
    "date": "2025-06-15",
    "montant": 52000.00,
    "fournisseur": "DELTA CONSULT SARL",
    "categorie": "Logiciels",
    "description": "Prestation conseil transformation digitale",
    "statut": "valide",
})

# ANOMALIE 2: Doublon exact (meme fournisseur, meme montant, 2 jours apres)
rows.append({
    "date": "2025-03-10",
    "montant": 847.50,
    "fournisseur": "Bureau Vallee",
    "categorie": "Fournitures",
    "description": "Commande fournitures Q1",
    "statut": "valide",
})
rows.append({
    "date": "2025-03-12",
    "montant": 847.50,
    "fournisseur": "Bureau Vallee",
    "categorie": "Fournitures",
    "description": "Commande fournitures Q1",
    "statut": "valide",
})

# ANOMALIE 3: Transaction le dimanche
rows.append({
    "date": "2025-08-03",  # dimanche
    "montant": 3200.00,
    "fournisseur": "Sodexo",
    "categorie": "Restauration",
    "description": "Repas seminaire equipe",
    "statut": "valide",
})

# ANOMALIE 4: Montant rond avec description vague
rows.append({
    "date": "2025-10-01",
    "montant": 10000.00,
    "fournisseur": "Total Energies",
    "categorie": "Carburant",
    "description": "divers",
    "statut": "valide",
})

# ANOMALIE 5: Pic Transport novembre (8 transactions)
for _ in range(8):
    rows.append({
        "date": f"2025-11-{random.randint(1, 28):02d}",
        "montant": round(random.uniform(800, 1500), 2),
        "fournisseur": "SNCF Voyages",
        "categorie": "Transport",
        "description": "Deplacement professionnel",
        "statut": "valide",
    })

random.shuffle(rows)

with open("demo_data/expenses.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["date", "montant", "fournisseur", "categorie", "description", "statut"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} rows with 5 injected anomalies -> demo_data/expenses.csv")

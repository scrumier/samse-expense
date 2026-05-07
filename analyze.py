#!/usr/bin/env python3
import sys
import os
from datetime import datetime
from expense.loader import load_csv
from expense.analyzer import detect_anomalies, summarize
from expense.reporter import generate_report


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze.py <expenses.csv> [output_dir]")
        print("Example: python analyze.py demo_data/expenses.csv output/")
        sys.exit(1)

    csv_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output"
    os.makedirs(output_dir, exist_ok=True)

    print(f"Chargement: {csv_path}")
    df = load_csv(csv_path)
    print(f"  {len(df)} lignes chargees")

    print("Analyse en cours...")
    anomalies = detect_anomalies(df)
    stats = summarize(df)

    print(f"  {len(anomalies)} anomalies detectees")
    for a in anomalies:
        print(f"  [{a['type']}] {a['date']} - {a['fournisseur']} - {a['montant']:,.2f} EUR")

    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
    output_path = os.path.join(output_dir, f"rapport-depenses-{timestamp}.html")

    print("Generation du rapport IA...")
    generate_report(stats, anomalies, output_path)

    print(f"\nRapport genere: {output_path}")
    print(f"Total depenses: {stats['total_depenses']:,.2f} EUR")
    print(f"Periode: {stats['periode']}")


if __name__ == "__main__":
    main()

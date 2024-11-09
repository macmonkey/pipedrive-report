import argparse
from datetime import datetime
from basic_calculator import calculate_deals_metrics, calculate_activities_metrics, calculate_response_time

# Standardwerte (aktuelles Datum)
default_month = 6
default_year = datetime.now().year

# Argumentparser konfigurieren
parser = argparse.ArgumentParser(description="Berechne Sales-Performance-Kennzahlen für einen bestimmten Monat.")
parser.add_argument("--month", type=int, default=default_month, help="Monat für die Berechnung (1-12).")
parser.add_argument("--year", type=int, default=default_year, help="Jahr für die Berechnung (z.B. 2024).")

# Argumente parsen
args = parser.parse_args()
month = args.month
year = args.year

# Berechnung der einzelnen Metriken
deals_metrics = calculate_deals_metrics(month, year)
activities_metrics = calculate_activities_metrics(month, year)
print("Berechne Response-Zeiten...", flush=True)
average_response_time, no_customer_email_ids, no_contact_person_ids = calculate_response_time(month, year)

# Zusammenführen der Ergebnisse in einem Report-Dictionary
report = {
    "Report Month": f"{month}-{year}",
    "Basic Metrics": {
        "Deals Created": deals_metrics["deals_created"],
        "Total Deal Value": f"€{deals_metrics['total_deal_value']}",
        "Deals Closed": deals_metrics["deals_closed"],
        "Deals Won": deals_metrics["deals_won"],
        "Deals Lost": deals_metrics["deals_lost"],
        "Deals Open": deals_metrics["deals_open"],
        "Activities Created": activities_metrics["activities_created"],
        "Activities Completed": activities_metrics["activities_completed"],
        "Average Response Time (Hours)": average_response_time if average_response_time else "N/A",
        "Deals with No Customer Email": len(no_customer_email_ids),
        "Deal IDs with No Customer Email": no_customer_email_ids,
        "Deals with No Contact Person": len(no_contact_person_ids),
        "Deal IDs with No Contact Person": no_contact_person_ids
    }
}

# Ausgabe des finalen Reports
print("\n=== Sales Performance Report ===")
print(f"Report Month: {report['Report Month']}")
print("Basic Metrics:")
for key, value in report["Basic Metrics"].items():
    print(f"  {key}: {value}")
print("\nBerechnung abgeschlossen.")
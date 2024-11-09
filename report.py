import argparse
import csv
from datetime import datetime
from basic_calculator import calculate_deals_metrics, calculate_activities_metrics, calculate_response_time, get_data


def filter_deals_for_month(deals, month, year):
    """
    Filtert Deals für einen bestimmten Monat und Jahr.
    """
    filtered_deals = []
    for deal in deals:
        deal_month = datetime.fromisoformat(deal['add_time']).month
        deal_year = datetime.fromisoformat(deal['add_time']).year
        if deal_month == month and deal_year == year:
            print(f"add_time: {datetime.fromisoformat(deal['add_time']).date()}", flush=True)
            filtered_deals.append(deal)

    print(f"Gefilterte Deals: {filtered_deals}", flush=True)
    return filtered_deals


# Standardwerte (aktuelles Datum)
default_month = 10
default_year = 2022

# Argumentparser konfigurieren
parser = argparse.ArgumentParser(description="Berechne Sales-Performance-Kennzahlen für einen bestimmten Monat.")
parser.add_argument("--month", type=int, default=default_month, help="Monat für die Berechnung (1-12).")
parser.add_argument("--year", type=int, default=default_year, help="Jahr für die Berechnung (z.B. 2024).")

# Argumente parsen
args = parser.parse_args()
month = args.month
year = args.year

# Einmaliger Fetch der Deals und Filterung
print("Hole alle Deals...", flush=True)
all_deals = get_data('deals')
filtered_deals = filter_deals_for_month(all_deals, month, year)

# Berechnung der einzelnen Metriken mit den gefilterten Deals
deals_metrics = calculate_deals_metrics(month, year, filtered_deals)
activities_metrics = calculate_activities_metrics(month, year)
print("Berechne Response-Zeiten...", flush=True)
average_response_time, no_customer_email_ids, no_contact_person_ids = calculate_response_time(month, year,
                                                                                              filtered_deals)

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
        "Won Deal IDs": deals_metrics["won_deal_ids"],  # Neue Zeile
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

# Speichern des Reports als CSV
report_filename = f"sales_report_{month}_{year}.csv"
with open(report_filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Metric', 'Value'])
    writer.writerow(['Report Month', report['Report Month']])
    for key, value in report["Basic Metrics"].items():
        writer.writerow([key, value])

print(f"\nReport wurde als CSV in '{report_filename}' gespeichert.")
print("\nBerechnung abgeschlossen.")
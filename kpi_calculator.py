# kpi_calculator.py

import requests
import datetime
import calendar
import os
from dotenv import load_dotenv

# Lade Umgebungsvariablen aus der .env-Datei
load_dotenv()
API_TOKEN = os.getenv('API_TOKEN')  # API-Token aus .env-Datei laden
BASE_URL = 'https://api.pipedrive.com/v1'


def get_data(endpoint, params={}):
    url = f"{BASE_URL}/{endpoint}"
    params['api_token'] = API_TOKEN
    all_data = []
    while url:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json().get('data', [])
            all_data.extend(data)
            # Prüfen, ob es eine weitere Seite gibt
            pagination = response.json().get('additional_data', {}).get('pagination', {})
            if pagination.get('more_items_in_collection'):
                start = pagination.get('next_start')
                params['start'] = start  # Setze das nächste Startlimit für die nächste Seite
            else:
                break
        else:
            print(f"Fehler beim Abrufen der Daten: {response.status_code}")
            break
    return all_data


def calculate_basic_metrics(month, year):
    # Setze den Start- und Endzeitpunkt des gewünschten Monats
    start_of_month = datetime.datetime(year, month, 1)
    end_of_month = start_of_month.replace(day=calendar.monthrange(year, month)[1])

    print(f"Berechne Metriken für {month}-{year} Startdatum: {start_of_month} Enddatum: {end_of_month}")

    # Anzahl Deals erstellt und Gesamtwert der Deals (nur Deals im Zeitraum berücksichtigen)
    deals = get_data('deals')
    filtered_deals = [
        deal for deal in deals
        if
        'add_time' in deal and start_of_month <= datetime.datetime.fromisoformat(deal['add_time'][:10]) <= end_of_month
    ]

    deals_created = len(filtered_deals)
    total_deal_value = sum(deal['value'] for deal in filtered_deals if deal['value'])
    print(f"Anzahl erstellter Deals: {deals_created}")
    print(f"Gesamtwert der Deals: €{total_deal_value}")

    # Anzahl geschlossener, gewonnener, verlorener und offener Deals
    deals_closed = [deal for deal in filtered_deals if deal['status'] == 'closed']
    deals_won = [deal for deal in filtered_deals if deal['status'] == 'won']
    deals_lost = [deal for deal in filtered_deals if deal['status'] == 'lost']
    deals_open = [deal for deal in filtered_deals if deal['status'] == 'open']
    print(
        f"Deals geschlossen: {len(deals_closed)}, gewonnen: {len(deals_won)}, verloren: {len(deals_lost)}, offen: {len(deals_open)}")

    # Aktivitäten erstellt und abgeschlossen
    activities_created = get_data('activities', params={'start_date': start_of_month, 'end_date': end_of_month})
    activities_completed = [activity for activity in activities_created if activity['done'] == True]
    num_activities_created = len(activities_created)
    num_activities_completed = len(activities_completed)
    print(f"Aktivitäten erstellt: {num_activities_created}, abgeschlossen: {num_activities_completed}")

    # Ergebnis-Ausgabe
    report = {
        "Report Month": f"{month}-{year}",
        "Basic Metrics": {
            "Deals Created": deals_created,
            "Total Deal Value": f"€{total_deal_value}",
            "Deals Closed": len(deals_closed),
            "Deals Won": len(deals_won),
            "Deals Lost": len(deals_lost),
            "Deals Open": len(deals_open),
            "Activities Created": num_activities_created,
            "Activities Completed": num_activities_completed
        }
    }

    print("Berechnung abgeschlossen.")
    return report
# basic_calculator.py

import os

import requests
from dotenv import load_dotenv

# Lade Umgebungsvariablen aus der .env-Datei
load_dotenv()
API_TOKEN = os.getenv('API_TOKEN')  # API-Token aus .env-Datei laden
BASE_URL = 'https://api.pipedrive.com/v1'


def get_data(endpoint, params={}):
    url = f"{BASE_URL}/{endpoint}"
    params['api_token'] = API_TOKEN
    all_data = []

    # Nur paginierte Endpunkte unterstützen den "start"-Parameter, nicht "mailMessages"
    is_paginated = endpoint in ["deals", "activities"]  # Fügt nur Paginierung für relevante Endpunkte hinzu

    while url:
        # print(f"Abrufen von URL: {url} mit Parametern: {params}", flush=True)  # Zeigt die URL und Parameter an
        response = requests.get(url, params=params)
        # print(f"Statuscode: {response.status_code}", flush=True)

        if response.status_code == 200:
            data = response.json().get('data', [])
            # print(f"Erhaltene Daten: {data}", flush=True)  # Gibt die empfangenen Daten aus
            if data is None:
                data = []  # Setze auf eine leere Liste, falls keine Daten vorhanden sind
            all_data.extend(data)

            # Paginierung nur anwenden, wenn der Endpunkt paginiert ist
            if is_paginated:
                pagination = response.json().get('additional_data', {}).get('pagination', {})
                if pagination.get('more_items_in_collection'):
                    start = pagination.get('next_start')
                    params['start'] = start  # Setze das nächste Startlimit für die nächste Seite
                else:
                    break
            else:
                break  # Wenn keine Paginierung erwartet wird, beenden wir nach dem ersten Abruf
        else:
            print(f"Fehler beim Abrufen der Daten: {response.status_code}", flush=True)
            break

    return all_data


def calculate_deals_metrics(month, year, filtered_deals):
    start_of_month = datetime.datetime(year, month, 1)
    end_of_month = start_of_month.replace(day=calendar.monthrange(year, month)[1])

    print(f"Berechne Deal-Metriken für {month}-{year} Startdatum: {start_of_month} Enddatum: {end_of_month}",
          flush=True)

    deals_created = len(filtered_deals)
    total_deal_value = sum(deal['value'] for deal in filtered_deals if deal['value'])

    print(f"Anzahl erstellter Deals: {deals_created}", flush=True)
    print(f"Gesamtwert der Deals: €{total_deal_value}", flush=True)

    deals_closed = len([deal for deal in filtered_deals if deal['status'] == 'closed'])

    # Erfasse gewonnene Deals und ihre IDs
    won_deals = [deal for deal in filtered_deals if deal['status'] == 'won']
    deals_won = len(won_deals)
    won_deal_ids = [deal['id'] for deal in won_deals]

    deals_lost = len([deal for deal in filtered_deals if deal['status'] == 'lost'])
    deals_open = len([deal for deal in filtered_deals if deal['status'] == 'open'])

    print(f"Deals geschlossen: {deals_closed}, gewonnen: {deals_won}, verloren: {deals_lost}, offen: {deals_open}",
          flush=True)
    print(f"IDs der gewonnenen Deals: {won_deal_ids}", flush=True)
    print(f"Links zu den gewonnenen Deals:", flush=True)
    for deal_id in won_deal_ids:
        print(f"https://app.pipedrive.com/deal/{deal_id}", flush=True)

    return {
        "deals_created": deals_created,
        "total_deal_value": total_deal_value,
        "deals_closed": deals_closed,
        "deals_won": deals_won,
        "deals_lost": deals_lost,
        "deals_open": deals_open,
        "won_deal_ids": won_deal_ids
    }


def filter_activities_for_month(activities, month, year):
    """
    Filtert Aktivitäten für einen bestimmten Monat und Jahr.
    """
    filtered_activities = []
    for activity in activities:
        activity_time = datetime.datetime.fromisoformat(activity['add_time'][:19])
        if activity_time.month == month and activity_time.year == year:
            filtered_activities.append(activity)

    print(f"Gefilterte Aktivitäten: {len(filtered_activities)}", flush=True)
    return filtered_activities


def get_activities():
    """
    Holt alle Aktivitäten über den Activities Collection Endpoint.
    """
    print(f"Hole alle Aktivitäten via Collection Endpoint...", flush=True)

    url = f"{BASE_URL}/activities/collection"
    params = {
        'api_token': API_TOKEN,
        'limit': 500  # Maximale Anzahl pro Request
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get('data', [])
    else:
        print(f"Fehler beim Abrufen der Aktivitäten: {response.status_code}", flush=True)
        return []


def calculate_activities_metrics(month, year):
    """
    Berechnet Aktivitäts-Metriken für einen bestimmten Monat und Jahr.
    """
    print(f"Berechne Aktivitäten-Metriken für {month}-{year}", flush=True)

    # Alle Aktivitäten holen und filtern
    all_activities = get_activities()
    filtered_activities = filter_activities_for_month(all_activities, month, year)

    # Berechnung der Metriken
    activities_created = len(filtered_activities)
    activities_completed = len([a for a in filtered_activities if a['done']])

    print(f"Aktivitäten erstellt: {activities_created}, abgeschlossen: {activities_completed}", flush=True)

    return {
        "activities_created": activities_created,
        "activities_completed": activities_completed
    }




import csv
import datetime
import calendar


def calculate_response_time(month, year, filtered_deals):
    start_of_month = datetime.datetime(year, month, 1)
    end_of_month = start_of_month.replace(day=calendar.monthrange(year, month)[1])

    print(f"Berechne Response-Zeiten für {month}-{year}", flush=True)
    print(f"Anzahl der Deals im Zeitraum {month}-{year}: {len(filtered_deals)}", flush=True)

    response_times = []
    no_customer_email_ids = []  # Liste für Deals ohne Kundenmail
    no_contact_person_ids = []  # Liste für Deals ohne Kontaktperson
    deal_data = []  # Daten für CSV
    slow_response_deals = []  # Liste für Deals mit langsamer Antwortzeit (>12h)

    for deal in filtered_deals:
        deal_id = deal['id']
        deal_creation_time = datetime.datetime.fromisoformat(deal['add_time'][:19])
        print(f"\nDeal ID: {deal_id} erstellt am {deal_creation_time}", flush=True)
        print(f"https://app.pipedrive.com/deal/{deal_id}", flush=True)

        # Abrufen der Kontaktperson und der E-Mail-Adressen
        person_info = deal.get('person_id', {})

        if person_info is None:
            print(f"Keine Kontaktperson für Deal ID {deal_id} gefunden", flush=True)
            no_contact_person_ids.append(deal_id)
            continue

        person_id = person_info.get('value')
        person_name = person_info.get('name', 'Unbekannt')
        customer_emails = [email['value'].lower() for email in person_info.get('email', []) if 'value' in email]

        if not person_id:
            print(f"Keine Kontaktperson für Deal ID {deal_id} gefunden", flush=True)
            no_contact_person_ids.append(deal_id)
            continue

        if not customer_emails:
            print(f"Keine Kunden-E-Mail-Adressen für Deal ID {deal_id} gefunden", flush=True)
            no_customer_email_ids.append(deal_id)
            continue

        print(f"Kunden-E-Mail-Adressen für Deal ID {deal_id}: {customer_emails}", flush=True)

        # Abrufen der E-Mails über den Kontaktpersonen-Endpunkt
        emails = get_data(f"persons/{person_id}/mailMessages", params={'start': 0})
        print(f"Anzahl der E-Mails für Kontaktperson ID {person_id}: {len(emails)}", flush=True)

        # Suche nach der ersten E-Mail an die Kundenadresse
        first_customer_email_time = None
        for email in reversed(emails):
            email_data = email.get("data", {})
            to_addresses = [recipient['email_address'].lower() for recipient in email_data.get('to', [])]

            print(f"E-Mail an: {to_addresses} at: {email.get('timestamp', [])}", flush=True)

            first_customer_email_time = datetime.datetime.fromisoformat(email['timestamp'][:19])
            break

        # Berechnung der Antwortzeit und Prüfung auf langsame Antworten
        if first_customer_email_time:
            response_time_hours = round((first_customer_email_time - deal_creation_time).total_seconds() / 3600, 2)
            response_times.append(response_time_hours)
            print(f"Response-Zeit für Deal ID {deal_id}: {response_time_hours} Stunden", flush=True)

            # Erfassen von Deals mit Antwortzeit > 12 Stunden
            if response_time_hours > 12:
                slow_response_deals.append({
                    'deal_id': deal_id,
                    'person_name': person_name,
                    'response_time': response_time_hours,
                    'creation_time': deal_creation_time,
                    'response_time': first_customer_email_time
                })
        else:
            response_time_hours = "N/A"
            print(f"Keine Kunden-E-Mail für Deal ID {deal_id} gefunden", flush=True)
            no_customer_email_ids.append(deal_id)

        # CSV-Daten hinzufügen
        deal_data.append({
            "Deal ID": deal_id,
            "Person ID": person_id,
            "Person Name": person_name,
            "Deal Creation Time": deal_creation_time,
            "First Email Response Time": first_customer_email_time if first_customer_email_time else "N/A",
            "Response Time (Hours)": response_time_hours
        })

    # Durchschnittliche Response-Zeit berechnen
    avg_response_time = round(sum(response_times) / len(response_times), 2) if response_times else None
    print(
        f"\nDurchschnittliche Response-Zeit über alle Deals: {avg_response_time} Stunden" if avg_response_time else "Keine Response-Zeiten verfügbar",
        flush=True)

    # Ausgabe der langsamen Response-Zeiten
    print("\n=== Deals mit Antwortzeit > 12 Stunden ===")
    print(f"Anzahl der Deals mit langsamer Antwortzeit: {len(slow_response_deals)}")
    for deal in slow_response_deals:
        print(f"\nDeal ID: {deal['deal_id']}")
        print(f"Kontaktperson: {deal['person_name']}")
        print(f"Response-Zeit: {deal['response_time']} Stunden")
        print(f"Deal erstellt: {deal['creation_time']}")
        print(f"Erste Antwort: {deal['response_time']}")
        print(f"Link: https://app.pipedrive.com/deal/{deal['deal_id']}")

    # CSV-Datei speichern
    csv_filename = f"response_times_{month}_{year}.csv"
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["Deal ID", "Person ID", "Person Name", "Deal Creation Time",
                                                  "First Email Response Time", "Response Time (Hours)"])
        writer.writeheader()
        writer.writerows(deal_data)

    print(f"\nCSV-Datei '{csv_filename}' wurde erfolgreich gespeichert.")

    # Ausgabe von Deals ohne Kontaktperson und Deals ohne Kunden-E-Mails
    print(f"\nAnzahl der Deals ohne Kontaktperson: {len(no_contact_person_ids)}")
    print(f"Deals ohne Kontaktperson (IDs): {no_contact_person_ids}")
    print(f"\nAnzahl der Deals ohne Kunden-E-Mail: {len(no_customer_email_ids)}")
    print(f"Deals ohne Kunden-E-Mail (IDs): {no_customer_email_ids}")

    return avg_response_time, no_customer_email_ids, no_contact_person_ids, slow_response_deals  # Neue Rückgabe
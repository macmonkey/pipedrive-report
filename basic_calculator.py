# basic_calculator.py

import requests
import datetime
import calendar  # Kalender-Modul für Monatsberechnung
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


def calculate_deals_metrics(month, year):
    start_of_month = datetime.datetime(year, month, 1)
    end_of_month = start_of_month.replace(day=calendar.monthrange(year, month)[1])

    print(f"Berechne Deal-Metriken für {month}-{year} Startdatum: {start_of_month} Enddatum: {end_of_month}",
          flush=True)

    deals = get_data('deals')
    filtered_deals = [
        deal for deal in deals
        if
        'add_time' in deal and start_of_month <= datetime.datetime.fromisoformat(deal['add_time'][:10]) <= end_of_month
    ]

    deals_created = len(filtered_deals)
    total_deal_value = sum(deal['value'] for deal in filtered_deals if deal['value'])

    print(f"Anzahl erstellter Deals: {deals_created}", flush=True)
    print(f"Gesamtwert der Deals: €{total_deal_value}", flush=True)

    deals_closed = len([deal for deal in filtered_deals if deal['status'] == 'closed'])
    deals_won = len([deal for deal in filtered_deals if deal['status'] == 'won'])
    deals_lost = len([deal for deal in filtered_deals if deal['status'] == 'lost'])
    deals_open = len([deal for deal in filtered_deals if deal['status'] == 'open'])

    print(f"Deals geschlossen: {deals_closed}, gewonnen: {deals_won}, verloren: {deals_lost}, offen: {deals_open}",
          flush=True)

    return {
        "deals_created": deals_created,
        "total_deal_value": total_deal_value,
        "deals_closed": deals_closed,
        "deals_won": deals_won,
        "deals_lost": deals_lost,
        "deals_open": deals_open
    }


def calculate_activities_metrics(month, year):
    start_of_month = datetime.datetime(year, month, 1)
    end_of_month = start_of_month.replace(day=calendar.monthrange(year, month)[1])

    print(f"Berechne Aktivitäten-Metriken für {month}-{year}", flush=True)

    activities_created = get_data('activities', params={'start_date': start_of_month, 'end_date': end_of_month})
    activities_completed = [activity for activity in activities_created if activity['done'] == True]
    num_activities_created = len(activities_created)
    num_activities_completed = len(activities_completed)

    print(f"Aktivitäten erstellt: {num_activities_created}, abgeschlossen: {num_activities_completed}", flush=True)

    return {
        "activities_created": num_activities_created,
        "activities_completed": num_activities_completed
    }


def calculate_response_time(month, year):
    start_of_month = datetime.datetime(year, month, 1)
    end_of_month = start_of_month.replace(day=calendar.monthrange(year, month)[1])

    print(f"Berechne Response-Zeiten für {month}-{year}", flush=True)

    # Lade alle Deals im angegebenen Zeitraum
    deals = get_data('deals')
    filtered_deals = [
        deal for deal in deals
        if
        'add_time' in deal and start_of_month <= datetime.datetime.fromisoformat(deal['add_time'][:10]) <= end_of_month
    ]

    response_times = []
    no_customer_email_ids = []  # Liste für Deals ohne Kundenmail

    for deal in filtered_deals:
        deal_id = deal['id']
        deal_creation_time = datetime.datetime.fromisoformat(deal['add_time'][:19])
        print(f"\nDeal ID: {deal_id} erstellt am {deal_creation_time}", flush=True)

        # Abrufen der Kontaktdaten (Kunden-E-Mail-Adressen)
        person_info = deal.get('person_id', {})
        customer_emails = [email['value'].lower() for email in person_info.get('email', []) if 'value' in email]

        if customer_emails:
            print(f"Kunden-E-Mail-Adressen für Deal ID {deal_id}: {customer_emails}", flush=True)
        else:
            print(f"Keine Kunden-E-Mail-Adressen für Deal ID {deal_id} gefunden", flush=True)
            no_customer_email_ids.append(deal_id)  # Deal ID speichern
            continue  # Ohne Kunden-E-Mail-Adresse ist eine Antwortzeit-Berechnung nicht möglich

        # Abrufen der E-Mails, die zu diesem Deal gehören
        emails = get_data(f"deals/{deal_id}/mailMessages", params={'start': 0})
        print(f"Anzahl der E-Mails für Deal ID {deal_id}: {len(emails)}", flush=True)

        # Suche nach der ersten E-Mail vom Agenten an eine der Kunden-E-Mail-Adressen (Liste umgedreht)
        first_customer_email_time = None
        for email in reversed(emails):  # Beginne mit der ältesten E-Mail
            email_data = email.get("data", {})
            from_addresses = [sender['email_address'].lower() for sender in email_data.get('from', [])]
            to_addresses = [recipient['email_address'].lower() for recipient in email_data.get('to', [])]

            print(f"E-Mail von: {from_addresses} an: {to_addresses}", flush=True)

            # Überprüfen, ob die E-Mail vom Agenten stammt und an den Kunden gesendet wurde
            if any(agent_email for agent_email in from_addresses) and any(
                    customer_email in to_addresses for customer_email in customer_emails):
                email_time = datetime.datetime.fromisoformat(email_data['add_time'][:19])
                first_customer_email_time = email_time
                print(f"Erste E-Mail vom Agenten an Kunden gefunden: Gesendet am {first_customer_email_time}",
                      flush=True)
                break

        # Berechnung der Antwortzeit, falls eine E-Mail gefunden wurde
        if first_customer_email_time:
            response_time_hours = (first_customer_email_time - deal_creation_time).total_seconds() / 3600
            response_times.append(response_time_hours)
            print(f"Response-Zeit für Deal ID {deal_id}: {response_time_hours} Stunden", flush=True)
        else:
            print(f"Keine Kunden-E-Mail für Deal ID {deal_id} gefunden", flush=True)
            no_customer_email_ids.append(deal_id)  # Deal ID speichern

    # Durchschnittliche Response-Zeit über alle Deals berechnen
    avg_response_time = sum(response_times) / len(response_times) if response_times else None
    print(
        f"\nDurchschnittliche Response-Zeit über alle Deals: {avg_response_time} Stunden" if avg_response_time else "Keine Response-Zeiten verfügbar",
        flush=True)

    # Rückgabe der durchschnittlichen Antwortzeit und der Liste der IDs ohne Kundenmail
    return avg_response_time, no_customer_email_ids
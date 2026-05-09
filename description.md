# Dokumentacja Projektu: System Zarządzania Odpadami Komunalnymi

Niniejszy dokument (`description.md`) opisuje architekturę, strukturę oraz kluczowe koncepcje projektu. Został przygotowany jako wsad dla narzędzi AI (LLM, asystentów kodu), aby zapewnić pełen kontekst przy pracy nad aplikacją.

## 1. Cel i charakterystyka aplikacji

**Opis z README:**
Aplikacja umożliwia zgłaszanie zapotrzebowania na wywóz pojemników oraz śledzenie historii dla przypisanych lokalizacji.

Projekt koncentruje się na zarządzaniu odpadami komunalnymi, koordynacji odbiorów, raportowaniu oraz harmonogramowaniu wywozu odpadów. Użytkownicy w zależności od ról i uprawnień zarządzają zleceniowymi odbiorami oraz przeglądają raporty i statystyki.

## 2. Stos Technologiczny i Środowisko

- **Język:** Python 3.13+
- **Framework webowy:** Django 5.2
- **Zarządzanie pakietami i uruchamianie:** `uv`
- **Baza danych:** Konfiguracja przygotowana pod PostgreSQL (`psycopg2-binary`), lecz lokalnie w `base.py` bywa używany SQLite do celów deweloperskich.
- **Kolejkowanie zadań / Background jobs:** Celery + Django Celery Beat + Django Celery Results
- **Przetwarzanie danych i raporty Excel:** `pandas`, `openpyxl`
- **Zabezpieczenia / Logowanie:** `django-axes` (blokowanie po nieudanych logowaniach), `django-auditlog`
- **Narzędzia developerskie:** `ruff` (linter), `pytest` / `pytest-django` (testy), `factory-boy`, `django-debug-toolbar`
- **Zarządzanie konfiguracją:** `python-decouple` (odczyt zmiennych środowiskowych z pliku `.env`)

### Zmienne środowiskowe (`.env`)
Projekt wymaga zdefiniowania w pliku `.env` m.in.:
- `SECRET_KEY`, `ALLOWED_HOSTS`
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- Ustawień SMTP: `SMTP_HOST`, `SMTP_PORT`, `SMTP_TLS`, `SMTP_USER`, `SMTP_PASSWORD`, `DEFAULT_FROM_EMAIL`, `ZGLOSZENIA_EMAIL`

## 3. Kluczowe Konwencje i Architektura Współdzielona

- **`core.models.CoreModel`:** Główna klasa bazowa abstrahująca większość modeli w systemie. Dodaje pola `created_at`, `updated_at`, `created_by`, `updated_by`, oraz `note`. Metoda `save()` korzysta z `django-crum` do automatycznego wypełniania pól `*_by` aktualnie zalogowanym użytkownikiem.
- W aplikacjach Django występuje podział na mniejsze moduły z wydzielonymi odpowiedzialnościami: `users`, `locations`, `waste`, `pickups`, `reports`, `scheduling`, `notifications`.

## 4. Struktura Katalogów i Modułów Django

### Główne Katalogi

- `config/` - Konfiguracja projektu Django (settings podzielone na środowiska: `base.py`, `development.py`, `production.py`, plik urls.py, itp.).
- `static/` - Statyczne pliki (CSS, JS, obrazy). Używany jest Bootstrap i niestandardowy CSS.
- `templates/` - Szablony HTML bazujące na mechanizmie Django Templates.

### Aplikacje Django (Architektura biznesowa)

Poniżej przedstawiono poszczególne aplikacje i opartą na nich strukturę bazy danych. Prawie wszystkie modele dziedziczą po `CoreModel`.

#### `core`
Odpowiada za współdzielone mechanizmy, takie jak eksport/import czy podstawowe klasy rozszerzające.
- **`CoreModel` (Abstract)**: Pola śledzące (`created_at`, `updated_at`, `created_by`, `updated_by`, `note`).
- **`DataTransferLog`**: Rejestr działań importu/eksportu (`action`, `table_name`, `file_name`, `status`, `records_count`, `details`).

#### `locations`
Zarządzanie lokalizacjami i punktami powstawania kosztów/odbioru.
- **`MPKNumber`**: Numer MPK (`mpk_number`, `active`).
- **`Location`**: Konkretne obiekty (`mpk_number`, `obj_name`, `org_unit_name`, `localization`, `active`).
- **`LocationWasteBin`**: Ilość i typ pojemników w danej lokalizacji (`location`, `waste_fraction`, `quantity`).
- **`LocationContact`**: Dane kontaktowe powiązane z lokalizacją (`location`, `contact_name`, `phone_number`, `active`).

#### `users`
Rozszerzenia wbudowanego modelu Użytkownika Django oraz system uprawnień i ról (np. koordynator).
- **`UserProfile`**: Profil użytkownika 1:1 z User (`phone`, `department_short`, `department_name`).
- **`Permission`**: Zarządzanie uprawnieniami w kontekście ról dla MPK (`user`, `mpk_number`, `role`, `active`, `granted_by`).
- **`Coordinator`**: Powiązanie użytkownika z lokalizacją (`user`, `location`, `active`).

#### `waste`
Słowniki oraz koszty związane z frakcjami odpadów.
- **`WasteFractionType`**: Rodzaj frakcji (`name`, `code`, `active`).
- **`WasteFraction`**: Pojemność, jednostka miary dla frakcji (`fraction_type`, `capacity`, `unit`, `active`).
- **`WasteCost`**: Koszty historyczne i obecne związane z frakcjami (`waste_fraction`, `cost`, `date_from`, `date_to`).

#### `pickups`
Serce systemu dla zgłaszania i śledzenia odbiorów.
- **`Pickup`**: Zlecenie odbioru (`pickup_number`, `location`, `mpk_number`, `reporter`, `reported_at`, `status`, `contact_phone`). Posiada własne statusy.
- **`PickupWasteBin`**: Pojemniki przypisane do danego zlecenia odbioru (`pickup`, `waste_fraction`, `quantity`).

#### `scheduling`
Zarządzanie harmonogramami regularnych odbiorów (planowanie).
- **`CollectionSchedule`**: Dzień i typ frakcji (`fraction_type`, `day_of_week`, `active`).

#### `reports`
Narzędzia analityczne i potwierdzenia miesięczne.
- **`SummaryCollectionSchedule`**: Podsumowania odbiorów (`mpk_number`, `year`, `month`, `waste_fraction`, `quantity`, `date_summary`, `imported_at`, `imported_by`).
- **`MonthlyConfirmation`**: Miesięczne potwierdzenie dla MPK (`mpk_number`, `month`, `status`, `approved_by`, `approved_at`).
- **`MonthlyConfirmationBin`**: Potwierdzenie ilości dla poszczególnych frakcji (`confirmation`, `waste_fraction`, `confirmed_quantity`, `note`).

#### `notifications`
Powiadamianie użytkowników o ważnych zdarzeniach (np. statusy odbiorów).
- **`Notification`**: Wiadomość systemowa (`user`, `message`, `is_read`).
- **`NotificationSetting`**: Ustawienia globalne dla przypomnień (`reminder_threshold_days`).

## 5. Wytyczne programistyczne (Guidelines dla AI)
1. **Rozszerzanie Modeli**: Wszelkie nowe tabele biznesowe powinny dziedziczyć z `core.models.CoreModel`, aby automatycznie zachować ślad audytowy. Pamiętaj, że podczas używania `.bulk_create()` i `.bulk_update()` pola `created_by` / `updated_by` nie uzupełnią się automatycznie i należy to obsłużyć ręcznie.
2. **Uprawnienia i Bezpieczeństwo**: Widoki, szczególnie eksport/import narzędzi administracyjnych, muszą jawnie wykluczać systemowe aplikacje (admin, auth, contenttypes).
3. **Zmienne lokalne**: Przy wdrażaniu nowej konfiguracji (np. ustawienia systemowe, logiki biznesowe) rozważ użycie `python-decouple` by zachować konfigurację w pliku `.env`.
4. **Testowanie**: Kod jest testowany przy użyciu modułu standardowego Django i `pytest`. Jeśli modele korzystają z `auto_now_add` (np. `reported_at`), dla powtarzalnych testów mockuj `django.utils.timezone.now` lub aktualizuj rekord przez `.update()`. Linter to `ruff`, ale nie używaj domyślnie `ruff check --fix` dla całego pliku ze względu na ryzyko usunięcia potrzebnych importów.
5. **Zarządzanie repozytorium**: Domyślną gałęzią (branch) jest `main`.

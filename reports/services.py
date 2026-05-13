from collections import defaultdict
# reports/services.py
import io

import pandas as pd
from datetime import date, timedelta
from collections import defaultdict
from django.db import transaction
from scheduling.services import get_next_pickup_date
from .models import SummaryCollectionSchedule, MonthlyConfirmation, MonthlyConfirmationBin
from waste.models import WasteFraction, WasteCost
from locations.models import Location
from locations.models import MPKNumber
from pickups.models import PickupWasteBin


def get_system_sum_for_month(mpk, fraction, month, year):
    """
    Sumuje zgłoszenia, których PLANOWANY odbiór wypada w danym miesiącu.
    """
    first_day_current = date(year, month, 1)
    if month == 12:
        first_day_next = date(year + 1, 1, 1)
    else:
        first_day_next = date(year, month + 1, 1)
    
    start_search = first_day_current - timedelta(days=10)
    end_search = first_day_next + timedelta(days=5)

    pickups = PickupWasteBin.objects.filter(
        pickup__mpk_number=mpk,
        waste_fraction=fraction,
        pickup__reported_at__date__range=[start_search, end_search]
    ).select_related('pickup')

    total_qty = 0
    
    for p in pickups:
        planned_date = get_next_pickup_date(
            fraction.fraction_type, 
            submitted_at=p.pickup.reported_at
        )
        
        if planned_date and planned_date.month == month and planned_date.year == year:
            total_qty += p.quantity
            
    return total_qty


def precalculate_system_sums(df):
    """
    Precalculate system sums for all unique combinations in the dataframe.
    """
    valid_rows = []

    # Check if all required columns are present
    required_cols = ['Numer MPK', 'Frakcja', 'Pojemność', 'Miesiąc', 'Rok']
    if not all(col in df.columns for col in required_cols):
        return {}, {}, defaultdict(int)

    for _, row in df.iterrows():
        try:
            valid_rows.append({
                'Numer MPK': int(row['Numer MPK']),
                'Frakcja': row['Frakcja'],
                'Pojemność': int(row['Pojemność']),
                'Miesiąc': int(row['Miesiąc']),
                'Rok': int(row['Rok'])
            })
        except (ValueError, TypeError):
            continue

    if not valid_rows:
        return {}, {}, defaultdict(int)

    valid_df = pd.DataFrame(valid_rows)
    unique_combinations = valid_df.drop_duplicates()

    mpk_numbers = unique_combinations['Numer MPK'].unique()
    mpks = {mpk.mpk_number: mpk for mpk in MPKNumber.objects.filter(mpk_number__in=mpk_numbers)}

    fraction_pairs = unique_combinations[['Frakcja', 'Pojemność']].drop_duplicates()
    fractions_q = WasteFraction.objects.none()
    for _, row in fraction_pairs.iterrows():
        fractions_q |= WasteFraction.objects.filter(fraction_type__name=row['Frakcja'], capacity=row['Pojemność'])

    fractions = {(f.fraction_type.name, f.capacity): f for f in fractions_q.select_related('fraction_type').prefetch_related('fraction_type__schedules')}

    min_date = None
    max_date = None

    ranges = []
    month_years = unique_combinations[['Miesiąc', 'Rok']].drop_duplicates()
    for _, row in month_years.iterrows():
        m, y = int(row['Miesiąc']), int(row['Rok'])
        first_day_current = date(y, m, 1)
        if m == 12:
            first_day_next = date(y + 1, 1, 1)
        else:
            first_day_next = date(y, m + 1, 1)

        start_search = first_day_current - timedelta(days=10)
        end_search = first_day_next + timedelta(days=5)

        if min_date is None or start_search < min_date:
            min_date = start_search
        if max_date is None or end_search > max_date:
            max_date = end_search

        ranges.append({'month': m, 'year': y, 'start': start_search, 'end': end_search})

    system_sums = defaultdict(int)

    if min_date is not None and max_date is not None and mpk_numbers.size > 0:
        all_pickups = PickupWasteBin.objects.filter(
            pickup__mpk_number__mpk_number__in=mpk_numbers,
            pickup__reported_at__date__range=[min_date, max_date]
        ).select_related('pickup', 'waste_fraction', 'pickup__mpk_number')

        pickups_by_mpk_frac = defaultdict(list)
        for p in all_pickups:
            key = (p.pickup.mpk_number_id, p.waste_fraction_id)
            pickups_by_mpk_frac[key].append(p)

        for _, row in unique_combinations.iterrows():
            mpk_num = int(row['Numer MPK'])
            f_name = row['Frakcja']
            f_cap = int(row['Pojemność'])
            month = int(row['Miesiąc'])
            year = int(row['Rok'])

            mpk = mpks.get(mpk_num)
            fraction = fractions.get((f_name, f_cap))

            if not mpk or not fraction:
                continue

            range_info = next((r for r in ranges if r['month'] == month and r['year'] == year), None)
            if not range_info:
                continue

            relevant_pickups = pickups_by_mpk_frac.get((mpk.id, fraction.id), [])

            total_qty = 0
            for p in relevant_pickups:
                # filter by range specific to this month/year combo
                if not (range_info['start'] <= p.pickup.reported_at.date() <= range_info['end']):
                    continue

                planned_date = get_next_pickup_date(
                    fraction.fraction_type,
                    submitted_at=p.pickup.reported_at
                )

                if planned_date and planned_date.month == month and planned_date.year == year:
                    total_qty += p.quantity

            system_sums[(mpk.id, fraction.id, month, year)] = total_qty

    return mpks, fractions, system_sums

def import_collection_data(file_path, user):
    if str(file_path).endswith('.csv') or hasattr(file_path, 'name') and file_path.name.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path, parse_dates=['Data Odbioru'])

    results = {'imported': 0, 'skipped': 0, 'auto_confirmed': 0, 'errors': []}

    mpks, fractions, system_sums = precalculate_system_sums(df)

    with transaction.atomic():
        for index, row in df.iterrows():
            try:
                mpk_num = int(row['Numer MPK'])
                f_name = row['Frakcja']
                f_cap = int(row['Pojemność'])

                mpk = mpks.get(mpk_num)
                if not mpk:
                    mpk = MPKNumber.objects.get(mpk_number=mpk_num)

                fraction = fractions.get((f_name, f_cap))
                if not fraction:
                    fraction = WasteFraction.objects.get(
                        fraction_type__name=f_name,
                        capacity=f_cap
                    )

                excel_qty = int(row['Ilość'])
                month = int(row['Miesiąc'])
                year = int(row['Rok'])

                raw_date = row['Data Odbioru']
                if pd.isna(raw_date):
                    date_summary = date(year, month, 1)
                else:
                    date_summary = pd.to_datetime(raw_date).date()

                obj, created = SummaryCollectionSchedule.objects.update_or_create(
                    mpk_number=mpk,
                    year=year,
                    month=month,
                    waste_fraction=fraction,
                    defaults={
                        'quantity': excel_qty,
                        'imported_by': user,
                        'date_summary': date_summary,
                    }
                )
                if created:
                    results['imported'] += 1
                    system_qty = system_sums.get((mpk.id, fraction.id, month, year), 0)
                    # Fallback if not precalculated for some reason
                    if (mpk.id, fraction.id, month, year) not in system_sums:
                        system_qty = get_system_sum_for_month(mpk, fraction, month, year)

                    if system_qty == excel_qty:
                        first_day = date(year, month, 1)
                        confirmation, _ = MonthlyConfirmation.objects.get_or_create(
                            mpk_number=mpk, month=first_day
                        )
                        MonthlyConfirmationBin.objects.update_or_create(
                        confirmation=confirmation,
                        waste_fraction=fraction,
                        defaults={
                            'confirmed_quantity': excel_qty,
                            'note': 'Zgodność automatyczna (uwzględniono przesunięcia dat).'
                            }
                        )
                        confirmation.status = 'POTWIERDZONE'
                        confirmation.save()
                        results['auto_confirmed'] += 1
                else:
                    results['skipped'] += 1

            except Exception as e:
                results['errors'].append(f"Błąd w wierszu {index}: {str(e)}")

    return results


def generate_mpk_cost_report(year=None, month=None, mpk_number_id=None, report_format='xlsx'):
    # Query data
    qs = SummaryCollectionSchedule.objects.select_related(
        'mpk_number', 'waste_fraction', 'waste_fraction__fraction_type'
    )

    if year:
        qs = qs.filter(year=year)
    if month:
        qs = qs.filter(month=month)
    if mpk_number_id:
        qs = qs.filter(mpk_number_id=mpk_number_id)

    summaries = list(qs)

    # Pre-fetch all costs to memory
    all_costs = list(WasteCost.objects.all().order_by('-date_from'))

    costs_by_fraction = defaultdict(list)
    for cost in all_costs:
        costs_by_fraction[cost.waste_fraction_id].append(cost)

    # Pre-fetch locations to memory
    # We want obj_name from Location for the given MPK.
    # An MPK can have multiple locations, we can just join them or take the first one.
    locations = list(Location.objects.filter(active=True))
    mpk_locations = defaultdict(list)
    for loc in locations:
        mpk_locations[loc.mpk_number_id].append(loc.obj_name)

    def get_location_name(mpk_id):
        locs = mpk_locations.get(mpk_id)
        if locs:
            return ", ".join(set(locs))
        return "Brak lokalizacji"

    def get_cost_for_fraction_and_date(fraction_id, target_date):
        for cost in costs_by_fraction.get(fraction_id, []):
            if cost.date_from <= target_date and (cost.date_to is None or cost.date_to >= target_date):
                return cost.cost
        return None

    data = []
    missing_costs = []
    missing_costs_keys = set()

    for row in summaries:
        target_date = row.date_summary
        unit_cost = get_cost_for_fraction_and_date(row.waste_fraction_id, target_date)

        mpk_num = row.mpk_number.mpk_number
        loc_name = get_location_name(row.mpk_number_id)
        fraction_name = str(row.waste_fraction)

        if unit_cost is None:
            cost_val = 0
            key = (mpk_num, row.year, row.month, fraction_name)
            if key not in missing_costs_keys:
                missing_costs_keys.add(key)
                missing_costs.append({
                    'Numer MPK': mpk_num,
                    'Rok': row.year,
                    'Miesiąc': row.month,
                    'Frakcja': fraction_name
                })
        else:
            cost_val = unit_cost

        total_cost = cost_val * row.quantity

        data.append({
            'Numer MPK': mpk_num,
            'Nazwa Lokalizacji': loc_name,
            'Rok': row.year,
            'Miesiąc': row.month,
            'Frakcja': fraction_name,
            'Ilość Pojemników': row.quantity,
            'Koszt Jednostkowy': cost_val,
            'Suma Kosztów': total_cost
        })

    df_main = pd.DataFrame(data)
    df_missing = pd.DataFrame(missing_costs)

    if report_format == 'csv':
        output = io.StringIO()
        if not df_main.empty:
            df_main.to_csv(output, index=False)
        else:
            pd.DataFrame(columns=['Numer MPK', 'Nazwa Lokalizacji', 'Rok', 'Miesiąc', 'Frakcja', 'Ilość Pojemników', 'Koszt Jednostkowy', 'Suma Kosztów']).to_csv(output, index=False)
        return output.getvalue().encode('utf-8')
    else:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            if not df_main.empty:
                df_main.to_excel(writer, sheet_name='Raport Kosztowy', index=False)

                # Group by MPK, Rok, Miesiac
                df_final = df_main.groupby(['Numer MPK', 'Rok', 'Miesiąc'])['Suma Kosztów'].sum().reset_index()
                df_final.to_excel(writer, sheet_name='Raport Końcowy', index=False)
            else:
                pd.DataFrame(columns=['Numer MPK', 'Nazwa Lokalizacji', 'Rok', 'Miesiąc', 'Frakcja', 'Ilość Pojemników', 'Koszt Jednostkowy', 'Suma Kosztów']).to_excel(writer, sheet_name='Raport Kosztowy', index=False)
                pd.DataFrame(columns=['Numer MPK', 'Rok', 'Miesiąc', 'Suma Kosztów']).to_excel(writer, sheet_name='Raport Końcowy', index=False)

            if not df_missing.empty:
                df_missing.to_excel(writer, sheet_name='Braki w kosztorysach', index=False)
            else:
                pd.DataFrame(columns=['Numer MPK', 'Rok', 'Miesiąc', 'Frakcja']).to_excel(writer, sheet_name='Braki w kosztorysach', index=False)

            # Apply openpyxl styling
            workbook = writer.book
            from openpyxl.styles import Font

            ws_main = workbook['Raport Kosztowy']
            for cell in ws_main[1]:
                cell.font = Font(bold=True)

            # Currency format for Cost columns (G and H)
            for col in ['G', 'H']:
                for cell in ws_main[col]:
                    if cell.row > 1:
                        cell.number_format = '#,##0.00 "zł"'

            ws_missing = workbook['Braki w kosztorysach']
            for cell in ws_missing[1]:
                cell.font = Font(bold=True)

            ws_final = workbook['Raport Końcowy']
            for cell in ws_final[1]:
                cell.font = Font(bold=True)

            # Currency format for Suma Kosztów column (D)
            for cell in ws_final['D']:
                if cell.row > 1:
                    cell.number_format = '#,##0.00 "zł"'


        # Applying styling via openpyxl if needed can be done using writer.sheets
        return output.getvalue()

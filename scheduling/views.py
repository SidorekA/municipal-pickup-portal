import calendar
from datetime import date
from django.shortcuts import render
from django.views.generic import TemplateView
from .models import CollectionSchedule

class CalendarView(TemplateView):
    template_name = 'scheduling/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get current year and month (could be passed via URL args in the future)
        today = date.today()
        year = kwargs.get('year', today.year)
        month = kwargs.get('month', today.month)

        # Get active schedules
        schedules = CollectionSchedule.objects.filter(active=True).select_related('fraction_type')

        # Group schedules by day of week (1=Monday, 7=Sunday in ISO,
        # but in Django Choices it's 1=Monday to 5=Friday usually.
        # Let's check model choices: 1=Poniedziałek, ..., 5=Piątek
        # Python calendar: 0=Monday, ..., 6=Sunday
        # So we map day_of_week to python weekday: model_day - 1
        schedules_by_weekday = {}
        for schedule in schedules:
            weekday = schedule.day_of_week - 1
            if weekday not in schedules_by_weekday:
                schedules_by_weekday[weekday] = []
            schedules_by_weekday[weekday].append(schedule)

        cal = calendar.Calendar(firstweekday=0) # Monday first
        month_days = cal.monthdatescalendar(year, month)

        # Build the calendar grid
        calendar_grid = []
        for week in month_days:
            week_data = []
            for day in week:
                is_current_month = day.month == month
                is_today = day == today
                weekday = day.weekday()

                day_schedules = schedules_by_weekday.get(weekday, []) if is_current_month else []

                week_data.append({
                    'date': day,
                    'day_num': day.day,
                    'is_current_month': is_current_month,
                    'is_today': is_today,
                    'schedules': day_schedules,
                })
            calendar_grid.append(week_data)

        context['calendar_grid'] = calendar_grid
        context['month'] = month
        context['year'] = year

        # Pass unique fractions to template for legend
        fractions = set(s.fraction_type for s in schedules)
        context['fractions'] = list(fractions)

        return context

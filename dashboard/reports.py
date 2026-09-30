from datetime import timedelta
from io import BytesIO
from xml.sax.saxutils import escape
from django import forms
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from health.models import WeightRecord, Meal, Activity

class WeekForm(forms.Form):
    week = forms.DateField(label='Une date de la semaine à consulter', widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'))
    def clean_week(self):
        value = self.cleaned_data['week']
        if value > timezone.localdate() or value.year < 1900:
            raise forms.ValidationError('Choisissez une date entre 1900 et aujourd’hui.')
        return value


def weekly_report(user, day):
    start = day - timedelta(days=day.weekday())
    end = start + timedelta(days=6)
    today = timezone.localdate()
    cutoff = min(end, today)
    meals = Meal.objects.filter(user=user, date__range=(start, cutoff))
    activities = Activity.objects.filter(user=user, date__range=(start, cutoff))
    weights = list(WeightRecord.objects.filter(user=user, date__range=(start, cutoff)).order_by('date'))
    consumed = {row['date']: row['total'] for row in meals.values('date').annotate(total=Sum('calories'))}
    burned = {row['date']: row['total'] for row in activities.values('date').annotate(total=Sum('calories_burned'))}
    weight_by_day = {row.date: row.weight for row in weights}
    rows = []
    for offset in range(7):
        date = start + timedelta(days=offset)
        rows.append({'date': date, 'consumed': consumed.get(date), 'burned': burned.get(date), 'weight': weight_by_day.get(date), 'future': date > today})
    return {'start': start, 'end': end, 'partial': end >= today, 'rows': rows, 'consumed': sum(consumed.values()), 'burned': sum(burned.values()), 'meal_days': len(consumed), 'sessions': activities.count(), 'minutes': activities.aggregate(total=Sum('duration'))['total'] or 0, 'weight_change': weights[-1].weight - weights[0].weight if len(weights) >= 2 else None, 'weight_count': len(weights)}


def report_pdf(report, user):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    stream = BytesIO()
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(stream, pagesize=A4, title='Forma - Rapport hebdomadaire')
    story = [Paragraph('Forma - Rapport hebdomadaire', styles['Title']), Paragraph(escape(user.get_full_name() or user.username), styles['Normal']), Paragraph(f"Du {report['start']:%d/%m/%Y} au {report['end']:%d/%m/%Y}" + (' (semaine en cours)' if report['partial'] else ''), styles['Normal']), Spacer(1, 18)]
    for text in [f"Calories enregistrées : {report['consumed']} kcal sur {report['meal_days']} jour(s) renseigné(s).", f"Activités : {report['sessions']} séance(s), {report['minutes']} minutes, {report['burned']} kcal brûlées.", f"Mesures de poids : {report['weight_count']}. Variation dans la semaine : " + (f"{report['weight_change']:+.2f} kg." if report['weight_change'] is not None else 'non calculable.')]:
        story.append(Paragraph(escape(text), styles['Normal']))
    story.append(Spacer(1, 18))
    data = [['Date', 'Poids (kg)', 'Repas (kcal)', 'Activités (kcal)']]
    for row in report['rows']:
        data.append([row['date'].strftime('%d/%m/%Y')] + [str(row[key]) if row[key] is not None else '-' for key in ['weight', 'consumed', 'burned']])
    table = Table(data, repeatRows=1, colWidths=[110, 100, 115, 125])
    table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e7eedb')), ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#233d32')), ('GRID', (0, 0), (-1, -1), .5, colors.HexColor('#d6dfd5')), ('TOPPADDING', (0, 0), (-1, -1), 10), ('BOTTOMPADDING', (0, 0), (-1, -1), 10)]))
    story += [table, Spacer(1, 18), Paragraph('Un tiret signifie aucune saisie (ou une date future), pas une valeur nulle. Les journées renseignées peuvent être incomplètes. Ce rapport décrit vos saisies et ne remplace pas un avis médical.', styles['Normal'])]
    doc.build(story)
    return stream.getvalue()


@login_required
@never_cache
def reports(request, pdf=False):
    default = timezone.localdate() - timedelta(days=timezone.localdate().weekday() + 7)
    form = WeekForm(request.GET if 'week' in request.GET else {'week': default.isoformat()})
    report = weekly_report(request.user, form.cleaned_data['week']) if form.is_valid() else None
    if pdf and report:
        response = HttpResponse(report_pdf(report, request.user), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="forma-semaine-{report["start"].isoformat()}.pdf"'
        return response
    return render(request, 'reports.html', {'form': form, 'report': report}, status=200 if report else 400)

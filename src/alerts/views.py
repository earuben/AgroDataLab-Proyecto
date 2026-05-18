from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import AlertReviewForm, RecommendationForm
from .models import Alert, Recommendation
from .services import get_alert_summary, get_recommendation_summary


@login_required
def alert_list(request):
    alerts = Alert.objects.select_related("record").order_by("-fecha")[:150]
    return render(
        request,
        "alerts/alert_list.html",
        {
            "alerts": alerts,
            "summary": get_alert_summary(),
            "generate_command": "python manage.py generate_alerts",
        },
    )


class AlertReviewView(LoginRequiredMixin, UpdateView):
    model = Alert
    form_class = AlertReviewForm
    template_name = "alerts/alert_review_form.html"
    context_object_name = "alert"
    success_url = reverse_lazy("alert_list")


class RecommendationListView(LoginRequiredMixin, ListView):
    model = Recommendation
    template_name = "alerts/recommendation_list.html"
    context_object_name = "recommendations"
    paginate_by = 20

    def get_queryset(self):
        return (
            Recommendation.objects.select_related("alerta_relacionada", "creada_por")
            .order_by("-actualizada_en", "-creada_en")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["summary"] = get_recommendation_summary()
        context["suggest_command"] = "python manage.py suggest_recommendations --limit 25"
        return context


class RecommendationDetailView(LoginRequiredMixin, DetailView):
    model = Recommendation
    template_name = "alerts/recommendation_detail.html"
    context_object_name = "recommendation"


class RecommendationCreateView(LoginRequiredMixin, CreateView):
    model = Recommendation
    form_class = RecommendationForm
    template_name = "alerts/recommendation_form.html"
    success_url = reverse_lazy("recommendation_list")

    def get_initial(self):
        initial = super().get_initial()
        alert_id = self.request.GET.get("alert")
        if alert_id:
            initial["alerta_relacionada"] = alert_id
        return initial

    def form_valid(self, form):
        form.instance.creada_por = self.request.user
        return super().form_valid(form)


class RecommendationUpdateView(LoginRequiredMixin, UpdateView):
    model = Recommendation
    form_class = RecommendationForm
    template_name = "alerts/recommendation_form.html"
    success_url = reverse_lazy("recommendation_list")


class RecommendationDeleteView(LoginRequiredMixin, DeleteView):
    model = Recommendation
    template_name = "alerts/recommendation_confirm_delete.html"
    context_object_name = "recommendation"
    success_url = reverse_lazy("recommendation_list")


@login_required
@require_POST
def recommendation_mark_reviewed(request, pk):
    recommendation = get_object_or_404(Recommendation, pk=pk)
    recommendation.estado = Recommendation.Status.DONE
    recommendation.save(update_fields=["estado", "actualizada_en"])
    return redirect("recommendation_list")

from django.urls import path

from . import views


urlpatterns = [
    path("", views.alert_list, name="alert_list"),
    path("<int:pk>/revisar/", views.AlertReviewView.as_view(), name="alert_review"),
    path("recomendaciones/", views.RecommendationListView.as_view(), name="recommendation_list"),
    path(
        "recomendaciones/nueva/",
        views.RecommendationCreateView.as_view(),
        name="recommendation_create",
    ),
    path(
        "recomendaciones/<int:pk>/",
        views.RecommendationDetailView.as_view(),
        name="recommendation_detail",
    ),
    path(
        "recomendaciones/<int:pk>/editar/",
        views.RecommendationUpdateView.as_view(),
        name="recommendation_update",
    ),
    path(
        "recomendaciones/<int:pk>/revisada/",
        views.recommendation_mark_reviewed,
        name="recommendation_mark_reviewed",
    ),
    path(
        "recomendaciones/<int:pk>/eliminar/",
        views.RecommendationDeleteView.as_view(),
        name="recommendation_delete",
    ),
]

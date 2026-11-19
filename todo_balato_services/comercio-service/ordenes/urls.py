from django.urls import path
from .views import CarritoCalcularView, CheckoutView

urlpatterns = [
    path("carrito/calcular", CarritoCalcularView.as_view()),
    path("checkout", CheckoutView.as_view()),
]
from django.urls import path
from .views import CarritoCalcularView, CheckoutView
from .carrito_views import CarritoView, CombinarCarritoView, ItemCarritoView

urlpatterns = [
    path("carrito", CarritoView.as_view()),
    path("carrito/calcular", CarritoCalcularView.as_view()),
    path("carrito/combinar", CombinarCarritoView.as_view()),
    path("carrito/items/<str:producto_id>", ItemCarritoView.as_view()),
    path("checkout", CheckoutView.as_view()),
]
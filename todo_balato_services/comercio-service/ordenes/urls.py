from django.urls import path
from .views import CarritoCalcularView, CheckoutView
<<<<<<< HEAD
from .views_pagos import IniciarPagoView, ReverificarPagoView, retorno_webpay
=======
from .carrito_views import CarritoView, CombinarCarritoView, ItemCarritoView
>>>>>>> d95303ebc4943a970bd0d320c887f2e49e2fd7e9

urlpatterns = [
    path("carrito", CarritoView.as_view()),
    path("carrito/calcular", CarritoCalcularView.as_view()),
    path("carrito/combinar", CombinarCarritoView.as_view()),
    path("carrito/items/<str:producto_id>", ItemCarritoView.as_view()),
    path("checkout", CheckoutView.as_view()),
    path("pagos/iniciar", IniciarPagoView.as_view()),
    path("pagos/webpay/retorno", retorno_webpay),
    path("pagos/<uuid:orden_id>/reverificar", ReverificarPagoView.as_view()),
]
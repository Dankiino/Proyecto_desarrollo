# Contrato de API: Checkout y pago

Proyecto de comercio electrónico · Solemne 02 · Backend · Versión 0.1 (propuesta) · 17-10-2026

## Propósito

Este documento define cómo el frontend inicia un pago y consulta su resultado, y cómo se comunican Comercio y Catálogo para reservar stock. Cubre RF-25, RF-27 a RF-35. Usa las convenciones comunes (dinero en CLP como entero, errores, autenticación) del documento "Contratos de API: convenciones y Catálogo". Todo lo marcado como propuesta debe ser aprobado por el equipo.

## Flujo visto desde el frontend

1. El frontend muestra el carrito y sus totales con POST /api/carrito/calcular.
2. Si el cliente no ha iniciado sesión, se autentica en Gestión y vuelve al carrito.
3. Al presionar Pagar, el frontend llama a POST /api/checkout.
4. Si responde 201, el frontend redirige el navegador a la dirección de pago que vino en la respuesta.
5. El cliente paga en Webpay. Webpay lo devuelve al backend de Comercio, que verifica el pago y redirige al cliente a la página de la orden.
6. El frontend consulta GET /api/ordenes/{id} y muestra el resultado según el estado de la orden.

Regla de fondo: el frontend nunca da una compra por aprobada por lo que diga la URL o el navegador. Solo vale el estado que devuelve GET /api/ordenes/{id}.

## Resumen de endpoints

Todos pertenecen al servicio de Comercio.

| Método y URL | Quién lo llama | Para qué |
| --- | --- | --- |
| POST /api/carrito/calcular | Visitante o cliente | Calcular subtotales y total con precios vigentes (RF-25) |
| POST /api/checkout | Cliente activo | Validar el carrito, crear la orden, reservar stock e iniciar el pago (RF-27 a RF-31) |
| GET o POST /api/pagos/webpay/retorno | Webpay, a través del navegador | Verificar el pago y confirmar la orden (RF-32 a RF-34). React no lo llama |
| GET /api/ordenes/{id} | Cliente dueño de la orden | Consultar resumen y estado (RF-35) |

## POST /api/carrito/calcular

Calcula los importes del carrito. Es público, porque el carrito anónimo vive en el navegador y no reserva stock (RB-01). El precio siempre lo toma el backend desde Catálogo; cualquier precio que envíe el navegador se ignora.

Petición:

```json
{
  "items": [
    { "producto_id": "6710f3a2c4b1e5a7d8f90123", "cantidad": 2 },
    { "producto_id": "6710f3a2c4b1e5a7d8f90124", "cantidad": 1 }
  ]
}
```

Respuesta 200:

```json
{
  "moneda": "CLP",
  "lineas": [
    {
      "producto_id": "6710f3a2c4b1e5a7d8f90123",
      "nombre": "Producto de ejemplo A",
      "precio_unitario": 12990,
      "cantidad": 2,
      "subtotal": 25980,
      "problema": null
    },
    {
      "producto_id": "6710f3a2c4b1e5a7d8f90124",
      "nombre": "Producto de ejemplo B",
      "precio_unitario": 24990,
      "cantidad": 1,
      "subtotal": 24990,
      "problema": "agotado"
    }
  ],
  "total": 25980,
  "puede_pagar": false
}
```

Reglas:

- problema vale null o uno de: agotado, stock\_insuficiente, inactivo, no\_existe.
- total suma solo las líneas sin problema. puede\_pagar es true solo si ninguna línea tiene problema.
- Responde 200 aunque haya líneas con problema, para que el frontend las muestre. Responde 400 si items está vacío o si una cantidad no es un entero positivo.
- El mismo producto repetido en items se suma en una sola línea.

## POST /api/checkout

Inicia la compra. Requiere un cliente activo (CC-02): un administrador recibe 403. En una sola llamada el backend revalida el carrito, crea la orden con los datos históricos, reserva el stock por 15 minutos y crea la transacción en Webpay.

Cabeceras:

- Authorization: Bearer TOKEN
- Idempotency-Key: un UUID que genera el frontend para cada intento de pago. Si el cliente hace doble clic o se reintenta por un fallo de red, se envía el mismo valor y el backend devuelve la misma orden, sin duplicar nada (RF-28 y RF-31).

Petición:

```json
{
  "items": [
    { "producto_id": "6710f3a2c4b1e5a7d8f90123", "cantidad": 2 }
  ],
  "total_esperado": 25980
}
```

total\_esperado es el total que el cliente vio en pantalla. No se usa para cobrar: el backend calcula el total válido y solo lo compara. Si difieren, responde 409 para que el cliente vea el importe actualizado antes de continuar (RF-27).

Respuesta 201 (orden creada):

```json
{
  "orden": {
    "id": "b3f1c2d4-8a6e-4c1f-9d2b-5e7a1c0f3b48",
    "estado": "PENDIENTE_PAGO",
    "moneda": "CLP",
    "lineas": [
      {
        "producto_id": "6710f3a2c4b1e5a7d8f90123",
        "nombre": "Producto de ejemplo A",
        "precio_unitario": 12990,
        "cantidad": 2,
        "subtotal": 25980
      }
    ],
    "total": 25980,
    "creada_en": "2026-10-17T14:30:00Z"
  },
  "reserva": { "expira_en": "2026-10-17T14:45:00Z" },
  "pago": {
    "proveedor": "webpay_plus",
    "url": "https://webpay3gint.transbank.cl/webpayserver/initTransaction",
    "token": "01ab0123456789abcdef"
  }
}
```

Repetir la misma petición con la misma Idempotency-Key responde 200 con la misma orden.

Para llevar al cliente a pagar, el frontend redirige el navegador a pago.url enviando el token como token\_ws. La documentación de Transbank indica que esa redirección debe hacerse por POST, con un formulario. En las pruebas con el sandbox, abrir la dirección con ?token\_ws= (GET) también abrió el formulario y permitió completar el pago, pero se recomienda el formulario POST: es lo que documenta Transbank y no depende de que el sandbox sea permisivo. La prueba con el formulario POST también funcionó en el sandbox: abrió el formulario de Webpay y el pago se pudo confirmar.

Ejemplo en React:

```javascript
const f = document.createElement("form");
f.method = "POST";
f.action = datos.pago.url;
const i = document.createElement("input");
i.type = "hidden";
i.name = "token_ws";
i.value = datos.pago.token;
f.appendChild(i);
document.body.appendChild(f);
f.submit();
```

Errores (formato común):

| HTTP | codigo | Cuándo | Qué hace el frontend |
| --- | --- | --- | --- |
| 400 | validacion | items vacío, cantidades inválidas o falta la cabecera Idempotency-Key | Mostrar los campos afectados |
| 401 | no\_autenticado | Sin sesión | Llevar a iniciar sesión y volver al carrito |
| 403 | no\_autorizado | Administrador o usuario bloqueado | Mostrar mensaje |
| 409 | carrito\_inconsistente | Hay productos agotados, inactivos o sin stock suficiente | Mostrar el carrito que viene en el error |
| 409 | precio\_cambiado | total\_esperado no coincide con el total actual | Mostrar el nuevo total y pedir confirmación |
| 409 | conflicto | La misma Idempotency-Key se usó con un cuerpo distinto | Generar una clave nueva |
| 502 | pasarela\_no\_disponible | No se pudo crear el pago en Webpay | Reintentar con la misma Idempotency-Key |
| 503 | servicio\_no\_disponible | Catálogo no responde. No se creó nada | Reintentar más tarde |

En los dos 409 sobre el carrito, el error trae un campo carrito con la misma estructura de la respuesta de POST /api/carrito/calcular:

```json
{
  "error": {
    "codigo": "precio_cambiado",
    "mensaje": "El total del carrito cambió.",
    "carrito": { "moneda": "CLP", "lineas": [], "total": 27980, "puede_pagar": true }
  }
}
```

En el 502, la orden ya existe en estado PENDIENTE\_PAGO con su reserva activa. El error trae orden\_id y reintentable: true, y la orden vence a los 15 minutos si no se paga.

## Retorno de Webpay (React no lo llama)

GET o POST /api/pagos/webpay/retorno es la dirección a la que Webpay devuelve el navegador del cliente. Apunta al backend y no al frontend, por una razón práctica: una aplicación React estática no puede recibir un POST, y la verificación del pago debe ocurrir en el servidor (RF-32).

| Qué llega | Qué hace el backend | Estado de la orden |
| --- | --- | --- |
| token\_ws | Confirma el pago con Webpay y valida estado, código de respuesta, monto y orden. Si es válido, consolida la reserva | CONFIRMADA, o CONFIRMACION\_PENDIENTE si falla la consolidación |
| token\_ws con pago no autorizado | Libera la reserva | RECHAZADA |
| TBK\_TOKEN (el cliente canceló o venció el tiempo) | Libera la reserva | CANCELADA |

En los tres casos responde con una redirección (302) a la página de la orden en el frontend, por ejemplo /orden/b3f1c2d4-8a6e-4c1f-9d2b-5e7a1c0f3b48. La dirección no lleva datos sensibles ni el resultado: el frontend siempre consulta el estado real. Repetir la misma llamada no duplica la orden ni el descuento de stock (RB-09).

### Resultados de las pruebas con el sandbox (18-10-2026)

| Prueba | Resultado |
| --- | --- |
| Redirección por GET (url con ?token\_ws=) y por POST (formulario) | En ambos casos abre el formulario de Webpay, permite completar el pago y se confirma con commit |
| Retorno de un pago exitoso y de uno cancelado | Ambos llegan por GET a la return\_url. El exitoso trae solo token\_ws. El cancelado (botón de anular compra) trae TBK\_TOKEN, TBK\_ORDEN\_COMPRA y TBK\_ID\_SESION, sin token\_ws |
| Estado con el pago ya hecho y antes del commit | INITIALIZED, sin código de autorización |
| commit inmediato tras el pago | AUTHORIZED, response\_code 0 |
| commit sobre una transacción que no se completó | Error 422 con el estado aborted |
| Espera prolongada antes del commit | Pendientes de probar |

Conclusiones para el backend:

- Que llegue token\_ws no significa que el pago esté aprobado. Tanto una aprobación como un rechazo llegan solo con token\_ws. Solo el resultado de commit decide.
- El retorno llegó por GET en las pruebas, tanto en el pago exitoso como en el cancelado. El endpoint debe aceptar GET y POST, y distinguir los casos por los parámetros: con TBK\_TOKEN no se llama a commit y la orden pasa a CANCELADA. El backend identifica la orden por el token que guardó al crear la transacción, no por los demás parámetros que llegan en la URL.
- El navegador también pide /favicon.ico a la misma dirección. El endpoint debe ignorarlo.
- INITIALIZED no distingue entre un pago hecho que falta confirmar y uno que venció sin completarse. Por eso la decisión se toma con el resultado de commit:

| commit responde | La orden pasa a |
| --- | --- |
| AUTHORIZED | Se consolida el stock y queda CONFIRMADA |
| Estado no autorizado | RECHAZADA, y se libera la reserva |
| Error 422 (aborted) | CANCELADA o VENCIDA, y se libera la reserva |

Si commit lanza un error, Comercio debe capturarlo y consultar status, sin dar la compra por exitosa.

## GET /api/ordenes/{id}

Requiere el token del cliente dueño de la orden. Una orden ajena o inexistente responde 404 con la misma respuesta, para no revelar su existencia (RF-35).

Respuesta 200:

```json
{
  "id": "b3f1c2d4-8a6e-4c1f-9d2b-5e7a1c0f3b48",
  "estado": "CONFIRMADA",
  "estado_pago": "APROBADO",
  "moneda": "CLP",
  "lineas": [
    {
      "producto_id": "6710f3a2c4b1e5a7d8f90123",
      "nombre": "Producto de ejemplo A",
      "precio_unitario": 12990,
      "cantidad": 2,
      "subtotal": 25980
    }
  ],
  "total": 25980,
  "creada_en": "2026-10-17T14:30:00Z",
  "confirmada_en": "2026-10-17T14:36:12Z",
  "reserva_expira_en": null
}
```

Las líneas conservan el nombre y el precio del momento de la compra, aunque el producto cambie después (RB-08). estado\_pago vale PENDIENTE, APROBADO o RECHAZADO. confirmada\_en es null mientras la orden no esté confirmada, y reserva\_expira\_en solo tiene valor en PENDIENTE\_PAGO.

Qué debe mostrar el frontend según el estado:

| estado | Qué mostrar |
| --- | --- |
| PENDIENTE\_PAGO | Esperando el pago, con la cuenta regresiva hasta reserva\_expira\_en |
| CONFIRMACION\_PENDIENTE | Pago recibido, estamos confirmando tu compra. No mostrarla como completada. Volver a consultar cada pocos segundos |
| CONFIRMADA | Compra confirmada, con el resumen |
| RECHAZADA | Pago rechazado, con opción de volver al carrito |
| CANCELADA | Pago cancelado, con opción de volver al carrito |
| VENCIDA | La reserva venció, con opción de volver al carrito |
| REVISION\_REQUERIDA | Estamos revisando tu pago y te avisaremos. No mostrarla como completada |

## Contratos internos: Comercio hacia Catálogo

Estos endpoints no los usa el frontend. Los llama Comercio y se autentican con un token de servicio (propuesta: un secreto compartido, guardado como variable de entorno).

| Método y URL | Para qué |
| --- | --- |
| POST /api/interno/productos/validar | Pedir precio vigente, estado y stock disponible de una lista de productos |
| POST /api/interno/reservas | Reservar todas las líneas de una orden, o ninguna |
| GET /api/interno/reservas/{id} | Consultar el estado de una reserva, para la conciliación |
| POST /api/interno/reservas/{id}/consolidar | Descontar el stock tras un pago verificado |
| POST /api/interno/reservas/{id}/liberar | Devolver el stock por rechazo, cancelación o vencimiento |

Crear una reserva. El reserva\_id es el id de la orden, así repetir la llamada no reserva dos veces:

```json
{
  "reserva_id": "b3f1c2d4-8a6e-4c1f-9d2b-5e7a1c0f3b48",
  "lineas": [
    { "producto_id": "6710f3a2c4b1e5a7d8f90123", "cantidad": 2 }
  ]
}
```

Respuesta 201 (200 si la reserva ya existía con los mismos datos):

```json
{
  "reserva_id": "b3f1c2d4-8a6e-4c1f-9d2b-5e7a1c0f3b48",
  "estado": "ACTIVA",
  "expira_en": "2026-10-17T14:45:00Z"
}
```

Reglas:

- Si alguna línea no tiene stock, responde 409 con codigo sin\_stock y las líneas afectadas con su stock\_disponible. No queda ninguna reserva parcial.
- Usar el mismo reserva\_id con líneas distintas responde 409 con codigo conflicto.
- consolidar y liberar responden 200 con el estado final (CONSOLIDADA o LIBERADA). Repetirlos devuelve el mismo estado sin volver a descontar.
- consolidar sobre una reserva ya liberada o vencida responde 409 con codigo reserva\_no\_disponible. Comercio marca entonces la orden como REVISION\_REQUERIDA.

## Cómo simular desde el día uno

El frontend puede probar el flujo completo con un mock, como en el contrato del Catálogo. Para el pago, el mock de POST /api/checkout devuelve en pago.url la dirección de una página local de prueba, que simula el retorno y redirige a /orden/{id}. Los JSON de este documento sirven como respuestas fijas, una por cada estado de la tabla.

## Decisiones abiertas para el equipo

- Retorno de Webpay: que apunte al backend, que luego redirige al frontend (propuesta), o directo a una página del frontend.
- Carrito autenticado: RF-26 habla de combinar el carrito anónimo con uno previo del cliente. Este contrato asume que el frontend envía los items en cada llamada. Si Comercio guarda el carrito en el servidor, se agregan endpoints de carrito.
- Cabecera Idempotency-Key: confirmar que el frontend la enviará en cada intento de pago.
- Autenticación entre servicios: secreto compartido (propuesta) u otro mecanismo.
- Redirección a Webpay: usar un formulario POST, según la documentación de Transbank. Probado en el sandbox: abre el formulario y el pago se confirma.
- Duración de la reserva: 15 minutos, sujeta al tiempo del formulario de Webpay y al plazo para confirmar el pago. Pendiente: medir en el sandbox cuánto se puede esperar entre el pago y el commit (pruebas con 5, 10 y 15 minutos) y confirmar esos plazos en la documentación de Transbank.
- Fuera de esta versión: endpoints administrativos de correos y conciliación (RF-37 y RF-38) y listado de órdenes del cliente.

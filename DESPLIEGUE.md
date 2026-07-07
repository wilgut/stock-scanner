# Cómo publicar el Scanner en internet (gratis)

El objetivo: que la app tenga una dirección web propia (ej. `https://scanner-acciones.onrender.com`)
para abrirla desde tu PC, tu MacBook o tu iPhone sin encender nada.

Usaremos **Render.com** (plan gratuito). Solo se hace una vez, toma unos 15 minutos.

## Paso 1 — Crear cuenta en GitHub (si no tienes)

1. Entra a https://github.com y pulsa **Sign up**.
2. Usa tu correo y crea una contraseña. Es gratis.

## Paso 2 — Subir el código a GitHub

1. Ya dentro de GitHub, pulsa el botón verde **New** (nuevo repositorio).
2. Nombre: `stock-scanner`. Déjalo en **Public**. Pulsa **Create repository**.
3. En la página que aparece, pulsa el enlace **uploading an existing file**.
4. Abre la carpeta `C:\Users\Wilfred\Trading Claude\stock-scanner` en el
   Explorador de Windows y arrastra TODO su contenido (incluida la carpeta
   `templates`) a la ventana de GitHub.
5. Pulsa el botón verde **Commit changes**.

## Paso 3 — Crear el servicio en Render

1. Entra a https://render.com y pulsa **Get Started** → **Sign in with GitHub**
   (así conecta con tu cuenta de GitHub automáticamente).
2. Pulsa **New +** → **Blueprint**.
3. Elige el repositorio `stock-scanner` y pulsa **Connect**.
4. Render lee el archivo `render.yaml` y configura todo solo. Pulsa **Apply**.
5. Espera 3-5 minutos. Al terminar verás la dirección web, algo como:
   `https://scanner-acciones.onrender.com`

## Paso 4 — Guardar el acceso en tus dispositivos

- **iPhone**: abre la dirección en Safari → botón Compartir → **Añadir a
  pantalla de inicio**. Queda como una app más.
- **PC / MacBook**: guárdala en favoritos del navegador.

## Cosas que debes saber del plan gratuito

- Si nadie usa la app durante 15 minutos, Render la "duerme". La siguiente
  visita tarda ~1 minuto en despertar. Después va rápida. Es normal.
- Si algún día quieres que nunca duerma, el plan de pago más barato de Render
  cuesta 7 USD/mes. No es necesario.

## Opcional — Datos en tiempo real con tu cuenta Premium

Sin hacer nada, los datos llegan con ~15 minutos de retraso (suficiente para
scans diarios/semanales). Si quieres tiempo real:

1. En tu PC, entra a tradingview.com con tu cuenta Premium.
2. Pulsa F12 → pestaña **Application** → **Cookies** → `https://es.tradingview.com`
   → copia el valor de la cookie llamada `sessionid`.
3. En Render: tu servicio → **Environment** → **Add Environment Variable**:
   - Key: `TV_SESSIONID`
   - Value: (pega el valor copiado)
4. Pulsa **Save Changes**. La cookie caduca cada cierto tiempo; si vuelven los
   datos con retraso, repite estos pasos.

## ¿Prefieres que lo haga contigo?

Pídemelo en una próxima sesión: puedo guiarte pantalla por pantalla o hacerlo
directamente usando tu navegador Chrome.

# Cómo publicar el Scanner en internet

El objetivo: que la app tenga una dirección web propia para abrirla desde tu
PC, tu MacBook o tu iPhone sin encender nada.

Ya tienes cuentas en GitHub, Vercel y Railway. La app está preparada para las
tres cosas: solo hay que subir el código a GitHub (una vez) y conectarlo.

**Recomendación: usa Vercel.** Es gratis de verdad y la app nunca "se duerme".
Railway funciona igual de bien, pero tras el crédito de prueba de $5 pasa a
costar ~$5/mes.

## Paso 1 — Subir el código a GitHub (solo la primera vez)

1. Entra a https://github.com y pulsa el botón verde **New** (nuevo repositorio).
2. Nombre: `stock-scanner`. Déjalo en **Public** (o Private, ambos funcionan).
   Pulsa **Create repository**.
3. En la página que aparece, pulsa el enlace **uploading an existing file**.
4. Abre la carpeta `C:\Users\Wilfred\Trading Claude\stock-scanner` en el
   Explorador de Windows y arrastra TODO su contenido (incluida la carpeta
   `templates`) a la ventana de GitHub.
5. Pulsa el botón verde **Commit changes**.

> Cuando hagamos mejoras a la app, repite los pasos 3-5 para actualizar los
> archivos: Vercel/Railway republican solos en 1-2 minutos.

## Paso 2 — Publicar en Vercel (recomendado, gratis)

1. Entra a https://vercel.com con tu cuenta.
2. Pulsa **Add New…** → **Project**.
3. En la lista de repositorios de GitHub, busca `stock-scanner` y pulsa
   **Import**. (Si no aparece, pulsa "Adjust GitHub App Permissions" y dale
   acceso al repositorio.)
4. No cambies nada y pulsa **Deploy**. Vercel detecta Flask automáticamente.
5. En 1-2 minutos verás tu dirección, algo como:
   `https://stock-scanner-xxxx.vercel.app`

Nota: si la app lleva un rato sin usarse, la primera consulta puede tardar
5-10 segundos (arranque en frío). Las siguientes van rápidas.

## Alternativa — Publicar en Railway

1. Entra a https://railway.app con tu cuenta.
2. **New Project** → **Deploy from GitHub repo** → elige `stock-scanner`.
3. Cuando termine el despliegue, entra al servicio → pestaña **Settings** →
   sección **Networking** → pulsa **Generate Domain**.
4. Esa es tu dirección pública, algo como
   `https://stock-scanner-production-xxxx.up.railway.app`

## Paso 3 — Guardar el acceso en tus dispositivos

- **iPhone**: abre la dirección en Safari → botón Compartir → **Añadir a
  pantalla de inicio**. Queda como una app más.
- **PC / MacBook**: guárdala en favoritos del navegador.

## Opcional — Datos en tiempo real con tu cuenta Premium

Sin configurar nada, los datos llegan con ~15 minutos de retraso (suficiente
para señales diarias/semanales; para las temporalidades de 15 min o 1 hora
conviene el tiempo real):

1. En tu PC, entra a tradingview.com con tu cuenta Premium.
2. Pulsa F12 → pestaña **Application** → **Cookies** →
   `https://es.tradingview.com` → copia el valor de la cookie `sessionid`.
3. Añade la variable de entorno en tu plataforma:
   - **Vercel**: tu proyecto → **Settings** → **Environment Variables** →
     Key: `TV_SESSIONID`, Value: (lo copiado) → **Save** → redespliega
     (Deployments → ⋯ → Redeploy).
   - **Railway**: tu servicio → pestaña **Variables** → **New Variable** →
     `TV_SESSIONID` = (lo copiado).
4. La cookie caduca cada cierto tiempo; si vuelven los datos con retraso,
   repite estos pasos.

## ¿Prefieres que lo haga contigo?

Pídemelo en una próxima sesión: puedo guiarte pantalla por pantalla o hacerlo
directamente usando tu navegador Chrome.

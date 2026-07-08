# Guía de uso local (tiempo real) — PC Windows y MacBook

La versión web (https://stock-scanner-six-delta.vercel.app) funciona desde
cualquier dispositivo pero con ~15 minutos de retraso, porque TradingView
bloquea las sesiones Premium desde servidores en la nube. Para operar con
**temporalidades bajas (15 min / 1 hora) en tiempo real**, usa la app en
local como explica esta guía.

---

## 🖥️ En el PC Windows (ya está todo instalado)

1. Abre la carpeta `C:\Users\Wilfred\Trading Claude\stock-scanner`
2. Doble clic en **`Iniciar Scanner.bat`** → se abre una ventana negra (es el
   motor: **no la cierres, solo minimízala**) y el navegador se abre solo.
3. Si Windows pregunta "¿Permitir que Python acceda a la red?", pulsa
   **Permitir acceso** (necesario para usar el Mac/iPhone por WiFi).
4. Para apagarlo: cierra la ventana negra.

La cookie Premium está guardada en `tv_sessionid.txt` (junto al .bat), así que
los datos son **en tiempo real**. Si TradingView cierra la sesión (pasa cada
cierto tiempo), pide a Claude actualizar la cookie.

## ⏱️ Cómo usar las temporalidades bajas

En la sección **"Mis Scans"**, arriba de las tarjetas, está el selector
**"Temporalidad (señal rápida + confirmación lenta)"**:

| Par | Uso típico |
|---|---|
| 15 min + 1 hora | Day trading: el cruce aparece en 15 min y la hora confirma |
| 1 hora + 4 horas | Swing muy corto |
| 4 horas + Diario | Swing corto (2-10 días) |
| Diario + Semanal | Posición (configuración original) |
| Semanal + Mensual | Largo plazo |

Eliges el par, pulsas "Ejecutar scan" y las columnas RSI de la tabla se
adaptan. Para 15 min / 1 hora usa siempre la app local, no la web.

## 💻 MacBook — Opción A: sin instalar nada (misma WiFi que el PC)

Con el scanner corriendo en el PC:

1. En el Mac, abre Safari o Chrome y entra a **http://10.18.167.106:8877**
2. Listo — usas el scanner del PC con su tiempo real. La misma URL funciona
   en el **iPhone** conectado a la WiFi de casa.

Nota: la dirección (10.18.167.106) puede cambiar si el router la reasigna.
Para verla de nuevo: en el PC, tecla Windows → escribir `cmd` → Enter →
escribir `ipconfig` → buscar "Dirección IPv4". O pídesela a Claude.

## 💻 MacBook — Opción B: instalación propia (para usarla en cualquier parte)

Solo la primera vez (~10 minutos):

1. **Instalar Python**: https://www.python.org/downloads → botón amarillo
   "Download Python" → abrir el archivo descargado → Continuar hasta el final.
2. **Descargar la app**: https://github.com/wilgut/stock-scanner → botón verde
   **Code** → **Download ZIP** → doble clic al ZIP para descomprimir → mover
   la carpeta `stock-scanner-main` a Documentos.
3. **Primer arranque**: clic derecho (o Ctrl+clic) sobre
   **`Iniciar Scanner Mac.command`** → **Abrir** → confirmar **Abrir** en el
   aviso de seguridad. (Si macOS lo bloquea: Configuración del Sistema →
   Privacidad y Seguridad → "Abrir de todos modos", solo esa vez.)
4. La Terminal prepara la app (1-2 min) y pide el **sessionid** para tiempo
   real. Cópialo desde TradingView en el Mac: Chrome → menú ⋮ → Más
   herramientas → Herramientas para desarrolladores → pestaña **Application**
   → **Cookies** → tradingview.com → fila **`sessionid`** → copiar el valor y
   pegarlo en la Terminal. (Si se deja vacío, funciona con ~15 min de retraso.)
5. El navegador se abre solo. **Las siguientes veces**: doble clic normal.

Para actualizar la app en el Mac más adelante: descargar de nuevo el ZIP y
reemplazar la carpeta (conservando `tv_sessionid.txt` si existe).

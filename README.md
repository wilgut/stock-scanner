# Scanner de Acciones

App en producción: https://stock-scanner-six-delta.vercel.app (se redespliega
automáticamente con cada cambio subido a GitHub).

Web app de scans de stock picking con datos del screener de TradingView
(NYSE, NASDAQ, AMEX). Incluye scans propios de doble marco temporal
(MACD y RSI diario + semanal) y scans institucionales clásicos
(Minervini, CANSLIM, Golden Cross, ruptura de 52 semanas, volumen inusual,
gap alcista, rebote sobrevendido, pullback a la SMA 50).

## Uso local con tiempo real (PC, Mac, temporalidades bajas)

Ver [USO-LOCAL.md](USO-LOCAL.md) — guía paso a paso.

## Ejecutar en esta PC

Doble clic en `Iniciar Scanner.bat`, o en una terminal:

```
python app.py
```

Luego abrir http://localhost:8877

## Publicar en internet

Ver [DESPLIEGUE.md](DESPLIEGUE.md) — guía paso a paso para GitHub + Vercel
(recomendado, gratis) o Railway (alternativa). La app incluye `vercel.json`
(Vercel) y `Procfile` (Railway), listos para ambas plataformas.

## Datos

- Fuente: API pública del screener de TradingView (librería `tradingview-screener`).
- Sin configurar nada: datos con ~15 min de retraso.
- Con la variable de entorno `TV_SESSIONID` (cookie de cuenta Premium): tiempo real.

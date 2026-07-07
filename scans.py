"""
Definición de los scans de stock picking.

Todos los scans consultan el screener oficial de TradingView (el mismo motor
que usa la página tradingview.com/screener) a través de la librería
tradingview-screener. No requiere login; si se define la variable de entorno
TV_SESSIONID (cookie sessionid de una cuenta Premium) los datos se obtienen
en tiempo real en lugar de con retraso de 15 minutos.
"""
import os

from tradingview_screener import Query, col

EXCHANGES = ['NASDAQ', 'NYSE', 'AMEX']

# Columnas que se devuelven en todos los scans
COLUMNS = [
    'name', 'description', 'close', 'change', 'volume',
    'relative_volume_10d_calc', 'market_cap_basic', 'sector',
    'RSI', 'RSI|1W', 'Perf.3M', 'Perf.Y',
]

SCANS = {
    # ------------------------- MIS SCANS -------------------------
    'macd_doble': {
        'nombre': 'MACD Doble: Diario + Semanal',
        'categoria': 'Mis Scans',
        'descripcion': 'La línea MACD diaria cruza HOY por encima de su señal, '
                       'y la MACD semanal ya está en tendencia positiva (por '
                       'encima de su señal). Confirma el giro diario con el '
                       'marco semanal.',
        'condiciones': lambda: [
            col('MACD.macd').crosses_above(col('MACD.signal')),
            col('MACD.macd|1W') > col('MACD.signal|1W'),
        ],
        'orden': 'volume',
    },
    'macd_doble_estricto': {
        'nombre': 'MACD Doble Estricto (cruce simultáneo)',
        'categoria': 'Mis Scans',
        'descripcion': 'La MACD diaria Y la semanal cruzan a positivo en la '
                       'misma sesión/semana. Señal muy poco frecuente pero muy '
                       'potente: puede dar 0 resultados muchos días.',
        'condiciones': lambda: [
            col('MACD.macd').crosses_above(col('MACD.signal')),
            col('MACD.macd|1W').crosses_above(col('MACD.signal|1W')),
        ],
        'orden': 'volume',
    },
    'rsi_doble': {
        'nombre': 'RSI Doble: Diario + Semanal',
        'categoria': 'Mis Scans',
        'descripcion': 'El RSI diario cruza HOY por encima de 50 (giro a '
                       'tendencia positiva) y el RSI semanal ya está por encima '
                       'de 50. Momentum alcista en ambos marcos temporales.',
        'condiciones': lambda: [
            col('RSI').crosses_above(50),
            col('RSI|1W') > 50,
        ],
        'orden': 'volume',
    },

    # -------------------- SCANS INSTITUCIONALES --------------------
    'minervini': {
        'nombre': 'Minervini — Trend Template (Fase 2)',
        'categoria': 'Institucionales',
        'descripcion': 'Mark Minervini (campeón US Investing Championship): '
                       'precio sobre la media de 50, medias apiladas '
                       '50 > 100 > 200, rendimiento 6 meses > 15% y RSI > 50. '
                       'Detecta acciones en fase 2 de tendencia alcista.',
        'condiciones': lambda: [
            col('close') > col('SMA50'),
            col('SMA50') > col('SMA100'),
            col('SMA100') > col('SMA200'),
            col('Perf.6M') > 15,
            col('RSI') > 50,
        ],
        'orden': 'Perf.6M',
    },
    'canslim': {
        'nombre': "CANSLIM — William O'Neil (aprox.)",
        'categoria': 'Institucionales',
        'descripcion': "Metodología de William O'Neil (Investor's Business "
                       'Daily): crecimiento de beneficios (BPA) interanual '
                       '> 25%, momentum de 3 meses > 15% y precio sobre la '
                       'media de 50. Crecimiento + fuerza técnica.',
        'condiciones': lambda: [
            col('earnings_per_share_diluted_yoy_growth_fq') > 25,
            col('Perf.3M') > 15,
            col('close') > col('SMA50'),
        ],
        'orden': 'Perf.3M',
    },
    'golden_cross': {
        'nombre': 'Golden Cross (SMA 50 cruza SMA 200)',
        'categoria': 'Institucionales',
        'descripcion': 'El cruce dorado clásico que siguen los fondos: la media '
                       'de 50 días cruza por encima de la de 200. Señal de '
                       'cambio de tendencia de largo plazo. Poco frecuente.',
        'condiciones': lambda: [
            col('SMA50').crosses_above(col('SMA200')),
        ],
        'orden': 'volume',
    },
    'ruptura_52s': {
        'nombre': 'Ruptura de máximo de 52 semanas',
        'categoria': 'Institucionales',
        'descripcion': 'Acciones cerrando en su máximo de 52 semanas. Favorita '
                       'de los momentum traders institucionales: "los máximos '
                       'históricos atraen más máximos". Ordenado por volumen '
                       'relativo para priorizar rupturas con participación.',
        'condiciones': lambda: [
            col('close') >= col('price_52_week_high'),
        ],
        'orden': 'relative_volume_10d_calc',
    },
    'volumen_inusual': {
        'nombre': 'Volumen inusual con subida',
        'categoria': 'Institucionales',
        'descripcion': 'Volumen relativo mayor a 3 veces su promedio de 10 días '
                       'con subida > 2%. El volumen anormal delata acumulación '
                       'institucional: "el volumen precede al precio".',
        'condiciones': lambda: [
            col('relative_volume_10d_calc') > 3,
            col('change') > 2,
        ],
        'orden': 'relative_volume_10d_calc',
    },
    'gap_alcista': {
        'nombre': 'Gap alcista con volumen',
        'categoria': 'Institucionales',
        'descripcion': 'Apertura con hueco (gap) mayor al 3% que se mantiene en '
                       'positivo, con volumen relativo alto. Scan típico de '
                       'traders de momentum para detectar catalizadores '
                       '(resultados, noticias, upgrades).',
        'condiciones': lambda: [
            col('gap') > 3,
            col('change') > 0,
            col('relative_volume_10d_calc') > 1.5,
        ],
        'orden': 'gap',
    },
    'rebote_sobrevendido': {
        'nombre': 'Rebote sobrevendido en tendencia alcista',
        'categoria': 'Institucionales',
        'descripcion': 'Estilo Larry Connors: el RSI diario sale HOY de zona de '
                       'sobreventa (cruza 30 al alza) en una acción que sigue '
                       'por encima de su media de 200. Comprar el susto dentro '
                       'de la tendencia.',
        'condiciones': lambda: [
            col('RSI').crosses_above(30),
            col('close') > col('SMA200'),
        ],
        'orden': 'volume',
    },
    'pullback_sma50': {
        'nombre': 'Pullback a la media de 50',
        'categoria': 'Institucionales',
        'descripcion': 'Acción fuerte (rendimiento 6 meses > 15%, medias 50>200) '
                       'que retrocede: precio por debajo de la media de 20 pero '
                       'aguantando sobre la de 50. Zona clásica de recompra '
                       'institucional.',
        'condiciones': lambda: [
            col('SMA50') > col('SMA200'),
            col('close') > col('SMA50'),
            col('close') < col('SMA20'),
            col('Perf.6M') > 15,
        ],
        'orden': 'Perf.6M',
    },
}


def _cookies():
    sid = os.environ.get('TV_SESSIONID', '').strip()
    return {'sessionid': sid} if sid else None


def run_scan(scan_id, min_price=5.0, min_volume=500_000, limit=60):
    """Ejecuta un scan y devuelve (total, lista de dicts)."""
    scan = SCANS[scan_id]
    q = (
        Query()
        .set_markets('america')
        .select(*COLUMNS)
        .where(
            col('type') == 'stock',
            col('typespecs').has('common'),
            col('is_primary') == True,
            col('exchange').isin(EXCHANGES),
            col('close') > min_price,
            col('volume') > min_volume,
            *scan['condiciones'](),
        )
        .order_by(scan['orden'], ascending=False)
        .limit(limit)
    )
    count, df = q.get_scanner_data(cookies=_cookies())
    df = df.astype(object).where(df.notna(), None)
    return count, df.to_dict(orient='records')

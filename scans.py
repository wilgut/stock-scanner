"""
Definición de los scans de stock picking.

Todos los scans consultan el screener oficial de TradingView (el mismo motor
que usa la página tradingview.com/screener) a través de la librería
tradingview-screener. No requiere login; si se define la variable de entorno
TV_SESSIONID (cookie sessionid de una cuenta Premium) los datos se obtienen
en tiempo real en lugar de con retraso de 15 minutos.

Los scans con 'multi_tf': True aceptan un par de temporalidades
(rápida-lenta): la señal se busca en la rápida y la confirmación en la lenta.
"""
import os

from tradingview_screener import Query, col

EXCHANGES = ['NASDAQ', 'NYSE', 'AMEX']

# Pares de temporalidad: clave -> (sufijo rápido, sufijo lento, etiqueta rápida, etiqueta lenta)
# Sufijo vacío = diario (el marco por defecto del screener).
TF_PAIRS = {
    '15-60':  ('|15',  '|60',  '15m', '1H'),
    '60-240': ('|60',  '|240', '1H',  '4H'),
    '60-1D':  ('|60',  '',     '1H',  'D'),
    '240-1D': ('|240', '',     '4H',  'D'),
    '1D-1W':  ('',     '|1W',  'D',   'S'),
    '1W-1M':  ('|1W',  '|1M',  'S',   'M'),
}
TF_DEFAULT = '1D-1W'

COLUMNS_BASE = [
    'name', 'description', 'close', 'change', 'volume',
    'relative_volume_10d_calc', 'market_cap_basic', 'sector',
]

SCANS = {
    # ------------------------- MIS SCANS -------------------------
    'macd_doble': {
        'nombre': 'MACD Doble: señal + confirmación',
        'categoria': 'Mis Scans',
        'multi_tf': True,
        'descripcion': 'La línea MACD del marco rápido cruza AHORA por encima '
                       'de su señal, y la MACD del marco lento ya está en '
                       'tendencia positiva. Ej. Diario + Semanal: giro diario '
                       'confirmado por el semanal.',
        'condiciones': lambda f, s: [
            col(f'MACD.macd{f}').crosses_above(col(f'MACD.signal{f}')),
            col(f'MACD.macd{s}') > col(f'MACD.signal{s}'),
        ],
        'orden': 'volume',
    },
    'macd_doble_estricto': {
        'nombre': 'MACD Doble Estricto (cruce simultáneo)',
        'categoria': 'Mis Scans',
        'multi_tf': True,
        'descripcion': 'La MACD del marco rápido Y la del lento cruzan a '
                       'positivo a la vez. Señal muy poco frecuente pero muy '
                       'potente: puede dar 0 resultados muchos días.',
        'condiciones': lambda f, s: [
            col(f'MACD.macd{f}').crosses_above(col(f'MACD.signal{f}')),
            col(f'MACD.macd{s}').crosses_above(col(f'MACD.signal{s}')),
        ],
        'orden': 'volume',
    },
    'rsi_doble': {
        'nombre': 'RSI Doble: cruce de 50',
        'categoria': 'Mis Scans',
        'multi_tf': True,
        'descripcion': 'El RSI del marco rápido cruza AHORA por encima de 50 '
                       '(zona alcista) y el RSI del marco lento ya está por '
                       'encima de 50. Momentum positivo en ambos marcos.',
        'condiciones': lambda f, s: [
            col(f'RSI{f}').crosses_above(50),
            col(f'RSI{s}') > 50,
        ],
        'orden': 'volume',
    },
    'rsi_giro': {
        'nombre': 'RSI Giro Alcista (cualquier nivel)',
        'categoria': 'Mis Scans',
        'multi_tf': True,
        'descripcion': 'El RSI gira a tendencia positiva aunque esté por '
                       'debajo de 50: el RSI rápido de 7 periodos cruza por '
                       'encima del RSI de 14 en el marco rápido, y en el marco '
                       'lento ya giró. Detecta el cambio de momentum antes que '
                       'el cruce de 50.',
        'condiciones': lambda f, s: [
            col(f'RSI7{f}').crosses_above(col(f'RSI{f}')),
            col(f'RSI7{s}') > col(f'RSI{s}'),
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


def run_scan(scan_id, min_price=5.0, min_volume=500_000, tf=TF_DEFAULT, limit=60):
    """Ejecuta un scan y devuelve (total, filas, etiquetas RSI)."""
    scan = SCANS[scan_id]

    if scan.get('multi_tf'):
        if tf not in TF_PAIRS:
            tf = TF_DEFAULT
        fast, slow, lbl_fast, lbl_slow = TF_PAIRS[tf]
        condiciones = scan['condiciones'](fast, slow)
    else:
        fast, slow, lbl_fast, lbl_slow = TF_PAIRS[TF_DEFAULT]
        condiciones = scan['condiciones']()

    rsi_fast, rsi_slow = f'RSI{fast}', f'RSI{slow}'
    q = (
        Query()
        .set_markets('america')
        .select(*COLUMNS_BASE, rsi_fast, rsi_slow)
        .where(
            col('type') == 'stock',
            col('typespecs').has('common'),
            col('is_primary') == True,
            col('exchange').isin(EXCHANGES),
            col('close') > min_price,
            col('volume') > min_volume,
            *condiciones,
        )
        .order_by(scan['orden'], ascending=False)
        .limit(limit)
    )
    count, df = q.get_scanner_data(cookies=_cookies())
    df = df.rename(columns={rsi_fast: 'rsi_fast', rsi_slow: 'rsi_slow'})
    df = df.astype(object).where(df.notna(), None)
    etiquetas = {'rsi_fast': f'RSI {lbl_fast}', 'rsi_slow': f'RSI {lbl_slow}'}
    return count, df.to_dict(orient='records'), etiquetas

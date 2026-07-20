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
import time
import traceback

import pandas as pd
from tradingview_screener import And, Or, Query, col

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
    'relative_volume_10d_calc', 'market_cap_basic', 'sector', 'industry',
    'Perf.W', 'Perf.1M',
]

# Profundidad de historia disponible en el screener: el marco diario expone
# hasta 2 velas atrás ([1] y [2]); semanal, mensual e intradía solo 1 ([1]).
def _max_hist(tf):
    return 2 if tf == '' else 1


def _macd_evento(tf, modo, n):
    """Señal MACD en un marco: giro de la línea (1ª vela del cambio) o
    cruce sobre su señal dentro de las últimas n velas."""
    if modo == 'cruce':
        k = min(n, _max_hist(tf))
        return [
            col(f'MACD.macd{tf}') > col(f'MACD.signal{tf}'),
            col(f'MACD.macd[{k}]{tf}') <= col(f'MACD.signal[{k}]{tf}'),
        ]
    # giro: la línea MACD pasa de bajar a subir. Con 2 velas de historia
    # (marco diario) se confirma que venía bajando; en los demás marcos se
    # exige que el giro sea fresco: la línea sube pero sigue por debajo de
    # su señal, o la está cruzando justo ahora.
    conds = [col(f'MACD.macd{tf}') > col(f'MACD.macd[1]{tf}')]
    if _max_hist(tf) >= 2:
        conds.append(col(f'MACD.macd[1]{tf}') <= col(f'MACD.macd[2]{tf}'))
    else:
        conds.append(Or(
            col(f'MACD.macd{tf}') < col(f'MACD.signal{tf}'),
            col(f'MACD.macd[1]{tf}') <= col(f'MACD.signal[1]{tf}'),
        ))
    return conds


def _macd_confirmacion(tf, modo):
    """Marco lento ya en tendencia positiva (según el tipo de señal)."""
    if modo == 'giro':
        return [col(f'MACD.macd{tf}') > col(f'MACD.macd[1]{tf}')]
    return [col(f'MACD.macd{tf}') > col(f'MACD.signal{tf}')]


SCANS = {
    # ------------------------- MIS SCANS -------------------------
    'macd_doble': {
        'nombre': 'MACD Doble: señal + confirmación',
        'categoria': 'Mis Scans',
        'multi_tf': True,
        'descripcion': 'La MACD del marco rápido da señal AHORA — giro de la '
                       'línea (la 1ª vela del cambio de tendencia) o cruce '
                       'sobre su señal, según el selector — y la MACD del '
                       'marco lento ya está en tendencia positiva (reciente '
                       'o madura, no importa la antigüedad).',
        'condiciones': lambda f, s, modo, n: [
            *_macd_evento(f, modo, n),
            *_macd_confirmacion(s, modo),
        ],
        'orden': 'volume',
    },
    'macd_doble_estricto': {
        'nombre': 'MACD Doble Estricto: ambos giran en su última vela',
        'categoria': 'Mis Scans',
        'multi_tf': True,
        'verificar_giro': True,
        'descripcion': 'El MACD cambia a tendencia positiva en su ÚLTIMA vela '
                       'tanto en el marco mayor como en el menor. La app '
                       'verifica el giro vela a vela con datos históricos, en '
                       'TODAS las temporalidades (incluidas las intradía: '
                       '15m, 1h, 4h). Muy selectivo: capta el nacimiento '
                       'simultáneo del impulso.',
        'condiciones': lambda f, s, modo, n: (
            [   # modo giro: pre-filtro amplio (ambas líneas MACD subiendo);
                # el giro exacto en la última vela lo confirma Yahoo después.
                col(f'MACD.macd{f}') > col(f'MACD.macd[1]{f}'),
                col(f'MACD.macd{s}') > col(f'MACD.macd[1]{s}'),
            ] if modo == 'giro' else [
                # modo cruce: el cruce se verifica exacto en TV (basta 1 vela).
                *_macd_evento(f, 'cruce', n),
                *_macd_evento(s, 'cruce', n),
            ]
        ),
        'orden': 'volume',
    },
    'rsi_doble': {
        'nombre': 'RSI Doble: cruce de 50',
        'categoria': 'Mis Scans',
        'multi_tf': True,
        'descripcion': 'El RSI del marco rápido cruza por encima de 50 (zona '
                       'alcista) dentro de las velas elegidas, y el RSI del '
                       'marco lento ya está por encima de 50.',
        'condiciones': lambda f, s, modo, n: [
            col(f'RSI{f}') > 50,
            col(f'RSI[{min(n, _max_hist(f))}]{f}') <= 50,
            col(f'RSI{s}') > 50,
        ],
        'orden': 'volume',
    },
    'rsi_giro': {
        'nombre': 'RSI Giro Alcista: ambos giran en su última vela',
        'categoria': 'Mis Scans',
        'multi_tf': True,
        'descripcion': 'El RSI gira a tendencia positiva aunque esté por '
                       'debajo de 50: el RSI rápido de 7 cruza por encima '
                       'del RSI de 14 en AMBOS marcos, cada uno en su vela '
                       'actual. Mismo criterio que el MACD Estricto: el '
                       'cambio debe ser recién nacido en las dos '
                       'temporalidades.',
        'condiciones': lambda f, s, modo, n: [
            col(f'RSI7{f}') > col(f'RSI{f}'),
            col(f'RSI7[{min(n, _max_hist(f))}]{f}') <=
            col(f'RSI[{min(n, _max_hist(f))}]{f}'),
            col(f'RSI7{s}') > col(f'RSI{s}'),
            col(f'RSI7[1]{s}') <= col(f'RSI[1]{s}'),
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


# --------- Verificación exacta del giro del MACD (vela a vela) ---------
# El screener de TradingView solo expone 1-2 velas de historia, insuficiente
# para confirmar en TODAS las temporalidades que el giro (cambio de pendiente
# de la línea MACD) ocurrió EN la última vela. Para eso se calcula el MACD con
# datos históricos de Yahoo Finance, en cualquier marco: intradía, diario,
# semanal o mensual.

# sufijo TradingView -> (intervalo Yahoo, periodo, ¿resamplear a 4h desde 1h?)
_YF_INTERVALOS = {
    '':     ('1d',  '2y',  False),
    '|1W':  ('1wk', '5y',  False),
    '|1M':  ('1mo', '10y', False),
    '|15':  ('15m', '60d', False),
    '|60':  ('60m', '2y',  False),
    '|240': ('60m', '2y',  True),   # 4h = resample de velas de 1h
}

# sufijo TradingView -> código de intervalo en la URL del gráfico de TradingView
TV_INTERVALO = {'|15': '15', '|60': '60', '|240': '240', '': 'D', '|1W': 'W', '|1M': 'M'}


def _giro_en_ultima_vela(m):
    return len(m) >= 3 and m.iloc[-1] > m.iloc[-2] and m.iloc[-2] <= m.iloc[-3]


def _closes_de(data, sym, un_solo):
    """Extrae la serie de cierres de un símbolo del resultado de yf.download,
    tolerando el formato de un solo ticker (sin nivel de ticker)."""
    if un_solo:
        return data['Close'].dropna().squeeze()
    return data[sym]['Close'].dropna()


def verificar_giro(tickers, tf):
    """Confirma con datos de Yahoo qué tickers giraron su MACD EN la última
    vela del marco `tf`. Devuelve (aprobados, pudo_verificar)."""
    if tf not in _YF_INTERVALOS or not tickers:
        return set(), False
    intervalo, periodo, resample_4h = _YF_INTERVALOS[tf]
    simbolos = {t: t.split(':')[-1].replace('.', '-') for t in tickers}
    un_solo = len(simbolos) == 1
    try:
        import yfinance as yf
        data = yf.download(list(simbolos.values()), period=periodo,
                           interval=intervalo, group_by='ticker',
                           progress=False, threads=True, auto_adjust=True)
    except Exception:
        traceback.print_exc()
        return set(), False
    aprobados, evaluados = set(), 0
    for t, sym in simbolos.items():
        try:
            closes = _closes_de(data, sym, un_solo)
            if resample_4h:
                closes = closes.resample('4h').last().dropna()
            if len(closes) < 40:
                continue
            ema12 = closes.ewm(span=12, adjust=False).mean()
            ema26 = closes.ewm(span=26, adjust=False).mean()
            evaluados += 1
            if _giro_en_ultima_vela(ema12 - ema26):
                aprobados.add(t)
        except Exception:
            pass
    # Si Yahoo falló para la mayoría, mejor no filtrar que filtrar mal
    return aprobados, evaluados >= max(1, len(simbolos) // 2)


def _cookies():
    sid = os.environ.get('TV_SESSIONID', '').strip()
    return {'sessionid': sid} if sid else None


def _get_data(q):
    """Consulta con la sesión Premium si existe; si TradingView la rechaza
    (p. ej. bloquea IPs de datacenter), reintenta sin sesión (datos con
    ~15 min de retraso) para que la app nunca deje de funcionar."""
    ck = _cookies()
    if ck:
        try:
            return q.get_scanner_data(cookies=ck)
        except Exception:
            traceback.print_exc()
    return q.get_scanner_data()


# ---------------- Flujo de capital institucional por sector/industria ----------------
# Aproximación: Money Flow Index (14) ponderado por volumen en dólares
# (Value.Traded) + momentum de 1 mes, agregado por sector e industria y
# convertido a percentil 0-100. Los grupos donde entra más dinero con más
# presión compradora puntúan más alto. Caché de 15 minutos.

_FLUJO_TTL = 15 * 60
_flujo_cache = {'ts': 0.0, 'sector': {}, 'industria': {}}


def _percentiles_grupo(df, grupo):
    agg = df.groupby(grupo).apply(
        lambda g: (
            (g['MoneyFlow'] * g['w']).sum() / g['w'].sum(),
            (g['Perf.1M'] * g['w']).sum() / g['w'].sum(),
        ),
        include_groups=False,
    )
    tabla = pd.DataFrame(agg.tolist(), index=agg.index, columns=['mfi', 'mom'])
    compuesto = tabla['mfi'].rank(pct=True) * 0.6 + tabla['mom'].rank(pct=True) * 0.4
    return (compuesto.rank(pct=True) * 100).round(0).to_dict()


def flujo_grupos():
    """Percentil de flujo institucional por sector y por industria (0-100)."""
    ahora = time.time()
    if ahora - _flujo_cache['ts'] < _FLUJO_TTL and _flujo_cache['sector']:
        return _flujo_cache['sector'], _flujo_cache['industria']

    q = (
        Query()
        .set_markets('america')
        .select('sector', 'industry', 'MoneyFlow', 'Value.Traded', 'Perf.1M')
        .where(
            col('type') == 'stock',
            col('typespecs').has('common'),
            col('exchange').isin(EXCHANGES),
            col('close') > 3,
            col('volume') > 200_000,
        )
        .order_by('Value.Traded', ascending=False)
        .limit(3000)
    )
    _, df = _get_data(q)
    df = df.dropna(subset=['MoneyFlow', 'Value.Traded', 'sector', 'industry'])
    df['Perf.1M'] = df['Perf.1M'].fillna(0)
    df['w'] = df['Value.Traded'].clip(lower=1)

    _flujo_cache['sector'] = _percentiles_grupo(df, 'sector')
    _flujo_cache['industria'] = _percentiles_grupo(df, 'industry')
    _flujo_cache['ts'] = ahora
    return _flujo_cache['sector'], _flujo_cache['industria']


def run_scan(scan_id, min_price=5.0, min_volume=500_000, min_mcap=0,
             tf=TF_DEFAULT, limit=60, min_flujo=0, modo='giro', velas=1):
    """Ejecuta un scan y devuelve (total, filas, etiquetas RSI)."""
    scan = SCANS[scan_id]
    if modo not in ('giro', 'cruce'):
        modo = 'giro'
    velas = max(1, min(int(velas), 2))

    if scan.get('multi_tf'):
        if tf not in TF_PAIRS:
            tf = TF_DEFAULT
        fast, slow, lbl_fast, lbl_slow = TF_PAIRS[tf]
        condiciones = scan['condiciones'](fast, slow, modo, velas)
    else:
        fast, slow, lbl_fast, lbl_slow = TF_PAIRS[TF_DEFAULT]
        condiciones = scan['condiciones']()

    if min_mcap > 0:
        condiciones = [col('market_cap_basic') > min_mcap, *condiciones]

    rsi_fast, rsi_slow = f'RSI{fast}', f'RSI{slow}'
    q = (
        Query()
        .set_markets('america')
        .select(*COLUMNS_BASE, rsi_fast, rsi_slow)
        .where2(And(
            col('type') == 'stock',
            col('typespecs').has('common'),
            col('is_primary') == True,
            col('exchange').isin(EXCHANGES),
            col('close') > min_price,
            col('volume') > min_volume,
            *condiciones,
        ))
        .order_by(scan['orden'], ascending=False)
        .limit(200 if scan.get('verificar_giro') and modo == 'giro' else limit)
    )
    count, df = _get_data(q)
    df = df.rename(columns={rsi_fast: 'rsi_fast', rsi_slow: 'rsi_slow'})

    nota = None
    if scan.get('verificar_giro') and modo == 'giro' and len(df):
        # Verifica el giro exacto (en la última vela) en AMBOS marcos con
        # datos de Yahoo. Un ticker pasa solo si ambos marcos giran ahora.
        tickers = list(df['ticker'])
        aprobados = set(tickers)
        sin_verificar = []
        for tfx, etiqueta_tf in [(fast, lbl_fast), (slow, lbl_slow)]:
            aprob, ok = verificar_giro(tickers, tfx)
            if ok:
                aprobados &= aprob
            else:
                sin_verificar.append(etiqueta_tf)
        df = df[df['ticker'].isin(aprobados)]
        count = len(df)
        if sin_verificar:
            nota = ('No se pudo verificar el giro exacto en el marco ' +
                    ' y '.join(sin_verificar) + ' (datos históricos no '
                    'disponibles ahora): ese marco quedó en modo aproximado.')
        df = df.head(limit)

    # Probabilidad de flujo institucional: 40% percentil del sector +
    # 60% percentil de la industria (más específica). Si la consulta de
    # flujo falla, los resultados salen igualmente sin score.
    try:
        sec_p, ind_p = flujo_grupos()
        df['prob_flujo'] = [
            round(0.4 * sec_p.get(s, 50) + 0.6 * ind_p.get(i, 50))
            for s, i in zip(df['sector'], df['industry'])
        ]
        df = df.sort_values('prob_flujo', ascending=False)
        if min_flujo > 0:
            df = df[df['prob_flujo'] >= min_flujo]
    except Exception:
        df['prob_flujo'] = None

    df = df.astype(object).where(df.notna(), None)
    etiquetas = {'rsi_fast': f'RSI {lbl_fast}', 'rsi_slow': f'RSI {lbl_slow}'}
    if nota:
        etiquetas['nota'] = nota
    return count, df.to_dict(orient='records'), etiquetas

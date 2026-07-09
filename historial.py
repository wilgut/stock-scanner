"""
Registro diario de señales y evaluación de rentabilidad por scanner.

Cada día hábil (cron de Vercel a las ~16:35 NY, o llamada manual a
/api/snapshot) se guardan en Vercel Blob las señales de todos los scans con
su precio de cierre. La evaluación mide la rentabilidad de cada señal desde
el día en que apareció hasta el precio actual, y agrega estadísticas por
scanner para compararlos.
"""
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from tradingview_screener import Query

from scans import SCANS, _get_data, run_scan

NY = ZoneInfo('America/New_York')
PREFIJO = 'senales/'


def _cargar_env_local():
    """En local, toma el token de Blob desde .env.local (Vercel lo inyecta solo)."""
    if os.environ.get('BLOB_READ_WRITE_TOKEN'):
        return
    ruta = os.path.join(os.path.dirname(__file__), '.env.local')
    if os.path.exists(ruta):
        with open(ruta, encoding='utf-8') as f:
            for linea in f:
                linea = linea.strip()
                if linea and not linea.startswith('#') and '=' in linea:
                    k, _, v = linea.partition('=')
                    os.environ.setdefault(k, v.strip('"'))


def _blob():
    _cargar_env_local()
    import vercel_blob
    return vercel_blob


def hoy_ny():
    return datetime.now(NY).date().isoformat()


def guardar_snapshot():
    """Ejecuta todos los scans (marco diario+semanal) y guarda las señales del día."""
    fecha = hoy_ny()
    datos = {'fecha': fecha, 'scans': {}}
    errores = {}
    for scan_id in SCANS:
        try:
            _, filas, _ = run_scan(scan_id)
            datos['scans'][scan_id] = [
                {'t': f['ticker'], 'p': f['close'], 'f': f.get('prob_flujo')}
                for f in filas if f.get('close')
            ]
        except Exception as e:
            errores[scan_id] = f'{type(e).__name__}: {e}'[:150]
    _blob().put(
        f'{PREFIJO}{fecha}.json', json.dumps(datos).encode(),
        {'allowOverwrite': True, 'addRandomSuffix': False,
         'contentType': 'application/json'},
    )
    return fecha, {k: len(v) for k, v in datos['scans'].items()}, errores


def _listar_snapshots():
    blob = _blob()
    blobs, cursor = [], None
    while True:
        opts = {'prefix': PREFIJO, 'limit': '1000'}
        if cursor:
            opts['cursor'] = cursor
        res = blob.list(opts)
        blobs += res.get('blobs', [])
        cursor = res.get('cursor')
        if not res.get('hasMore'):
            break
    return blobs


def _precios_actuales(tickers):
    precios = {}
    ts = sorted(tickers)
    for i in range(0, len(ts), 400):
        lote = ts[i:i + 400]
        q = Query().set_tickers(*lote).select('close').limit(len(lote))
        _, df = _get_data(q)
        for _, fila in df.iterrows():
            precios[fila['ticker']] = fila['close']
    return precios


def evaluar(desde, hasta):
    """Rentabilidad (desde la señal hasta hoy) de las señales emitidas en el rango."""
    docs = []
    for b in _listar_snapshots():
        fecha = b['pathname'][len(PREFIJO):].removesuffix('.json')
        if desde <= fecha <= hasta:
            try:
                docs.append(requests.get(b['url'], timeout=30).json())
            except Exception:
                pass

    # Primera aparición de cada (scan, ticker) dentro del rango
    senales = {}
    for doc in sorted(docs, key=lambda d: d.get('fecha', '')):
        for scan_id, lista in doc.get('scans', {}).items():
            if scan_id not in SCANS:
                continue
            for s in lista:
                clave = (scan_id, s['t'])
                if clave not in senales:
                    senales[clave] = {'fecha': doc['fecha'], 'precio': s['p'],
                                      'flujo': s.get('f')}

    tickers = {t for (_, t) in senales}
    precios = _precios_actuales(tickers) if tickers else {}

    detalle = {}
    for (scan_id, t), s in senales.items():
        actual = precios.get(t)
        if not actual or not s['precio']:
            continue
        rent = (actual / s['precio'] - 1) * 100
        detalle.setdefault(scan_id, []).append({
            'ticker': t, 'symbol': t.split(':')[-1], 'fecha': s['fecha'],
            'precio_senal': round(s['precio'], 2),
            'precio_actual': round(actual, 2),
            'rent': round(rent, 2), 'flujo': s['flujo'],
        })

    resumen = []
    for scan_id, scan in SCANS.items():
        filas = detalle.get(scan_id)
        if not filas:
            # Sin señales en el periodo: se muestra igual para que el
            # comparativo incluya todos los scanners.
            resumen.append({
                'scan': scan_id, 'nombre': scan['nombre'],
                'categoria': scan['categoria'], 'senales': 0,
                'media': None, 'mediana': None, 'positivas': None,
                'mejor': None, 'peor': None,
            })
            continue
        rents = sorted(f['rent'] for f in filas)
        n = len(rents)
        mediana = rents[n // 2] if n % 2 else (rents[n // 2 - 1] + rents[n // 2]) / 2
        mejor = max(filas, key=lambda f: f['rent'])
        peor = min(filas, key=lambda f: f['rent'])
        resumen.append({
            'scan': scan_id,
            'nombre': SCANS[scan_id]['nombre'],
            'categoria': SCANS[scan_id]['categoria'],
            'senales': n,
            'media': round(sum(rents) / n, 2),
            'mediana': round(mediana, 2),
            'positivas': round(100 * sum(1 for r in rents if r > 0) / n),
            'mejor': {'symbol': mejor['symbol'], 'rent': mejor['rent']},
            'peor': {'symbol': peor['symbol'], 'rent': peor['rent']},
        })
        detalle[scan_id] = sorted(filas, key=lambda f: -f['rent'])

    # Con datos primero (por rentabilidad media desc.); sin señales al final
    resumen.sort(key=lambda r: (r['media'] is None, -(r['media'] or 0)))
    dias = sorted({d.get('fecha') for d in docs if d.get('fecha')})
    return {'desde': desde, 'hasta': hasta, 'dias_registrados': dias,
            'resumen': resumen, 'detalle': detalle}

"""Scanner de Acciones — web app de scans de stock picking sobre TradingView."""
import traceback

from flask import Flask, jsonify, render_template, request

from scans import SCANS, TF_DEFAULT, TF_PAIRS, run_scan

app = Flask(__name__)


TF_OPCIONES = {
    '15-60': '15 min + 1 hora',
    '60-240': '1 hora + 4 horas',
    '60-1D': '1 hora + Diario',
    '240-1D': '4 horas + Diario',
    '1D-1W': 'Diario + Semanal',
    '1W-1M': 'Semanal + Mensual',
}


@app.route('/')
def index():
    categorias = {}
    for scan_id, scan in SCANS.items():
        categorias.setdefault(scan['categoria'], []).append((scan_id, scan))
    return render_template('index.html', categorias=categorias,
                           tf_opciones=TF_OPCIONES, tf_default=TF_DEFAULT)


@app.route('/api/scan/<scan_id>')
def api_scan(scan_id):
    if scan_id not in SCANS:
        return jsonify({'error': 'Scan no encontrado'}), 404
    try:
        min_price = float(request.args.get('min_price', 5))
        min_volume = int(request.args.get('min_volume', 500_000))
        min_mcap = float(request.args.get('min_mcap', 0))
        min_flujo = int(request.args.get('min_flujo', 0))
        velas = int(request.args.get('velas', 1))
    except ValueError:
        return jsonify({'error': 'Filtros inválidos'}), 400
    tf = request.args.get('tf', TF_DEFAULT)
    modo = request.args.get('modo', 'giro')
    try:
        total, filas, etiquetas = run_scan(scan_id, min_price, min_volume,
                                           min_mcap, tf, min_flujo=min_flujo,
                                           modo=modo, velas=velas)
    except Exception:
        traceback.print_exc()
        return jsonify({'error': 'Error consultando TradingView. '
                                 'Inténtalo de nuevo en unos segundos.'}), 502
    return jsonify({
        'scan': SCANS[scan_id]['nombre'],
        'total': total,
        'resultados': filas,
        'etiquetas': etiquetas,
    })


@app.route('/rentabilidad')
def rentabilidad():
    return render_template('rentabilidad.html')


@app.route('/api/snapshot', methods=['GET', 'POST'])
def api_snapshot():
    from historial import guardar_snapshot
    try:
        fecha, conteos, errores = guardar_snapshot()
    except Exception:
        traceback.print_exc()
        return jsonify({'error': 'No se pudo guardar el registro de señales.'}), 502
    return jsonify({'fecha': fecha, 'senales_por_scan': conteos,
                    'errores': errores})


@app.route('/api/rentabilidad')
def api_rentabilidad():
    from historial import evaluar, hoy_ny
    hoy = hoy_ny()
    desde = request.args.get('desde', hoy)
    hasta = request.args.get('hasta', hoy)
    try:
        import re
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', desde) or \
           not re.fullmatch(r'\d{4}-\d{2}-\d{2}', hasta):
            return jsonify({'error': 'Fechas inválidas (formato AAAA-MM-DD)'}), 400
        datos = evaluar(desde, hasta)
    except Exception:
        traceback.print_exc()
        return jsonify({'error': 'No se pudo calcular la rentabilidad. '
                                 'Inténtalo de nuevo en unos segundos.'}), 502
    return jsonify(datos)


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8877))
    try:
        from waitress import serve
        print(f'Scanner de Acciones en http://localhost:{port}')
        serve(app, host='0.0.0.0', port=port)
    except ImportError:
        app.run(host='0.0.0.0', port=port, debug=False)

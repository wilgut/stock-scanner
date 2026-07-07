"""Scanner de Acciones — web app de scans de stock picking sobre TradingView."""
import traceback

from flask import Flask, jsonify, render_template, request

from scans import SCANS, run_scan

app = Flask(__name__)


@app.route('/')
def index():
    categorias = {}
    for scan_id, scan in SCANS.items():
        categorias.setdefault(scan['categoria'], []).append((scan_id, scan))
    return render_template('index.html', categorias=categorias)


@app.route('/api/scan/<scan_id>')
def api_scan(scan_id):
    if scan_id not in SCANS:
        return jsonify({'error': 'Scan no encontrado'}), 404
    try:
        min_price = float(request.args.get('min_price', 5))
        min_volume = int(request.args.get('min_volume', 500_000))
    except ValueError:
        return jsonify({'error': 'Filtros inválidos'}), 400
    try:
        total, filas = run_scan(scan_id, min_price, min_volume)
    except Exception:
        traceback.print_exc()
        return jsonify({'error': 'Error consultando TradingView. '
                                 'Inténtalo de nuevo en unos segundos.'}), 502
    return jsonify({
        'scan': SCANS[scan_id]['nombre'],
        'total': total,
        'resultados': filas,
    })


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8877))
    try:
        from waitress import serve
        print(f'Scanner de Acciones en http://localhost:{port}')
        serve(app, host='0.0.0.0', port=port)
    except ImportError:
        app.run(host='0.0.0.0', port=port, debug=False)

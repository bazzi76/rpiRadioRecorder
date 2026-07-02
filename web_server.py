from flask import Flask, render_template, send_from_directory, abort
import os

app = Flask(__name__)

# Cartella dove sono salvate le registrazioni
RECORDINGS_DIR = '/home/gmattei/rpiRadioRecorder/recordings'

@app.route('/')
def index():
    # Elenca i file MP3 ordinati dal più recente al più vecchio
    try:
        files = [f for f in os.listdir(RECORDINGS_DIR) if f.endswith('.mp3')]
        files.sort(reverse=True)
    except FileNotFoundError:
        files = []
    return render_template('index.html', files=files)

@app.route('/download/<filename>')
def download_file(filename):
    # Permette il download o l'ascolto in streaming del file
    if os.path.exists(os.path.join(RECORDINGS_DIR, filename)):
        return send_from_directory(RECORDINGS_DIR, filename, as_attachment=False)
    else:
        abort(404)

if __name__ == '__main__':
    # Avvia il server su tutte le interfacce di rete (0.0.0.0) sulla porta 8080
    app.run(host='0.0.0.0', port=8080, debug=False)

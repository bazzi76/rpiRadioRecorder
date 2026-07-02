#!/bin/bash

# Blocco di sicurezza: interrompe lo script se qualcosa va in errore
set -e

echo "===================================================="
echo "  Installazione di rpiRadioRecorder iniziato...     "
echo "===================================================="

# 1. Verifica se lo script è eseguito con sudo
if [ "$EUID" -ne 0 ]; then
  echo "Errore: Per favore, esegui questo script con sudo."
  echo "Esempio: sudo ./install.sh"
  exit 1
fi

# 2. Ottieni il nome dell'utente reale (non 'root') per configurare i percorsi
REAL_USER=${SUDO_USER:-$USER}
USER_HOME=$(eval echo ~$REAL_USER)
REPO_DIR="$USER_HOME/rpiRadioRecorder"

echo "-> Rilevato utente principale: $REAL_USER"
echo "-> Cartella di lavoro impostata su: $REPO_DIR"

# 3. Aggiorna i pacchetti e installa le dipendenze di sistema
echo "-> Installazione delle dipendenze di sistema (ALSA, Lame, Python)..."
apt update
apt install -y alsa-utils lame python3 python3-pip python3-rpi.gpio python3-flask

# 4. Crea la cartella per le registrazioni (se non esiste già)
echo "-> Creazione della cartella dei salvataggi..."
mkdir -p "$REPO_DIR/recordings"
chown -R $REAL_USER:$REAL_USER "$REPO_DIR/recordings"

# 5. Copia lo script Python in /usr/bin/ e rendilo eseguibile
echo "-> Installazione dello script in /usr/bin/..."
cp "$REPO_DIR/rpi_recorder" /usr/bin/rpi_recorder
chmod +x /usr/bin/rpi_recorder

# 6. Copia il file del servizio in /etc/systemd/system/
echo "-> Configurazione del servizio Systemd..."
cp "$REPO_DIR/radiorecorder.service" /etc/systemd/system/radiorecorder.service

# 7. Ricarica Systemd e abilita il servizio all'avvio
echo "-> Abilitazione e avvio del servizio..."
systemctl daemon-reload
systemctl enable radiorecorder.service
systemctl restart radiorecorder.service

# 8. Abilita web-service
cp "$REPO_DIR/radiorecorder-web.service" /etc/systemd/system/radiorecorder-web.service

systemctl daemon-reload
systemctl enable radiorecorder-web.service 
systemctl restart radiorecorder-web.service

echo "===================================================="
echo "  Installazione completata con successo!            "
echo "  Il servizio è ora attivo e partirà all'avvio.     "
echo "===================================================="

import RPi.GPIO as GPIO
import time
import subprocess
import threading
import sys
import signal # <--- Importante per gestire systemd

# Configurazione PIN
BUTTON_PIN = 23
LED_PIN = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.output(LED_PIN, GPIO.LOW)

print("Attivazione dello speaker di monitor...")
cmd_monitor = "alsaloop -C plug:dsnoop:0 -P plughw:0,0 -c 1 -t 80000"
processo_monitor = subprocess.Popen(cmd_monitor, shell=True)

registrando = False
processo_registrazione = None
stop_led_thread = False

def lampeggia_led():
    global stop_led_thread
    while not stop_led_thread:
        GPIO.output(LED_PIN, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(LED_PIN, GPIO.LOW)
        time.sleep(0.5)

# FUNZIONE DI CHIUSURA PULITA (Valida sia per Ctrl+C che per Systemd)
def chiusura_pulita(signum, frame):
    print("\nChiusura pulita ricevuta (Segnale {})...".format(signum))
    global stop_led_thread, processo_monitor, processo_registrazione
    
    stop_led_thread = True
    
    if processo_monitor:
        processo_monitor.terminate()
    if processo_registrazione:
        subprocess.run("pkill -P " + str(processo_registrazione.pid), shell=True)
        processo_registrazione.terminate()

    GPIO.output(LED_PIN, GPIO.LOW)
    GPIO.cleanup()
    sys.exit(0)

# Colleghiamo i segnali alla nostra funzione di chiusura
signal.signal(signal.SIGINT, chiusura_pulita)  # Gestisce Ctrl+C
signal.signal(signal.SIGTERM, chiusura_pulita) # Gestisce il comando "systemctl stop"

print("Sistema pronto. Premi il pulsante per avviare/fermare.")

try:
    while True:
        stato_pulsante = GPIO.input(BUTTON_PIN)

        if stato_pulsante == False:
            if not registrando:
                print("--- Avvio Registrazione ---")
                nome_file = time.strftime("/home/gmattei/rpiRadioRecorder/recordings/radio_%Y%m%d_%H%M%S.mp3")
                comando_mp3 = f"arecord -D plug:dsnoop:0 -c 1 -r 48000 -f S16_LE -B 500000 | lame -b 64 - {nome_file}"
                processo_registrazione = subprocess.Popen(comando_mp3, shell=True)

                registrando = True
                print(f"Sto registrando in MP3: {nome_file}")

                stop_led_thread = False
                led_thread = threading.Thread(target=lampeggia_led)
                led_thread.daemon = True
                led_thread.start()

            else:
                print("--- Arresto Registrazione ---")
                if processo_registrazione:
                    subprocess.run("pkill -P " + str(processo_registrazione.pid), shell=True)
                    processo_registrazione.terminate()

                registrando = False
                stop_led_thread = True
                GPIO.output(LED_PIN, GPIO.LOW)
                print("Registrazione salvata.")

            time.sleep(1) # Debounce

        time.sleep(0.1)

except Exception as e:
    print(f"Errore imprevisto: {e}")
    chiusura_pulita(None, None)

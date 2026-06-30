import RPi.GPIO as GPIO
import time
import subprocess
import threading

# Configurazione PIN
BUTTON_PIN = 23
LED_PIN = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.output(LED_PIN, GPIO.LOW) # Assicuriamo che parta spento

# --- AVVIO MONITOR CON BUFFER MAGGIORE ---
print("Attivazione dello speaker di monitor...")
cmd_monitor = "alsaloop -C plug:dsnoop:0 -P plughw:0,0 -c 1 -t 80000"
processo_monitor = subprocess.Popen(cmd_monitor, shell=True)

registrando = False
processo_registrazione = None
stop_led_thread = False

# Funzione parallela per far lampeggiare il LED
def lampeggia_led():
    global stop_led_thread
    while not stop_led_thread:
        GPIO.output(LED_PIN, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(LED_PIN, GPIO.LOW)
        time.sleep(0.5)

print("Sistema pronto. Premi il pulsante per avviare/fermare.")

try:
    while True:
        stato_pulsante = GPIO.input(BUTTON_PIN)

        if stato_pulsante == False:
            if not registrando:
                print("--- Avvio Registrazione ---")

                nome_file = time.strftime("/home/gmattei/rpiRadioRecorder/recordings/radio_%Y%m%d_%H%M%S.mp3")

                # Comando ottimizzato
                comando_mp3 = f"arecord -D plug:dsnoop:0 -c 1 -r 48000 -f S16_LE -B 500000 | lame -b 64 - {nome_file}"
                processo_registrazione = subprocess.Popen(comando_mp3, shell=True)

                registrando = True
                print(f"Sto registrando in MP3: {nome_file}")

                # Avvia il thread del LED lampeggiante
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
                
                # Ferma il thread del LED e spegnilo
                stop_led_thread = True
                GPIO.output(LED_PIN, GPIO.LOW)
                
                print("Registrazione salvata.")

            time.sleep(1) # Debounce

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nChiusura...")
    if processo_monitor:
        processo_monitor.terminate()
    if processo_registrazione:
        subprocess.run("pkill -P " + str(processo_registrazione.pid), shell=True)
        processo_registrazione.terminate()
    
    # Pulizia finale hardware
    GPIO.output(LED_PIN, GPIO.LOW)
    GPIO.cleanup()

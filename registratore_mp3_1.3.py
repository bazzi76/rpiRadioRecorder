import RPi.GPIO as GPIO
import time
import subprocess

# Configurazione PIN
BUTTON_PIN = 23

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# --- AVVIO MONITOR CON BUFFER MAGGIORE ---
# Usiamo il parametro '-t 80000' (80ms di latenza). Crea un cuscinetto che elimina gli underrun.
print("Attivazione dello speaker di monitor...")
cmd_monitor = "alsaloop -C plug:dsnoop:0 -P plughw:0,0 -c 1 -t 80000"
processo_monitor = subprocess.Popen(cmd_monitor, shell=True)

registrando = False
processo_registrazione = None

print("Sistema pronto. Premi il pulsante per avviare/fermare.")

try:
    while True:
        stato_pulsante = GPIO.input(BUTTON_PIN)
        
        if stato_pulsante == False:
            if not registrando:
                print("--- Avvio Registrazione ---")
                
                nome_file = time.strftime("./recordings/radio_%Y%m%d_%H%M%S.mp3")
                
                # CORREZIONE FINALE VELOCITÀ: 
                # 1. '-B 500000' imposta un buffer di mezzo secondo su arecord per stabilizzare il flusso.
                # 2. Passiamo a lame i parametri espliciti per il campionamento RAW (-r) a 48kHz (-s 48).
                comando_mp3 = f"arecord -D plug:dsnoop:0 -c 1 -r 48000 -f S16_LE -B 500000 | lame -b 64 - {nome_file}"
                
                processo_registrazione = subprocess.Popen(comando_mp3, shell=True)
                
                registrando = True
                print(f"Sto registrando in MP3: {nome_file}")
                
            else:
                print("--- Arresto Registrazione ---")
                
                if processo_registrazione:
                    subprocess.run("pkill -P " + str(processo_registrazione.pid), shell=True)
                    processo_registrazione.terminate()
                
                registrando = False
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
    GPIO.cleanup()

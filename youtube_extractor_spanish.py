#!/usr/bin/env python3
import os
import re
import sys
import glob
import tempfile
import time
from datetime import datetime
from yt_dlp import YoutubeDL
import whisper
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
import logging
from pydub import AudioSegment  # Usado para convertir el formato de audio

# ---------------------------- Configuración ---------------------------- #

# Tamaño del modelo Whisper: elegir entre 'tiny', 'base', 'small', 'medium', 'large'
WHISPER_MODEL_SIZE = 'base'  # Ajusta según las capacidades de tu sistema

# Configuración de logging
logging.basicConfig(
    filename='single_video_summary_spanish.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ------------------------ Funciones Auxiliares ----------------------------- #

def sanitize_filename(name):
    """
    Sanitiza el título del video (o cualquier cadena) para crear un nombre de archivo válido.
    Elimina o reemplaza caracteres que no son válidos en los nombres de archivos.
    """
    name = name.replace(' ', '_')  # Reemplaza espacios por guiones bajos
    name = re.sub(r'[^\w\-]', '', name)  # Elimina caracteres no alfanuméricos/guiones bajos/guiones
    return name

def download_audio(video_url, download_path, max_retries=3):
    """
    Descarga el stream de audio de un video de YouTube usando yt-dlp y lo convierte a mp3.
    Implementa un mecanismo de reintentos en caso de fallos de red.
    Después de la descarga, busca el archivo mp3 en el directorio de descarga.
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(download_path, '%(id)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
        'retries': max_retries,
    }
    
    attempt = 0
    while attempt < max_retries:
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(video_url, download=True)
                logging.info(f"Descargado info del video para {video_url}: {info_dict.get('title', 'Título Desconocido')}")
            # Después de la descarga, encuentra el archivo mp3 en la carpeta de descarga
            mp3_files = glob.glob(os.path.join(download_path, "*.mp3"))
            if mp3_files:
                audio_file = mp3_files[0]
                logging.info(f"Archivo de audio encontrado: {audio_file}")
                return audio_file
            else:
                logging.error("No se encontró ningún archivo MP3 después de la descarga.")
                return None
        except Exception as e:
            attempt += 1
            logging.error(f"Intento {attempt} - Error al descargar {video_url}: {e}")
            if attempt < max_retries:
                time.sleep(3)  # Espera un poco antes de reintentar
            else:
                return None

def convert_to_mono_wav(mp3_path, output_path):
    """
    Convierte un archivo MP3 a un archivo WAV mono.
    """
    try:
        audio = AudioSegment.from_mp3(mp3_path)
        audio = audio.set_channels(1)  # Convierte a mono
        audio.export(output_path, format="wav")
        logging.info(f"Convertido {mp3_path} a WAV mono en {output_path}.")
        return output_path
    except Exception as e:
        logging.error(f"Error al convertir {mp3_path} a WAV: {e}")
        return None

def transcribe_audio(audio_path, model):
    """
    Transcribe el audio a texto usando Whisper.
    Devuelve tanto la transcripción como el código del idioma detectado.
    """
    try:
        # Especifica el idioma para mejorar la precisión
        result = model.transcribe(audio_path, language="es")
        transcript = result.get('text', "")
        language = result.get('language', "es")
        logging.info(f"Transcrito el archivo de audio {audio_path} con idioma detectado: {language}.")
        return transcript, language
    except Exception as e:
        logging.error(f"Error al transcribir {audio_path}: {e}")
        return "", "es"

def summarize_text_sumy(text, sentence_count=5):
    """
    Genera un resumen del texto proporcionado usando sumy con el algoritmo LexRank.
    """
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("spanish"))
        summarizer = LexRankSummarizer()
        summary = summarizer(parser.document, sentences_count=sentence_count)
        summary_text = ' '.join([str(sentence) for sentence in summary])
        logging.info("Resumen generado utilizando sumy.")
        return summary_text
    except Exception as e:
        logging.error(f"Error al resumir el texto con sumy: {e}")
        return ""

# --------------------------- Script Principal ------------------------------- #

def main():
    if len(sys.argv) != 2:
        print("Uso: python youtube_extractor_spanish.py <URL_de_YouTube>")
        print("Ejemplo: python youtube_extractor_spanish.py https://www.youtube.com/watch?v=1234567890A")
        sys.exit(1)
    
    video_url = sys.argv[1]
    logging.info(f"Iniciado procesamiento de la URL del video: '{video_url}'.")
    
    # Obtiene la información del video (por ejemplo, el título) usando yt-dlp
    try:
        with YoutubeDL({'quiet': True, 'skip_download': True, 'forcejson': True}) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            video_title = info_dict.get('title', 'Título_Desconocido')
    except Exception as e:
        print(f"Error al obtener la información del video para {video_url}: {e}")
        logging.error(f"Error al obtener la información del video para {video_url}: {e}")
        sys.exit(1)
    
    print(f"Procesando Video: {video_title}")
    print(f"URL: {video_url}")

    # Crea un título sanitizado para usar en los nombres de archivos
    sanitized_title = sanitize_filename(video_title)
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    summary_filename = f"{sanitized_title}-{timestamp}.txt"
    summary_filepath = os.path.join(os.getcwd(), summary_filename)
    
    # Carga el modelo Whisper para la transcripción
    print(f"Cargando modelo Whisper ({WHISPER_MODEL_SIZE})...")
    logging.info(f"Cargando modelo Whisper '{WHISPER_MODEL_SIZE}'.")
    whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)
    
    # Crea una carpeta temporal para almacenar el audio descargado
    with tempfile.TemporaryDirectory() as tmpdirname:
        print("Descargando audio...")
        audio_file = download_audio(video_url, tmpdirname)
        if audio_file:
            print(f"Audio descargado en {audio_file}")
            logging.info(f"Audio descargado exitosamente en {audio_file}.")
            
            # Convierte MP3 a WAV mono para mejorar la precisión de la transcripción
            wav_path = os.path.join(tmpdirname, "audio_mono.wav")
            converted_audio = convert_to_mono_wav(audio_file, wav_path)
            if not converted_audio:
                print("Error al convertir el audio a WAV. Saliendo.")
                logging.error("Conversión de audio fallida.")
                sys.exit(1)
            
            # Verifica la duración del archivo de audio
            try:
                audio = AudioSegment.from_wav(converted_audio)
                duration = audio.duration_seconds
                print(f"Duración del audio (s): {duration:.1f}")
                logging.info(f"Duración del audio: {duration:.1f} segundos")
            except Exception as e:
                logging.error(f"No se pudo determinar la duración del audio: {e}")
            
            # Transcribe el audio descargado usando Whisper
            transcript, lang = transcribe_audio(converted_audio, whisper_model)
            if transcript.strip():
                print("Transcripción completada.")
                logging.info("Transcripción completada exitosamente.")
                
                # Genera el resumen del texto transcrito utilizando sumy
                print("Generando resumen...")
                logging.info("Iniciando resumen de la transcripción utilizando sumy.")
                summary = summarize_text_sumy(transcript, sentence_count=5)  # Ajusta el número de frases según tus necesidades
                
                if not summary.strip():
                    print("Error al generar el resumen o el resumen está vacío. Saliendo.")
                    logging.warning("El resumen está vacío después de la generación.")
                    summary = "No se generó ningún resumen."
                
                print("\n--- Resumen ---\n")
                print(summary)
                
                # Prepara el contenido completo para guardar (incluyendo transcripción y resumen)
                file_content = (
                    f"URL del Video: {video_url}\n"
                    f"Título del Video: {video_title}\n"
                    f"Idioma Detectado: {lang}\n"
                    f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    "=== Transcripción ===\n\n"
                    f"{transcript}\n\n"
                    "=== Resumen ===\n\n"
                    f"{summary}"
                )
                
                # Guarda la transcripción y el resumen en un archivo de texto en el directorio actual
                try:
                    with open(summary_filepath, 'w', encoding='utf-8') as f:
                        f.write(file_content)
                    print(f"\nResumen guardado en '{summary_filename}'.")
                    logging.info(f"Resumen guardado en '{summary_filepath}'.")
                except Exception as e:
                    print(f"Error al guardar el resumen en el archivo: {e}")
                    logging.error(f"Error al guardar el archivo '{summary_filepath}': {e}")
            else:
                print("No se generó ninguna transcripción. Saliendo.")
                logging.warning("La transcripción estaba vacía después del procesamiento del audio.")
        else:
            print("Error al descargar el audio. Saliendo.")
            logging.error("La descarga del audio falló para la URL proporcionada.")

if __name__ == "__main__":
    main()

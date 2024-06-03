
import datetime
import io
import openai
import os
import pvcobra
import pvleopard
import pvporcupine
import pyaudio
import random
import socket
import struct
import schedule
import sys
import threading
import time
import traceback
import urllib.request
import logging

from colorama import Fore, Style
from inky.auto import auto
from openai import OpenAI
from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageEnhance
from pvleopard import *
from pvrecorder import PvRecorder
from threading import Thread, Event
from time import sleep
from lib import epd5in65f
from dotenv import load_dotenv
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')

audio_stream = None
cobra = None
pa = None
porcupine = None
recorder = None
wav_file = None
load_dotenv()
logging.basicConfig(level=logging.DEBUG)

epd = epd5in65f.EPD()
logging.info("init and Clear")
epd.Clear()
fontBold = ImageFont.truetype(os.path.join(libdir, 'Roboto-Bold.ttc'), 24)
fontMed = ImageFont.truetype(os.path.join(libdir, 'Roboto-Medium.ttc'), 18)
fontBlack = ImageFont.truetype(os.path.join(libdir, 'Roboto-Black.ttc'), 40)

openai.api_key = "youropenaikey"
pv_access_key= "yourpicokey"

''''''
client = OpenAI(api_key=openai.api_key)

Clear_list = ["Clear",
    "Clear the screen",
    "Clear the epd",
    "Clear the canvas",
    "Delete",
    "Clean",
    "Clean the screen",
    "Clean the epd",
    "Clean the canvas",
    "Wipe",
    "Wipe the screen",
    "Wipe the epd",
    "Wipe the canvas", 
    "Erase",
    "Erase the screen",
    "Erase the epd",
    "Erase the canvas",
    "Blank screen",
    "Blank epd"]

# Uncomment the following if you want to speicfy the style(s) that will be used
# without including it in the specific request.  You can use or modify this list.
"""
style = [
    "Leonardo da Vinci",
    "Pablo Picasso",
    "Mary Cassatt",
    "Salvador Dali",
    "Frida Kahlo",
    "Vincent van Gogh",
    "Berthe Morisot",
    "Fern Coppedge",
    "Roy Lichtenstein",
    "Tamara de Lempicka",
    "Paul Gauguin",
    "Henri Matisse",
    "Yayoi Kusama",
    "Jean-Michel Baquiat",
    "Norman Rockwell",
    "Banksy",
    "Bauhaus",
    "Baroque",
    "Pop Art",
    "Romanticism",
    "Surrealism",
    "Impressionism",
    "Cubism",
    "Steampunk",
    "oil painting",
    "watercolor",
    "Naturalism",
    "Retro",
    "Flat Art",
    "3D Illustration"
    ]
"""

def clean_screen():
    logging.info("1.Clearing...")
    epd.Clear()
    logging.info("Cleaning complete")

def render_time():
    Himage = Image.new('RGB', (epd.width, epd.height), 0xffffff)  # 255: clear the frame
    draw = ImageDraw.Draw(Himage)
    time_now = datetime.datetime.now()
    formatted_time = time_now.strftime("%d-%m-%Y %I:%M:%S %p")
    draw.text((10, 160), formatted_time.split()[0], font = fontBlack, fill = epd.BLACK)
    draw.text((10, 200), formatted_time.split()[1], font = fontBlack, fill = epd.ORANGE)
    draw.text((10, 240), formatted_time.split()[2], font = fontBlack, fill = epd.GREEN)
    draw.text((10, 280), formatted_time.split()[3], font = fontBlack, fill = epd.BLUE)
    draw.text((10, 320), formatted_time.split()[4], font = fontBlack, fill = epd.RED)
    draw.text((10, 360), formatted_time.split()[5], font = fontBlack, fill = epd.YELLOW)
    draw.line((20, 50, 70, 100), fill = 0)
    draw.line((70, 50, 20, 100), fill = 0)
    draw.rectangle((20, 50, 70, 100), outline = 0)
    draw.line((165, 50, 165, 100), fill = 0)
    draw.line((140, 75, 190, 75), fill = 0)
    draw.arc((140, 50, 190, 100), 0, 360, fill = 0)
    draw.rectangle((80, 50, 130, 100), fill = 0)
    draw.chord((200, 50, 250, 100), 0, 360, fill = 0)
    epd.epd(epd.getbuffer(Himage))
    time.sleep(1)
    print("The current date and time is:", formatted_time)  

def current_time():

    time_now = datetime.datetime.now()
    formatted_time = time_now.strftime("%m-%d-%Y %I:%M %p\n")
    print("The current date and time is:", formatted_time)  


def dall_e3(prompt):
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        return (response.data[0].url) 
    except ConnectionResetError:
        print("ConnectionResetError")
        current_time()

def detect_silence():

    cobra = pvcobra.create(access_key=pv_access_key)
    silence_pa = pyaudio.PyAudio()
    cobra_audio_stream = silence_pa.open(
                    rate=cobra.sample_rate,
                    channels=1,
                    format=pyaudio.paInt16,
                    input=True,
                    frames_per_buffer=cobra.frame_length)
    last_voice_time = time.time()
    while True:
        cobra_pcm = cobra_audio_stream.read(cobra.frame_length)
        cobra_pcm = struct.unpack_from("h" * cobra.frame_length, cobra_pcm)      
        if cobra.process(cobra_pcm) > 0.2:
            last_voice_time = time.time()
        else:
            silence_duration = time.time() - last_voice_time
            if silence_duration > 1.3:
                print("End of request detected\n")
                Himage = Image.new('RGB', (epd.width, epd.height), 0xffffff)  # 255: clear the frame
                draw = ImageDraw.Draw(Himage)
                draw.text((10, 160), "Couldn't hear you :(", font = fontBlack, fill = epd.BLACK)
                draw.line((20, 50, 70, 100), fill = 0)
                draw.line((70, 50, 20, 100), fill = 0)
                draw.rectangle((20, 50, 70, 100), outline = 0)
                draw.line((165, 50, 165, 100), fill = 0)
                draw.line((140, 75, 190, 75), fill = 0)
                draw.arc((140, 50, 190, 100), 0, 360, fill = 0)
                draw.rectangle((80, 50, 130, 100), fill = 0)
                draw.chord((200, 50, 250, 100), 0, 360, fill = 0)
                epd.epd(epd.getbuffer(Himage))
                cobra_audio_stream.stop_stream                
                cobra_audio_stream.close()
                cobra.delete()
                last_voice_time=None
                break

def fade_leds(event):

    Himage = Image.new('RGB', (epd.width, epd.height), 0xffffff)  # 255: clear the frame
    draw = ImageDraw.Draw(Himage)
    draw.text((10, 160), "I'm Listening...", font = fontBlack, fill = epd.BLACK)
    draw.line((20, 50, 70, 100), fill = 0)
    draw.line((70, 50, 20, 100), fill = 0)
    draw.rectangle((20, 50, 70, 100), outline = 0)
    draw.line((165, 50, 165, 100), fill = 0)
    draw.line((140, 75, 190, 75), fill = 0)
    draw.arc((140, 50, 190, 100), 0, 360, fill = 0)
    draw.rectangle((80, 50, 130, 100), fill = 0)
    draw.chord((200, 50, 250, 100), 0, 360, fill = 0)
    epd.epd(epd.getbuffer(Himage))
    time.sleep(.3)
        
def listen():

    cobra = pvcobra.create(access_key=pv_access_key)
    listen_pa = pyaudio.PyAudio()
    listen_audio_stream = listen_pa.open(
                rate=cobra.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=cobra.frame_length)
    print("Listening...")
    while True:
        listen_pcm = listen_audio_stream.read(cobra.frame_length)
        listen_pcm = struct.unpack_from("h" * cobra.frame_length, listen_pcm)
        if cobra.process(listen_pcm) > 0.3:
            print("Voice detected")
            listen_audio_stream.stop_stream
            listen_audio_stream.close()
            cobra.delete()
            break

def refresh():

    print("\nThe screen refreshes every day at midnight to help prevent burn-in\n")
    current_time()
    clean_screen()
    sleep(5)
    print("\nRe-rendering")
    epd.set_image(img_resized)
#    epd.set_border(epd.BLACK)
    epd.show()
    print("\nDone")
    
def refresh_schedule(event2):

    schedule.every().day.at("00:00").do(refresh)
    event2.clear()
    while not event2.is_set():                     
        schedule.run_pending()
        sleep(1)
        
def wake_word():

    porcupine = pvporcupine.create(keywords=["computer", "jarvis", "Art-Frame"],
                            access_key=pv_access_key,                                   
                            sensitivities=[0.1, 0.1, 0.1], #from 0 to 1.0 - a higher number reduces the miss rate at the cost on increased false alarms
                                   )
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(2)
    sys.stderr.flush()
    os.dup2(devnull, 2)
    os.close(devnull) 
    wake_pa = pyaudio.PyAudio()
    porcupine_audio_stream = wake_pa.open(
                    rate=porcupine.sample_rate,
                    channels=1,
                    format=pyaudio.paInt16,
                    input=True,
                    frames_per_buffer=porcupine.frame_length)
    Detect = True
    while Detect:
        porcupine_pcm = porcupine_audio_stream.read(porcupine.frame_length)
        porcupine_pcm = struct.unpack_from("h" * porcupine.frame_length, porcupine_pcm)
        porcupine_keyword_index = porcupine.process(porcupine_pcm)
        if porcupine_keyword_index >= 0:
            Himage = Image.new('RGB', (epd.width, epd.height), 0xffffff)  # 255: clear the frame
            draw = ImageDraw.Draw(Himage)
            draw.text((10, 160), "Heard you!", font = fontBlack, fill = epd.BLACK)
            draw.line((20, 50, 70, 100), fill = 0)
            draw.line((70, 50, 20, 100), fill = 0)
            draw.rectangle((20, 50, 70, 100), outline = 0)
            draw.line((165, 50, 165, 100), fill = 0)
            draw.line((140, 75, 190, 75), fill = 0)
            draw.arc((140, 50, 190, 100), 0, 360, fill = 0)
            draw.rectangle((80, 50, 130, 100), fill = 0)
            draw.chord((200, 50, 250, 100), 0, 360, fill = 0)
            epd.epd(epd.getbuffer(Himage))
            print(Fore.GREEN + "\nWake word detected\n")
            current_time()
            print("What would you like me to render?\n")
            porcupine_audio_stream.stop_stream
            porcupine_audio_stream.close()
            porcupine.delete()         
            os.dup2(old_stderr, 2)
            os.close(old_stderr)
            Detect = False

class Recorder(Thread):

    def __init__(self):
        super().__init__()
        self._pcm = list()
        self._is_recording = False
        self._stop = False

    def is_recording(self):
        return self._is_recording

    def run(self):
        self._is_recording = True

        recorder = PvRecorder(device_index=-1, frame_length=512)
        recorder.start()

        while not self._stop:
            self._pcm.extend(recorder.read())
        recorder.stop()

        self._is_recording = False

    def stop(self):
        self._stop = True
        while self._is_recording:
            pass

        return self._pcm

try:

    o = create(
        access_key=pv_access_key,
        enable_automatic_punctuation = False,
        )
    
    event = threading.Event()
    event2 = threading.Event()
    
    while True:

        wake_word()
        event2.set()
        recorder = Recorder()
        recorder.start()
        listen()
        detect_silence()
        transcript, words = o.process(recorder.stop())
        t_fade = threading.Thread(target=fade_leds, args=(event,))
        t_fade.start()
        recorder.stop()
        if transcript not in Clear_list:
            current_time()
            prompt_full = (transcript + (" using vibrant colors"))
# this program asks that only bright colors be used because they look more vibrant on e-paper
# if you prefer not to do this, comment out the prompt_full line above and uncomment the floowing line
#            prompt_full = transcript            
# comment out the prior line and uncomment one of the following lines to try pretermined styles
#            prompt_full = (transcript + (", using only shades of the colors blue, green, red, white, yellow, orange and black."))
#            Style = random.choice(style)
#            prompt_full = (transcript + (" in the style of ") + Style + (", using only shades of the colors blue, green, red, white, yellow, orange and black."))   
            print("You requested: " + prompt_full)
            print("\nCreating...")   
            image_url = dall_e3(prompt_full)
            raw_data = urllib.request.urlopen(image_url).read()
            img = Image.open(io.BytesIO(raw_data))
            img_bordered = ImageOps.expand(img, border=(152,0), fill='black')    
            img_resized = img_bordered.resize((600, 448), Image.ANTIALIAS)

#     curr_col = ImageEnhance.Color(img_resized)
#     new_col = 2.5
#     img_enhanced = curr_col.enhance(new_col)
#     img_bordered = ImageOps.expand(img_enhanced, border=(0,76), fill='black')

            print("\nRendering...")
            epd.set_image(img_resized)
#            epd.set_border(epd.BLACK)
            epd.show()
# uncomment the following line if you also want the image to show on a epd connected to the RPi
#            img.show()
            event.set()
            sleep(2)            
            t_refresh = threading.Thread(target=refresh_schedule, args=(event2,))
            t_refresh.start()                      
            print("\nDone")
   
        else:
            print ("Clearing the epd...")
            clean_screen()            
            event.set()
            event2.set()
            print("\nDone")
   
except ConnectionResetError:
    print ("Reset Error")
    current_time()
    
except KeyboardInterrupt:    
    exit()
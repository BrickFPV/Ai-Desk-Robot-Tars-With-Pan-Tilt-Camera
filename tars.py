import asyncio
import io
import os
import sys
import wave
import subprocess
import ctypes
import random
import time
import json
import base64
import cv2
import numpy as np
import pyaudio
from datetime import datetime, timezone, timedelta

# Improved import order for ddgs library
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

from groq import AsyncGroq
from contextlib import contextmanager

# --- SERVO CONTROLLER (PCA9685 via ServoKit) ---
SERVO_ENABLED = False
try:
    from adafruit_servokit import ServoKit
    kit = ServoKit(channels=16)
    SERVO_ENABLED = True
    print("[PCA9685 Servo Controller Initialized Successfully]")
except Exception as e:
    print(f"[PCA9685 Servo Warning]: Could not initialize ServoKit ({e}). Servos disabled.")

# --- C-LEVEL ALSA ERROR SUPPRESSION ---
ERROR_HANDLER_FUNC = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p)
def py_error_handler(filename, line, function, err, fmt):
    pass
c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

try:
    asound = ctypes.cdll.LoadLibrary('libasound.so.2')
    asound.snd_lib_error_set_handler(c_error_handler)
except Exception:
    pass

os.environ["PA_ALSA_PLUGINS_DISABLE"] = "1"
os.environ["PYTHONUNBUFFERED"] = "1"

# Keywords that trigger playback interruption during TTS speech
INTERRUPT_KEYWORDS = ["hey tars", "tars", "stop", "wait"]

# Keywords that trigger returning to wake-word standby mode
EXIT_KEYWORDS = [
    "stop the conversation", "stop conversation", "stop", 
    "cancel", "never mind", "nevermind", "exit", "bye", "goodbye", "go to standby"
]

def is_exit_command(text: str) -> bool:
    """Checks if user prompt requests ending the conversation session."""
    text_lower = text.lower().strip()
    return any(kw in text_lower for kw in EXIT_KEYWORDS)


@contextmanager
def suppress_stderr():
    """Redirects low-level ALSA/PyAudio stderr warnings to /dev/null."""
    try:
        null_fd = os.open(os.devnull, os.O_WRONLY)
        old_stderr = os.dup(2)
        os.dup2(null_fd, 2)
        os.close(null_fd)
        yield
    finally:
        os.dup2(old_stderr, 2)
        os.close(old_stderr)

# ==========================================
# --- CONFIGURATION & KEYS -----------------
# PLACE YOUR GROQ API KEY
GROQ_API_KEY = "PLACE YOUR GROQ API KEY HERE"

# Groq Orpheus TTS Voice Options: "troy", "daniel", "austin", "hannah", "diana", "autumn"
GROQ_TTS_MODEL = "canopylabs/orpheus-v1-english"
GROQ_TTS_VOICE = "troy"

TURKEY_TZ = timezone(timedelta(hours=3))
ACK_DIR = os.path.join(os.path.dirname(__file__), "acks")
TEMP_WAV_PATH = "/tmp/tars_tts_speech.wav"

# VAD Tuning Parameters
SILENCE_THRESHOLD = 400     # Silence threshold for user speech
INTERRUPT_THRESHOLD = 1200  # Voice threshold to trigger interruption during TTS output
SILENCE_DURATION = 0.6      # Seconds of silence before stopping recording early
MAX_RECORD_TIME = 6.0       # Maximum clip duration hard limit

# Servo Motion Calibration - MAXIMUM RANGE LIMITS
PAN_CHANNEL = 0
TILT_CHANNEL = 1

PAN_CENTER = 90
TILT_CENTER = 90

PAN_RIGHT = 20    # Maximum right limit
PAN_LEFT = 160    # Maximum left limit
TILT_UP = 150     # Maximum up limit
TILT_DOWN = 30    # Maximum down limit

# Global tracking of current head position
current_pan = PAN_CENTER
current_tilt = TILT_CENTER

# Vision trigger words
VISION_KEYWORDS = [
    "holding", "look", "see", "showing", "camera", "picture", 
    "photo", "what is this", "what am i", "view", "watch", "read",
    "describe", "what's", "what is"
]
# ==========================================

if GROQ_API_KEY == "PASTE_YOUR_GROQ_API_KEY_HERE":
    print("\n[ERROR] You need to paste your Groq API key into tars.py!")
    sys.exit(1)

client = AsyncGroq(api_key=GROQ_API_KEY)

# Audio Parameters (Logitech C270 USB Webcam Microphone Setup)
HW_CHANNELS = 1
HW_RATE = 16000
CHUNK = 1024

def find_webcam_mic_index(p):
    """Locates the Logitech C270 / USB Webcam input device index in PyAudio."""
    for i in range(p.get_device_count()):
        try:
            dev = p.get_device_info_by_index(i)
            name = dev.get('name', '').lower()
            if dev.get('maxInputChannels', 0) > 0:
                if 'c270' in name or 'webcam' in name or 'usb' in name:
                    return i
        except Exception:
            pass
    return None

# --- WEB SEARCH TOOL DEFINITION ---
WEB_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the live internet for up-to-date facts, sports results, news, or current events.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query keywords including current context."
                }
            },
            "required": ["query"]
        }
    }
}

# ==========================================
# --- SERVO MOTION CONTROL FUNCTIONS ------
# ==========================================
async def move_head_smooth(target_pan, target_tilt, speed=0.015):
    """Moves pan/tilt servos smoothly to target angles to prevent mechanical jerking."""
    global current_pan, current_tilt
    if not SERVO_ENABLED:
        return

    # Safety clamping to prevent servo over-rotation
    target_pan = max(20, min(160, target_pan))
    target_tilt = max(30, min(150, target_tilt))

    pan_steps = np.linspace(current_pan, target_pan, num=15)
    tilt_steps = np.linspace(current_tilt, target_tilt, num=15)

    for p_angle, t_angle in zip(pan_steps, tilt_steps):
        try:
            kit.servo[PAN_CHANNEL].angle = p_angle
            kit.servo[TILT_CHANNEL].angle = t_angle
            current_pan = p_angle
            current_tilt = t_angle
        except Exception:
            pass
        await asyncio.sleep(speed)

async def head_nod():
    """Nods head down and back to center."""
    await move_head_smooth(current_pan, max(30, current_tilt - 20), speed=0.01)
    await move_head_smooth(current_pan, min(150, current_tilt + 20), speed=0.01)

async def head_tilt_curious():
    """Tilts head slightly off-center when listening."""
    offset_pan = PAN_CENTER + random.choice([-15, 15])
    await move_head_smooth(offset_pan, TILT_CENTER + 15, speed=0.02)

async def head_center():
    """Resets head to forward center position."""
    await move_head_smooth(PAN_CENTER, TILT_CENTER, speed=0.015)

async def head_subtle_speak_movement():
    """Generates minor head movement while speaking to emulate lifelike presence."""
    rand_pan = max(30, min(150, current_pan + random.randint(-10, 10)))
    rand_tilt = max(40, min(140, current_tilt + random.randint(-6, 6)))
    await move_head_smooth(rand_pan, rand_tilt, speed=0.02)

def parse_directional_command(text: str):
    """
    Parses user input for directional movements.
    Re-centers unmentioned axes so single-direction commands move straight on that axis.
    Returns: (has_direction, target_pan, target_tilt, is_pure_movement)
    """
    text_lower = text.lower()
    
    # Default unmentioned axes to CENTER
    target_pan = PAN_CENTER
    target_tilt = TILT_CENTER
    
    has_horizontal = False
    has_vertical = False

    # Check horizontal directions (handles 'şeft' typo for 'left')
    if "right" in text_lower:
        target_pan = PAN_RIGHT
        has_horizontal = True
    elif "left" in text_lower or "şeft" in text_lower:
        target_pan = PAN_LEFT
        has_horizontal = True

    # Check vertical directions
    if "up" in text_lower or "higher" in text_lower:
        target_tilt = TILT_UP
        has_vertical = True
    elif "down" in text_lower or "lower" in text_lower:
        target_tilt = TILT_DOWN
        has_vertical = True

    has_direction = has_horizontal or has_vertical

    # Check center/reset request
    if any(w in text_lower for w in ["straight", "forward", "front", "center", "reset"]):
        target_pan = PAN_CENTER
        target_tilt = TILT_CENTER
        has_direction = True

    # Check if a question is being asked alongside the direction
    has_question = any(q in text_lower for q in [
        "what", "who", "where", "describe", "tell", "see", "read", "showing", "photo", "picture", "is on"
    ])

    # Pure movement = user commanded movement without asking a question
    is_pure_movement = has_direction and not has_question

    return has_direction, target_pan, target_tilt, is_pure_movement

# Initialize Head Position on Startup
if SERVO_ENABLED:
    try:
        kit.servo[PAN_CHANNEL].angle = PAN_CENTER
        kit.servo[TILT_CHANNEL].angle = TILT_CENTER
    except Exception:
        pass

# ==========================================

def capture_image_base64():
    """Captures a frame from USB webcam (Logitech C270) and returns base64 JPEG string."""
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("\n[Camera Error]: Could not open webcam on /dev/video0", flush=True)
            return None

        for _ in range(5):
            ret, frame = cap.read()

        cap.release()

        if not ret or frame is None:
            print("\n[Camera Error]: Failed to capture image frame", flush=True)
            return None

        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        return base64.b64encode(buffer).decode('utf-8')
    except Exception as e:
        print(f"\n[Camera Error]: {e}", flush=True)
        return None

def is_vision_query(text: str) -> bool:
    """Checks if user prompt requests visual observation via webcam."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in VISION_KEYWORDS)

def play_local_ack():
    """Plays a random pre-recorded acknowledgment WAV file locally."""
    if not os.path.exists(ACK_DIR):
        print("TARS: YES?", flush=True)
        return

    files = [f for f in os.listdir(ACK_DIR) if f.lower().endswith(".wav")]
    if not files:
        print("TARS: YES?", flush=True)
        return

    chosen_file = random.choice(files)
    filepath = os.path.join(ACK_DIR, chosen_file)

    display_name = os.path.splitext(chosen_file)[0].upper().replace("_", " ")
    print(f"TARS: {display_name}?", flush=True)

    try:
        subprocess.run(['aplay', '-q', filepath], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"[Audio Error]: {e}")

def execute_web_search(query: str) -> str:
    """Performs a web search using DuckDuckGo."""
    try:
        results = DDGS().text(query, max_results=3)
        if not results:
            return "No internet search results found."
        formatted = "\n".join([f"- {r.get('title')}: {r.get('body')}" for r in results])
        return formatted
    except Exception as e:
        return f"Search error: {e}"

def process_pcm_to_mono_wav(raw_pcm):
    """Converts recorded 16kHz PCM directly into a WAV container for Whisper STT."""
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(raw_pcm)
    
    wav_io.seek(0)
    wav_io.name = "input.wav"
    return wav_io

def record_audio_smart(prompt_msg="", is_wake_word=False):
    """VAD recorder using Logitech C270 USB microphone."""
    if prompt_msg:
        print(prompt_msg, flush=True)

    with suppress_stderr():
        p = pyaudio.PyAudio()
        dev_idx = find_webcam_mic_index(p)
        
        stream_kwargs = {
            "format": pyaudio.paInt16,
            "channels": HW_CHANNELS,
            "rate": HW_RATE,
            "input": True,
            "frames_per_buffer": CHUNK
        }
        if dev_idx is not None:
            stream_kwargs["input_device_index"] = dev_idx

        stream = p.open(**stream_kwargs)

    frames = []
    has_spoken = False
    silence_start = None
    start_time = time.time()
    max_duration = 1.8 if is_wake_word else MAX_RECORD_TIME

    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)

        audio_chunk = np.frombuffer(data, dtype=np.int16)
        rms = np.sqrt(np.mean(audio_chunk.astype(np.float32)**2)) if len(audio_chunk) > 0 else 0

        if rms > SILENCE_THRESHOLD:
            has_spoken = True
            silence_start = None
        elif has_spoken:
            if silence_start is None:
                silence_start = time.time()
            elif time.time() - silence_start >= SILENCE_DURATION:
                break

        if time.time() - start_time >= max_duration:
            break

    with suppress_stderr():
        stream.stop_stream()
        stream.close()
        p.terminate()

    return b''.join(frames)

async def transcribe_audio(wav_file):
    """Speech-to-Text using whisper-large-v3-turbo via Groq API."""
    try:
        transcription = await client.audio.transcriptions.create(
            file=wav_file,
            model="whisper-large-v3-turbo",
            response_format="text",
            temperature=0.0
        )
        return transcription.strip()
    except Exception as e:
        print(f"\n[STT Error]: {e}")
        return ""

async def stream_tars_response(chat_history, image_b64=None):
    """Handles streaming responses from Groq with vision routing and thinking suppressed."""
    
    # -------------------------------------------------------------
    # VISION EXECUTION PATH (Qwen 3.6 27B)
    # -------------------------------------------------------------
    if image_b64:
        model_name = "qwen/qwen3.6-27b"
        
        last_msg = chat_history.pop()
        user_prompt_text = last_msg["content"] if isinstance(last_msg["content"], str) else "What do you see?"

        multimodal_msg = {
            "role": "user",
            "content": [
                {"type": "text", "text": user_prompt_text},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                }
            ]
        }
        chat_history.append(multimodal_msg)

        try:
            completion = await client.chat.completions.create(
                model=model_name,
                messages=chat_history,
                temperature=0.7,
                max_completion_tokens=256,
                reasoning_format="hidden",
                reasoning_effort="none",
                stream=True
            )
            
            in_think_block = False
            async for chunk in completion:
                delta = chunk.choices[0].delta.content
                if not delta:
                    continue

                if "<think>" in delta:
                    in_think_block = True
                    delta = delta.split("<think>")[0]
                if "</think>" in delta:
                    in_think_block = False
                    delta = delta.split("</think>")[-1]

                if not in_think_block and delta:
                    yield delta
            return
        except Exception as e:
            print(f"\n[Vision LLM Error]: {e}")
            yield "My optical sensors had a glitch."
            return

    # -------------------------------------------------------------
    # STANDARD TEXT & SEARCH EXECUTION PATH (GPT-OSS 120B)
    # -------------------------------------------------------------
    model_name = "openai/gpt-oss-120b"
    try:
        first_pass = await client.chat.completions.create(
            model=model_name,
            messages=chat_history,
            tools=[WEB_SEARCH_TOOL],
            tool_choice="auto",
            temperature=0.7,
            max_completion_tokens=256,
            reasoning_format="hidden",
            reasoning_effort="low"
        )

        msg = first_pass.choices[0].message

        if msg.tool_calls:
            assistant_msg = {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in msg.tool_calls
                ]
            }
            chat_history.append(assistant_msg)

            for tool_call in msg.tool_calls:
                if tool_call.function.name == "web_search":
                    args = json.loads(tool_call.function.arguments)
                    query = args.get("query", "")
                    print(f"\n[TARS Searching Internet: '{query}']...", flush=True)

                    search_result = await asyncio.to_thread(execute_web_search, query)
                    
                    chat_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": search_result
                    })

            # Pass WITH tools parameter to maintain tool call context schema requirement
            completion = await client.chat.completions.create(
                model=model_name,
                messages=chat_history,
                tools=[WEB_SEARCH_TOOL],
                temperature=0.7,
                max_completion_tokens=256,
                reasoning_format="hidden",
                reasoning_effort="low",
                stream=True
            )
            async for chunk in completion:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        else:
            yield msg.content or ""

    except Exception as e:
        print(f"\n[LLM Error]: {e}")
        yield ""

async def generate_and_play_groq_tts(text, interrupt_event):
    """Sends text to Groq Orpheus TTS API, streams audio via aplay, and checks mic for wake/stop keywords."""
    if not text.strip() or interrupt_event.is_set():
        return True
    
    try:
        response = await client.audio.speech.create(
            model=GROQ_TTS_MODEL,
            voice=GROQ_TTS_VOICE,
            input=text,
            response_format="wav"
        )
        
        audio_bytes = await response.read()

        with open(TEMP_WAV_PATH, "wb") as f:
            f.write(audio_bytes)

        player_proc = subprocess.Popen(
            ['aplay', '-q', TEMP_WAV_PATH],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Trigger subtle head movement while TARS is speaking
        asyncio.create_task(head_subtle_speak_movement())

        with suppress_stderr():
            p = pyaudio.PyAudio()
            dev_idx = find_webcam_mic_index(p)
            stream_kwargs = {
                "format": pyaudio.paInt16,
                "channels": HW_CHANNELS,
                "rate": HW_RATE,
                "input": True,
                "frames_per_buffer": CHUNK
            }
            if dev_idx is not None:
                stream_kwargs["input_device_index"] = dev_idx

            mic_stream = p.open(**stream_kwargs)

        interrupted = False
        speaking_frames = []
        is_collecting_speech = False
        silence_start = None

        while player_proc.poll() is None:
            if interrupt_event.is_set():
                player_proc.terminate()
                player_proc.kill()
                interrupted = True
                break

            try:
                data = mic_stream.read(CHUNK, exception_on_overflow=False)
                audio_chunk = np.frombuffer(data, dtype=np.int16)
                rms = np.sqrt(np.mean(audio_chunk.astype(np.float32)**2)) if len(audio_chunk) > 0 else 0
                
                # Detect speech activity
                if rms > SILENCE_THRESHOLD:
                    if not is_collecting_speech:
                        is_collecting_speech = True
                        speaking_frames = []
                    speaking_frames.append(data)
                    silence_start = None
                elif is_collecting_speech:
                    speaking_frames.append(data)
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start >= 0.4:
                        # Pause detected: transcribe the captured snippet to test for interrupt words
                        is_collecting_speech = False
                        frames_to_check = list(speaking_frames)
                        speaking_frames = []
                        
                        wav_file = process_pcm_to_mono_wav(b''.join(frames_to_check))
                        transcript = await transcribe_audio(wav_file)
                        
                        if transcript:
                            text_lower = transcript.lower()
                            if any(kw in text_lower for kw in INTERRUPT_KEYWORDS):
                                print(f"\n[Interrupt Keyword Detected: '{transcript}']", flush=True)
                                player_proc.terminate()
                                player_proc.kill()
                                interrupt_event.set()
                                interrupted = True
                                break
            except Exception:
                pass

            await asyncio.sleep(0.001)

        with suppress_stderr():
            mic_stream.stop_stream()
            mic_stream.close()
            p.terminate()

        return interrupted
    except Exception as e:
        print(f"\n[Groq TTS Error]: {e}")
        return False

async def speak_text_groq_tts(text_stream, interrupt_event):
    """Buffers text by sentence and speaks it. Stops immediately if interrupted by user."""
    print("TARS: ", end="", flush=True)
    buffer = ""
    full_response = ""
    sentence_enders = {'.', '!', '?', '\n'}
    interrupted = False
    
    async for chunk in text_stream:
        if interrupt_event.is_set():
            interrupted = True
            break
        if not chunk:
            continue
        print(chunk, end="", flush=True)
        buffer += chunk
        full_response += chunk

        if any(p in chunk for p in sentence_enders) and len(buffer.strip()) > 15:
            was_interrupted = await generate_and_play_groq_tts(buffer.strip(), interrupt_event)
            buffer = ""
            if was_interrupted:
                interrupted = True
                break

    if not interrupted and buffer.strip():
        was_interrupted = await generate_and_play_groq_tts(buffer.strip(), interrupt_event)
        if was_interrupted:
            interrupted = True

    if interrupted:
        print(" [Interrupted!]", flush=True)

    print()
    return full_response, interrupted

def get_updated_system_instruction():
    """Generates TARS prompt initialized with UTC+3 local time."""
    now = datetime.now(TURKEY_TZ)
    live_time = now.strftime("%I:%M %p")
    live_date = now.strftime("%A, %B %d, %Y")
    return (
        f"You are TARS from Interstellar. Humor: 75%, Honesty: 90%. "
        f"The current date is {live_date} and local time in Turkey is {live_time} (UTC+3). "
        "You have optical camera vision and live internet search. Answer concisely, dryly, and sarcastically in under 25 words."
    )

async def handle_user_command(command_text, chat_history):
    """Processes directional head movement, pure movement commands, and vision queries."""
    has_dir, target_pan, target_tilt, is_pure_movement = parse_directional_command(command_text)

    # Move head first if direction specified
    if has_dir:
        print(f"[Moving head to Pan: {target_pan}°, Tilt: {target_tilt}°]", flush=True)
        await move_head_smooth(target_pan, target_tilt)
        await asyncio.sleep(0.3)  # Allow servo to settle & camera focus to adjust

    # PURE MOVEMENT PATH (No photo, no vision call)
    if is_pure_movement:
        ack_msg = random.choice([
            "Looking that way.", "Head position adjusted.", "Sensors pointed.", 
            "Oriented.", "Target acquired."
        ])
        print(f"TARS: {ack_msg}", flush=True)
        interrupt_event = asyncio.Event()
        await generate_and_play_groq_tts(ack_msg, interrupt_event)
        
        chat_history.append({"role": "user", "content": command_text})
        chat_history.append({"role": "assistant", "content": ack_msg})
        return False

    # VISION QUERY PATH (Capture photo at current head position)
    image_b64 = None
    if is_vision_query(command_text) or (has_dir and not is_pure_movement):
        print("[Capturing webcam image at current position...]", flush=True)
        image_b64 = await asyncio.to_thread(capture_image_base64)

    chat_history.append({"role": "user", "content": command_text})
    
    interrupt_event = asyncio.Event()
    text_stream = stream_tars_response(chat_history, image_b64=image_b64)
    assistant_reply, was_interrupted = await speak_text_groq_tts(text_stream, interrupt_event)

    if isinstance(chat_history[-1].get("content"), list):
        chat_history[-1]["content"] = command_text

    chat_history.append({"role": "assistant", "content": assistant_reply})
    return was_interrupted

async def main():
    print("\n--- TARS VOICE + VISION ASSISTANT ONLINE (LOGITECH C270 MIC ENABLED) ---", flush=True)

    chat_history = []
    await head_center()

    while True:
        raw_pcm = record_audio_smart(prompt_msg="\n[Waiting for wake word 'Hey Tars'...]", is_wake_word=True)
        wav_file = process_pcm_to_mono_wav(raw_pcm)

        user_text = await transcribe_audio(wav_file)
        if not user_text or len(user_text) < 2:
            continue

        text_lower = user_text.lower()
        if not any(word in text_lower for word in ["tars", "tar"]):
            continue

        print(f"\n[Wake word detected!]", flush=True)
        asyncio.create_task(head_nod())
        play_local_ack()

        asyncio.create_task(head_tilt_curious())
        raw_pcm_cmd = record_audio_smart(prompt_msg="[Listening for command...]")
        wav_file_cmd = process_pcm_to_mono_wav(raw_pcm_cmd)

        command_text = await transcribe_audio(wav_file_cmd)
        if not command_text or len(command_text) < 2:
            print("[No command heard, returning to standby...]")
            await head_center()
            continue

        print(f"You: {command_text}", flush=True)

        # Check for immediate exit/stop request
        if is_exit_command(command_text):
            print("TARS: Standing by.", flush=True)
            interrupt_event = asyncio.Event()
            await generate_and_play_groq_tts("Standing by.", interrupt_event)
            await head_center()
            chat_history.clear()
            continue

        system_instruction = get_updated_system_instruction()
        if not chat_history:
            chat_history.append({"role": "system", "content": system_instruction})
        else:
            chat_history[0] = {"role": "system", "content": system_instruction}

        was_interrupted = await handle_user_command(command_text, chat_history)

        # Dynamic follow-up loop
        while True:
            prompt_label = "[Listening for command...]" if was_interrupted else "[Listening for follow-up...]"
            
            raw_followup = record_audio_smart(prompt_msg=prompt_label)
            wav_followup = process_pcm_to_mono_wav(raw_followup)

            followup_text = await transcribe_audio(wav_followup)
            if not followup_text or len(followup_text) < 2:
                print("[Conversation ended, returning to standby...]")
                await head_center()
                chat_history.clear()
                break

            print(f"You: {followup_text}", flush=True)

            # Check for exit request during follow-ups
            if is_exit_command(followup_text):
                print("TARS: Standing by.", flush=True)
                interrupt_event = asyncio.Event()
                await generate_and_play_groq_tts("Standing by.", interrupt_event)
                await head_center()
                chat_history.clear()
                break

            chat_history[0] = {"role": "system", "content": get_updated_system_instruction()}

            was_interrupted = await handle_user_command(followup_text, chat_history)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTARS shutting down.", flush=True)
        sys.exit(0)

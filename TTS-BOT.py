import asyncio
import edge_tts
import os
import time
import psutil
from pydub import AudioSegment
from telethon import TelegramClient, events
from telethon.tl.types import DocumentAttributeAudio
import fitz  # PyMuPDF for PDFs
from docx import Document  # For Word (DOCX)
from asyncio import Lock
import subprocess

# Telegram bot credentials
API_ID = "YOUR_API_ID"
API_HASH = "YOUR_API_HASH"
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# State management: store users currently uploading or processing files
user_locks = set()
file_lock = Lock()

client = TelegramClient('bot_session', API_ID,
                        API_HASH).start(bot_token=BOT_TOKEN)


def release_file(filepath):
    """Release a locked file by terminating the process."""
    for proc in psutil.process_iter():
        try:
            for open_file in proc.open_files():
                if open_file.path == filepath:
                    proc.terminate()
                    proc.wait()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass


def validate_and_fix_mp3(file_path):
    """Check if the MP3 is valid, and fix it if needed."""
    try:
        result = subprocess.run(
            ['ffmpeg', '-v', 'error', '-i', file_path, '-f', 'null', '-'],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Invalid MP3 detected: {file_path}. Attempting to fix...")
            fixed_path = file_path.replace(".mp3", "_fixed.mp3")
            subprocess.run(['ffmpeg', '-i', file_path,
                           '-c', 'copy', fixed_path])
            return fixed_path if os.path.exists(fixed_path) else None
        return file_path
    except Exception as e:
        print(f"Error during MP3 validation: {e}")
        return None


def extract_text_from_file(file_path):
    """Extract text from TXT, PDF, or DOCX files."""
    ext = os.path.splitext(file_path)[-1].lower()

    if ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    elif ext == '.pdf':
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
        return text
    elif ext == '.docx':
        doc = Document(file_path)
        return '\n'.join([para.text for para in doc.paragraphs])
    else:
        raise ValueError("Unsupported file format")


async def generate_audio_for_paragraph(text, voice, output_filename):
    """Generate TTS audio for a paragraph."""
    communicate = edge_tts.Communicate(text, voice)
    try:
        await communicate.save(output_filename)
        print(f"Generated {output_filename} using {voice}")
        return output_filename
    except Exception as e:
        print(f"Error with {voice}: {e}")
        return None


async def process_text_to_speech(text, user_id):
    """Convert text to speech and combine audio files."""
    voices = ["fa-IR-FaridNeural", "fa-IR-DilaraNeural"]
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

    temp_dir = f"temp_{user_id}_{int(time.time())}"
    os.makedirs(temp_dir, exist_ok=True)

    temp_files = []
    failed_files = []

    for i, paragraph in enumerate(paragraphs):
        voice = voices[i % len(voices)]
        temp_file = f"{temp_dir}/part_{i + 1}_{voice.split('-')[2]}.mp3"

        result = await generate_audio_for_paragraph(paragraph, voice, temp_file)
        if result and os.path.exists(result):
            temp_files.append(result)
        else:
            print(f"Error generating {temp_file}, adding to retry list.")
            failed_files.append((paragraph, temp_file, voice))

        await asyncio.sleep(0.1)

    for paragraph, temp_file, voice in failed_files:
        print(f"Retrying generation for {temp_file}...")
        result = await generate_audio_for_paragraph(paragraph, voice, temp_file)
        if result and os.path.exists(result):
            temp_files.append(result)
        else:
            print(f"Failed again: {temp_file}. Skipping.")

    combined = AudioSegment.empty()
    pause = AudioSegment.silent(duration=500)

    for i, temp_file in enumerate(temp_files):
        valid_file = validate_and_fix_mp3(temp_file)
        if valid_file:
            audio_segment = AudioSegment.from_mp3(valid_file)
            combined += audio_segment
            if i < len(temp_files) - 1:
                combined += pause
        else:
            print(f"Skipping invalid file: {temp_file}")

    output_file = f"{temp_dir}/final_output_{user_id}.mp3"
    combined.export(output_file, format="mp3")

    for temp_file in temp_files:
        try:
            release_file(temp_file)
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception as e:
            print(f"Error removing {temp_file}: {e}")

    return output_file


@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Handle the /start command."""
    await event.respond("سلام! فایل خود را ارسال کنید تا به گفتار تبدیل کنم.")


@client.on(events.NewMessage(incoming=True, func=lambda e: e.file))
async def handle_file_message(event):
    """Process incoming file messages."""
    user_id = event.sender_id

    if user_id in user_locks:
        await event.respond("لطفاً منتظر بمانید تا فایل قبلی شما پردازش شود.")
        return

    user_locks.add(user_id)  # Lock this user

    async with file_lock:
        try:
            processing_msg = await event.respond("در حال پردازش فایل و تولید صوت...")

            file_path = await event.download_media()
            text = extract_text_from_file(file_path)

            output_file = await process_text_to_speech(text, user_id)

            audio = AudioSegment.from_mp3(output_file)
            duration = len(audio) / 1000

            await client.send_file(
                event.chat_id,
                output_file,
                voice_note=True,
                attributes=[DocumentAttributeAudio(
                    duration=int(duration), voice=True)],
            )

            release_file(output_file)
            if os.path.exists(output_file):
                os.remove(output_file)
            os.rmdir(os.path.dirname(output_file))

            await processing_msg.delete()

        except Exception as e:
            await event.respond(f"متاسفانه خطایی رخ داد: {str(e)}")

        finally:
            user_locks.remove(user_id)  # Unlock the user


async def main():
    """Start the bot."""
    try:
        print("Bot started...")
        me = await client.get_me()
        print(f"Bot info: @{me.username}")
        await client.run_until_disconnected()
    except Exception as e:
        print(f"Bot error: {e}")
        time.sleep(5)


if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(main())

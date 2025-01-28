import json
import ssl
import certifi
import logging
import requests
import base64
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from transformers import VitsModel, AutoTokenizer, WhisperProcessor, WhisperForConditionalGeneration
import torch
import scipy.io.wavfile
import os
import librosa

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

os.environ["TOKENIZERS_PARALLELISM"] = "false"

class Config:
    def __init__(self):
        try:
            with open('config.json') as f:
                config = json.load(f)
                self.telegram_api_key = config['TelegramApiKey']
                self.voice_message_file_path = config['VoiceMessageFilePath']
                self.translate_kh_username = config['TranslateKHUsername']
                self.translate_kh_password = config['TranslateKHPassword']
            if not all([self.telegram_api_key, self.voice_message_file_path, 
                        self.translate_kh_username, self.translate_kh_password]):
                raise ValueError("Missing required configuration keys in 'config.json'.")
        except FileNotFoundError:
            raise FileNotFoundError("The 'config.json' file is missing. Please create it with the required keys.")


class TranscribeKHBot:
    def __init__(self):
        self.config = Config()
        self.application = Application.builder().token(self.config.telegram_api_key).build()
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.initialize_mms_model()
        self.initialize_whisper_model()

    def initialize_mms_model(self):
        logger.info("Initializing MMS model for Khmer TTS...")
        self.mms_model = VitsModel.from_pretrained("facebook/mms-tts-khm").to(self.device)
        self.mms_tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-khm")
        logger.info("MMS model initialized successfully.")

    def initialize_whisper_model(self):
        logger.info("Initializing Whisper model...")
        try:
            self.whisper_model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-medium").to(self.device)
            self.whisper_processor = WhisperProcessor.from_pretrained("openai/whisper-medium")
            self.whisper_model.eval()
            logger.info("Whisper model initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing Whisper model: {e}", exc_info=True)
            raise

    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
    
    def run(self):
        self.setup_handlers()
        logger.info("Bot is running...")
        self.application.run_polling()

    async def start_command(self, update: Update, context):
        await update.message.reply_text(
            "Welcome to Transcribe KH Bot\n"
            "Send a voice message, and the bot will convert it to text, translate to Khmer, and generate Khmer speech for you.\n"
            "Commands: \n"
            "/help - help information\n"
            "/select - select language"
        )

    async def help_command(self, update: Update, context):
        await update.message.reply_text("Send a voice message to get started")

    def preprocess_audio(self, audio_path):
        audio, sr = librosa.load(audio_path, sr=16000)
        audio = librosa.effects.trim(audio, top_db=20)[0]
        return audio

    async def handle_voice(self, update: Update, context):
        message = await update.message.reply_text("Processing your voice message")

        try:
            file = await update.message.voice.get_file()
            await file.download_to_drive(self.config.voice_message_file_path)
            
            preprocessed_audio = self.preprocess_audio(self.config.voice_message_file_path)
            input_features = self.whisper_processor(preprocessed_audio, sampling_rate=16000, return_tensors="pt").input_features

            # Create attention mask
            attention_mask = torch.ones_like(input_features)

            # Get the forced_decoder_ids for English transcription
            forced_decoder_ids = self.whisper_processor.get_decoder_prompt_ids(language="en", task="transcribe")

            # Generate transcription with forced_decoder_ids and attention mask
            predicted_ids = self.whisper_model.generate(
                input_features.to(self.device),
                attention_mask=attention_mask.to(self.device),
                forced_decoder_ids=forced_decoder_ids
            )
            transcription = self.whisper_processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]

            logger.info(f"Whisper transcription: {transcription}")
                
            try:
                khmer_text = self.translate_to_khmer(transcription)
            except Exception as e:
                logger.error(f"Error translating text: {str(e)}")
                await update.message.reply_text("An error occurred while translating the text. Please try again later.")
                return
            
            khmer_speech = self.khmer_text_to_speech(khmer_text)
            
            output_file = "khmer_speech.wav"
            scipy.io.wavfile.write(output_file, self.mms_model.config.sampling_rate, khmer_speech)
            
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message.message_id)
            await update.message.reply_text(f"Original (English): {transcription}\n\nTranslated (Khmer): {khmer_text}")
            
            await update.message.reply_voice(voice=open(output_file, "rb"))
            
        except Exception as e:
            logger.error(f"Error processing voice message: {str(e)}", exc_info=True)
            await update.message.reply_text("An error occurred while processing your voice message. Please try again later.")


    def translate_to_khmer(self, text):
        url = "https://translatekh.mptc.gov.kh/api"
        username = self.config.translate_kh_username
        password = self.config.translate_kh_password
        
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json"
        }
        
        data = {
            "input_text": [text],
            "src_lang": "eng",
            "tgt_lang": "kh"
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if "translate_text" in result and len(result["translate_text"]) > 0:
                return result["translate_text"][0]
            else:
                logger.error(f"Empty or invalid translation result: {result}")
                raise ValueError("Translation result is empty or invalid")
        except requests.RequestException as e:
            logger.error(f"Error calling Translate KH API: {str(e)}")
            raise

    @torch.no_grad()
    def khmer_text_to_speech(self, text):
        inputs = self.mms_tokenizer(text, return_tensors="pt").to(self.device)
        output = self.mms_model(**inputs).waveform
        return output.squeeze().cpu().numpy()

def main():
    bot = TranscribeKHBot()
    bot.run()

if __name__ == "__main__":
    main()

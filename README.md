# Transcribe KH Bot - Speech to Text

Transcribe KH Bot is an advanced Telegram bot designed for speech-to-text tasks. It transcribes English voice messages, translates them into Khmer, and generates Khmer text using open-source AI models for speech recognition and translation. In its latest version, it also includes the ability to generate Khmer speech, making it even more versatile.


## Transcribe KH Bot Demo

This video demonstration shows the bot transcribing a voice message, translating it to Khmer, and generating Khmer speech. Users can see how easy and efficient it is to use the bot directly in Telegram.

<video src="https://github.com/user-attachments/assets/e41287f7-12f5-4e44-b003-4bc094db1cb9"></video>


## Features

- Voice message transcription using Whisper
- English to Khmer translation using TranslateKH API
- Khmer text-to-speech synthesis using MMS-TTS
- User-friendly Telegram interface

## Prerequisites

- Python 3.8+
- CUDA-capable GPU (recommended for faster processing)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/lyfeyvutha/transcribe-kh-bot.git
   cd transcribe-kh-bot
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with the following structure:
   ```bash
   {
      TELEGRAM_API_KEY="YOUR_TELEGRAM_BOT_TOKEN"
      VOICE_MESSAGE_FILE_PATH="path/to/save/voice/messages",
      TRANSLATE_KH_USERNAME="YOUR_TRANSLATE_KH_USERNAME",
      TRANSLATE_KH_PASSWORD="YOUR_TRANSLATE_KH_PASSWORD"
   }
   ```

## Usage

1. Start the bot:
   ```bash
   python main.py
   ```

2. Open Telegram and start a conversation with your bot.

3. Send a voice message to the bot.

4. The bot will process your message and reply with:
   - The original English transcription
   - The Khmer translation
   - A voice message with the Khmer speech

## Commands

- `/start`: Initialize the bot and get a welcome message
- `/help`: Display help information

## Technical Details

- Speech Recognition: OpenAI's Whisper (medium model)
- Translation: TranslateKH API
- Text-to-Speech: Facebook's MMS-TTS for Khmer

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](https://github.com/lyfeyvutha/transcribe-kh-bot/blob/main/LICENSE) file for details.

## Acknowledgments

- OpenAI for the Whisper model
- Meta for the MMS-TTS model
- TranslateKH for their translation API

## Contact

For any queries or support, please open an issue in the GitHub repository.

## Author

[Chealyfey Vutha](https://github.com/lyfeyvutha)

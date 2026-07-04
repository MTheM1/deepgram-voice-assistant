# Deepgram Voice Assistant - Coffee Shop Demo

A voice-based coffee shop assistant. Talk to it, and it handles orders, menu lookups, and order tracking using Deepgram for speech recognition and OpenAI for the conversation logic.

## Features

- Voice recognition with Deepgram's Nova-3 model
- Chat with the assistant to place orders, ask about items, or look up orders
- Real-time audio streaming
- Simple order management system
- Order confirmation before processing

## Prerequisites

- Python 3.8+
- Deepgram API key

## Setup
1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate it:
   - `venv\Scripts\activate`

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root:
   ```
   DEEPGRAM_API_KEY=your_key
   ```

## Configuration

Edit `config.json` to change:
- Audio encoding and sample rates
- Which Deepgram model to use (currently `nova-3`)
- Which OpenAI model to use (currently `gpt-4o-mini`)
- The assistant's system prompt
- Available functions the assistant can call

## Running It

```bash
python main.py
```

Just start talking. Ask about menu items, place orders, or look up existing orders. The assistant will handle it.

Example things you can say:
- "What's a latte?"
- "I want to order two espressos"
- "Look up order number 5"

## Modes

Microphone Mode (default):
```bash
python main.py
```
from microphone to Deepgram to Your speakers. Local testing only. Just needs your Deepgram API key.

Twilio Mode:
```bash
python main.py --mode twilio
```
Opens a WebSocket server on `localhost:5000`. Twilio connects to it, sends audio from phone calls, and gets responses back. Requires a Deepgram API key and Twilio account with a phone number routed to your server.

## Dependencies

- `websockets` - WebSocket communication with Deepgram
- `sounddevice` - Audio input/output handling
- `python-dotenv` - Environment variable management

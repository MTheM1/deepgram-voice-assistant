import argparse
import asyncio
import base64
import json
import os

import sounddevice as sd
import websockets
from dotenv import load_dotenv
from functions import FUNCTION_MAP

load_dotenv()


def sts_connect():
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        raise Exception("DEEPGRAM_API_KEY not found")

    sts_ws = websockets.connect(
        "wss://agent.deepgram.com/v1/agent/converse",
        subprotocols=["token", api_key]
    )
    return sts_ws


def load_config():
    with open("config.json", "r") as f:
        return json.load(f)


def load_mic_config():
    config = load_config()
    config["audio"]["input"] = {
        "encoding": "linear16",
        "sample_rate": 16000,
    }
    config["audio"]["output"] = {
        "encoding": "linear16",
        "sample_rate": 16000,
        "container": "none",
    }
    return config


async def handle_barge_in(decoded, twilio_ws, streamsid):
    if twilio_ws is None:
        return

    if decoded["type"] == "UserStartedSpeaking":
        clear_message = {
            "event": "clear",
            "streamSid": streamsid
        }
        await twilio_ws.send(json.dumps(clear_message))


def execute_function_call(func_name, arguments):
    if func_name in FUNCTION_MAP:
        result = FUNCTION_MAP[func_name](**arguments)
        print(f"Function call result: {result}")
        return result
    else:
        result = {"error": f"Unknown function: {func_name}"}
        print(result)
        return result


def create_function_call_response(func_id, func_name, result):
    return {
        "type": "FunctionCallResponse",
        "id": func_id,
        "name": func_name,
        "content": json.dumps(result)
    }


async def handle_function_call_request(decoded, sts_ws):
    try:
        for function_call in decoded["functions"]:
            func_name = function_call["name"]
            func_id = function_call["id"]
            arguments = json.loads(function_call["arguments"])

            print(f"Function call: {func_name} (ID: {func_id}), arguments: {arguments}")

            result = execute_function_call(func_name, arguments)

            function_result = create_function_call_response(func_id, func_name, result)
            await sts_ws.send(json.dumps(function_result))
            print(f"Sent function result: {function_result}")

    except Exception as e:
        print(f"Error calling function: {e}")
        error_result = create_function_call_response(
            func_id if "func_id" in locals() else "unknown",
            func_name if "func_name" in locals() else "unknown",
            {"error": f"Function call failed with: {str(e)}"}
        )
        await sts_ws.send(json.dumps(error_result))


async def handle_text_message(decoded, twilio_ws, sts_ws, streamsid):
    await handle_barge_in(decoded, twilio_ws, streamsid)

    if decoded["type"] == "FunctionCallRequest":
        await handle_function_call_request(decoded, sts_ws)


async def print_text_messages(sts_ws, twilio_ws=None, streamsid=None, play_queue=None):
    async for message in sts_ws:
        if type(message) is str:
            print(message)
            decoded = json.loads(message)
            await handle_text_message(decoded, twilio_ws, sts_ws, streamsid)
        else:
            if twilio_ws is None and play_queue is not None:
                await play_queue.put(message)
            else:
                raw_mulaw = message

                media_message = {
                    "event": "media",
                    "streamSid": streamsid,
                    "media": {"payload": base64.b64encode(raw_mulaw).decode("ascii")}
                }

                await twilio_ws.send(json.dumps(media_message))


async def sts_sender(sts_ws, audio_queue):
    print("sts_sender started")
    while True:
        chunk = await audio_queue.get()
        await sts_ws.send(chunk)


async def sts_receiver(sts_ws, twilio_ws, streamsid_queue):
    print("sts_receiver started")
    streamsid = await streamsid_queue.get()
    await print_text_messages(sts_ws, twilio_ws, streamsid)


async def twilio_receiver(twilio_ws, audio_queue, streamsid_queue):
    BUFFER_SIZE = 20 * 160
    inbuffer = bytearray(b"")

    async for message in twilio_ws:
        try:
            data = json.loads(message)
            event = data["event"]

            if event == "start":
                print("get our streamsid")
                start = data["start"]
                streamsid = start["streamSid"]
                streamsid_queue.put_nowait(streamsid)
            elif event == "connected":
                continue
            elif event == "media":
                media = data["media"]
                chunk = base64.b64decode(media["payload"])
                if media["track"] == "inbound":
                    inbuffer.extend(chunk)
            elif event == "stop":
                break

            while len(inbuffer) >= BUFFER_SIZE:
                chunk = inbuffer[:BUFFER_SIZE]
                audio_queue.put_nowait(chunk)
                inbuffer = inbuffer[BUFFER_SIZE:]
        except:
            break


async def twilio_handler(twilio_ws):
    audio_queue = asyncio.Queue()
    streamsid_queue = asyncio.Queue()

    async with sts_connect() as sts_ws:
        config_message = load_config()
        await sts_ws.send(json.dumps(config_message))

        await asyncio.wait(
            [
                asyncio.ensure_future(sts_sender(sts_ws, audio_queue)),
                asyncio.ensure_future(sts_receiver(sts_ws, twilio_ws, streamsid_queue)),
                asyncio.ensure_future(twilio_receiver(twilio_ws, audio_queue, streamsid_queue)),
            ]
        )

        await twilio_ws.close()


async def mic_sender(sts_ws, audio_queue):
    print("mic_sender started")
    while True:
        chunk = await audio_queue.get()
        await sts_ws.send(chunk)


async def mic_capture(audio_queue):
    print("mic_capture started")
    loop = asyncio.get_running_loop()

    def callback(indata, frames, time, status):
        if status:
            print(status)
        loop.call_soon_threadsafe(audio_queue.put_nowait, bytes(indata))

    with sd.RawInputStream(
        samplerate=16000,
        channels=1,
        dtype="int16",
        callback=callback,
    ):
        await asyncio.Future()


async def mic_playback(play_queue):
    print("mic_playback started")

    with sd.RawOutputStream(
        samplerate=16000,
        channels=1,
        dtype="int16",
    ) as stream:
        while True:
            chunk = await play_queue.get()
            await asyncio.to_thread(stream.write, chunk)


async def mic_handler():
    audio_queue = asyncio.Queue()
    play_queue = asyncio.Queue()

    async with sts_connect() as sts_ws:
        config_message = load_mic_config()
        await sts_ws.send(json.dumps(config_message))

        await asyncio.gather(
            mic_sender(sts_ws, audio_queue),
            print_text_messages(sts_ws, play_queue=play_queue),
            mic_capture(audio_queue),
            mic_playback(play_queue),
        )


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["twilio", "mic"], default="mic")
    args = parser.parse_args()

    if args.mode == "mic":
        print("Started mic mode.")
        await mic_handler()
        return

    await websockets.serve(twilio_handler, "localhost", 5000)
    print("Started Twilio server on localhost:5000.")
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
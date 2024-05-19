import datetime
import threading
import time
import tkinter as tk

import ollama
import poe_api_wrapper
import pyaudiowpatch
import yaml

import src.service.google.translator as googletrans
from src import rtask
from src.common import sim
from src.rrecord import Recorder
from src.service.gui import barrage


def test_config():
    config_path = "../../config/cfg.yaml"
    with open(config_path, mode='r', encoding='utf-8') as config_file:
        cfg = yaml.safe_load(config_file)
    return cfg


def test_google():
    print("hello")
    trans = googletrans.GoogleTranslator(url_suffix="hk")
    ret = trans.translate("hello", "zh", "en")
    print(ret)


def test_poe():
    # https://github.com/snowby666/poe-api-wrapper?tab=readme-ov-file#how-to-get-your-token

    config_path = "../../config/cfg.yaml"
    with open(config_path, mode='r', encoding='utf-8') as config_file:
        cfg = yaml.safe_load(config_file)

    token = sim.get(cfg, {}, "poe", "token")
    bot_id = sim.get(cfg, "", "poe", "translate", "all").lower()

    poe = poe_api_wrapper.PoeApi(cookie=token)

    # ret = poe.get_chat_history(count=3, bot=bot_id)

    response = poe.get_chat_history(
        bot=bot_id,
        count=1,
    )

    chats = response["data"][bot_id]

    """
    [{'chatCode': '2ayefr830yxpi1bm7ej', 'chatId': 483212303, 'id': 'Q2hhdDo0ODMyMTIzMDM=', 'title': 'translator'}]
    """

    print(chats)

    """
    res = poe.send_message(bot_id, "translate 'power overwhelming' into chinese")
    chunk = None
    for chunk in res:
        pass    
    print(chunk["text"])    
    """


async def test_ollama():
    host = "http://127.0.0.1:11434"
    agent_ollama = ollama.AsyncClient(host=host)
    model = "sakura-13b"

    message = {
        'role': 'user',
        'content': '圧倒的な力',
    }
    result = await agent_ollama.chat(
        model=model,
        messages=[message],
    )
    print(result['message'].get('content', ''))


def test_time():
    create = time.time_ns() / 1_000_000
    time.sleep(2)
    finish = time.time_ns() / 1_000_000
    print(finish - create)


sum_len = 0
time_prev = 0


def test_denoising():
    # https://github.com/timsainb/noisereduce
    # https://github.com/timsainb/noisereduce/issues/44
    # https://gist.github.com/PandaWhoCodes/9f3dc05faee761149842e43b56e6ee8c
    """
           data = noisereduce.reduce_noise(
               y=io.BytesIO(data),
               sr=task.param.sample_rate,
           )
           """

    """
    # Assuming you have audio data in 'audio_bytes'        
    audio_array = noisereduce.frombuffer(data, dtype=noisereduce.int16)

    # Estimate noise profile (optional)
    noise_profile = noisereduce.profile(audio_array)

    # Apply noise reduction
    denoised_audio = noisereduce.reduce_noise(
        y=audio_array,
        sr=task.param.sample_rate,
        profile=noise_profile
    )
    """
    cfg = test_config()
    p_audio = pyaudiowpatch.PyAudio()
    task_ctrl = rtask.RTaskControl(cfg=cfg)
    recorder = Recorder(
        p_audio=p_audio,
        task_ctrl=task_ctrl,
    )
    recorder.init()

    def callback(frame, task):
        global sum_len
        global time_prev

        sum_len += len(frame)
        time_next = time.time_ns() / 1_000_000
        if time_prev <= 0:
            time_prev = time_next

        if time_next - time_prev > 100:
            current_time = datetime.datetime.now()
            t = current_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            print(f"{t}: {sum_len}")
            time_prev = time_next
            sum_len = 0

    recorder.record(callback=callback)


def test_barrage():
    def send_message():
        message = entry.get()
        label.config(text=message)
        entry.delete(0, tk.END)

    # Create the main window
    window = tk.Tk()
    window.title("Barrage GUI")

    # Create a label to display the message
    label = tk.Label(window, text="", font=("Arial", 16))
    label.pack(pady=10)

    # Create an entry field for input
    entry = tk.Entry(window, font=("Arial", 12))
    entry.pack(pady=10)

    # Create a button to send the message
    button = tk.Button(window, text="Send", command=send_message)
    button.pack(pady=10)

    # Start the main event loop
    window.mainloop()


def test_barrage_2():
    # Create the main window

    # Create the main window
    window = tk.Tk()
    window.attributes("-topmost", True)  # Set the window to be always on top

    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()

    window.geometry(f"{screen_w}x{screen_h}+{0}+{0}")  # Set window size and position
    window.attributes("-transparentcolor", "#F0F0F0")
    window.attributes("-toolwindow", True)
    window.overrideredirect(True)

    # Create a transparent canvas for the barrage text
    canvas = tk.Canvas(window, highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    # Create a list to store the barrage messages
    barrage_messages = []

    # Function to add a new barrage message
    def add_barrage_message(message):
        if len(barrage_messages) >= 10:
            # Remove the oldest message if the limit is reached
            canvas.delete(barrage_messages.pop(0))
            # Move existing messages up by 30 pixels
            for i in range(len(barrage_messages)):
                canvas.move(barrage_messages[i], 0, -30)
        x = 10
        y = (len(barrage_messages) + 1) * 30  # Adjust the vertical position of each message
        text = canvas.create_text(
            x, y,
            text=message, fill="#FF0000", font=("Arial", 24), anchor=tk.NW)
        barrage_messages.append(text)

    for i in range(15):
        add_barrage_message(f"Message {i}")

    # Start the main event loop
    window.mainloop()


def test_barrage_add(bar: barrage.RBarrage):
    for i in range(3):
        time.sleep(0.5)
        bar.add_barrage_message(f"Message {i}\nPower {i}")


def test_barrage_3():
    bar = barrage.RBarrage(cfg=test_config())
    t = threading.Thread(target=test_barrage_add, args=(bar,))
    t.start()

    bar.run()
    t.join()



if __name__ == '__main__':
    # asyncio.run(test_ollama())
    # test_poe()
    # test_denoising()
    test_barrage_3()
    pass

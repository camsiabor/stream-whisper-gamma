import datetime
import random
import threading
import time

import ollama
import poe_api_wrapper
import pyaudiowpatch
import yaml

import src.service.google.translator as googletrans
from src import rtask
from src.common import sim
from src.rrecord import Recorder
from src.service.gui.root import RGuiRoot


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


def test_barrage_add(bar: RGuiRoot):
    for i in range(0):
        timing = random.randint(1, 1024)
        bar.add_barrage(
            text=f"T {timing} I {i}",
            timing=timing,
        )


def test_barrage_3():
    gui_root = RGuiRoot(cfg=test_config())
    t = threading.Thread(target=test_barrage_add, args=(gui_root,))
    t.start()

    gui_root.init()
    gui_root.run_mainloop()


    # t.join()


def test_japanese_romanji():
    import cutlet
    katsu = cutlet.Cutlet()
    ret = katsu.romaji("カツカレーは美味しい")
    print(ret)




if __name__ == '__main__':
    # asyncio.run(test_ollama())
    # test_poe()
    # test_denoising()
    # test_barrage_3()
    test_barrage_3()

    pass

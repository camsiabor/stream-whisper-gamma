import time

import ollama
import poe_api_wrapper
import yaml

import src.service.google.translator as googletrans
from src.common import sim


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


if __name__ == '__main__':
    # asyncio.run(test_ollama())

    # test_poe()

    s = 'huggingface_hub.file_download'



    test_time()
    pass

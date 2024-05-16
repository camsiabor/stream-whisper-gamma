import asyncio

import ollama
import poe_api_wrapper
import yaml

import src.service.google.translator as googletrans


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

    bot_id = cfg["poe"]["bot_translate"]["id"]

    poe = poe_api_wrapper.PoeApi(cookie=cfg["poe"])

    # ret = poe.get_chat_history(count=3, bot=bot_id)

    res = poe.send_message(bot_id, "translate 'power overwhelming' into chinese")
    chunk = None
    for chunk in res:
        pass

    print(chunk["text"])


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


if __name__ == '__main__':
    asyncio.run(test_ollama())
    # test_ollama()
    pass

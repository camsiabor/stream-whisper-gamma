import logging

import poe_api_wrapper

from src import rtask
from src.common import sim, langutil


class OllamaCtrl:
    translate_map = {}

    def __init__(self, cfg):
        self.cfg = cfg
        self.agent = None
        self.active = False
        self.logger = logging.getLogger('ollama')

    def configure(self) -> 'OllamaCtrl':
        poe_cfg = sim.get(self.cfg, None, "ollama")

        self.active = sim.get(poe_cfg, False, "active")
        if not self.active:
            return self

        trans_map = sim.get(poe_cfg, None, "translate")
        if trans_map is None:
            raise Exception("poe translate map not found !")
        self.translate_map.clear()

        for lang_src, bot_info in trans_map.items():
            self.translate_map[lang_src] = rtask.RBot(
                lang=lang_src,
                bot_id=bot_info.get("id", ""),
                model=bot_info.get("model", ""),
                prompt_type=bot_info.get("prompt_type", ""),
            )

        self.agent = poe_api_wrapper.PoeApi(
            cookie=token
        )
        return self

    def get_chat_id(self, bot: rtask.RBot, create=True):
        response = self.agent.get_chat_history(
            bot=bot.id,
            count=1,
        )
        data = sim.get(response, None, "data", bot.id)
        if data is None or len(data) <= 0:
            if not create:
                return None
            _, chat_id = self.translate(bot.id, "hello", bot.lang)
        return data[0]["chatId"]

    def warmup_one(self, lang_src, bot):
        chat_id = self.get_chat_id(bot=bot, create=True)
        if chat_id is None or len(chat_id) <= 0:
            self.logger.error(f"chat not found for lang: {lang_src}")
        bot.chat_id = chat_id
        self.logger.info(f"for {lang_src} -> {bot.id} | chat_id : {bot.chat_id}")

    def warmup(self):
        if not self.active:
            return
        for lang_src, bot in self.translate_map.items():
            try:
                self.warmup_one(lang_src, bot)
            except Exception as ex:
                self.logger.error(f"failed to warmup for lang: {lang_src} | {ex}", exc_info=True, stack_info=True)

    def get_bot(self, mapping, lang_src):
        bot = mapping.get(lang_src, None)
        if bot is not None:
            return bot
        return mapping.get("all")

    def translate(self, text, lang_src, lang_des):
        bot = self.get_bot(self.translate_map, lang_src)
        if bot is None:
            raise Exception(f"bot not found for lang: {lang_src}")

        src_name = langutil.LANGUAGES[lang_src]
        des_name = langutil.LANGUAGES[lang_des]

        prompt = f"translate following {src_name} to {des_name}, return ONLY the translated text: {text}"
        res = self.agent.send_message(
            bot=bot.id,
            chatId=bot.chat_id,
            message=prompt,
        )

        if res is None:
            raise Exception("poe response is None")

        chunk = None
        for chunk in res:
            pass
        text_ret = chunk["text"]
        chat_id = chunk["chatId"]
        return text_ret, chat_id

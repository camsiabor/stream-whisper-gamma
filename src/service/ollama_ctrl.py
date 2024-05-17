import asyncio
import logging

import ollama

from src import rtask
from src.common import sim, langutil


class OllamaCtrl:
    domains = {}

    def __init__(self, cfg):
        self.cfg = cfg
        self.host = ""
        self.agent = None
        self.active = False

        self.logger = logging.getLogger('ollama')

    def configure(self, domain) -> 'OllamaCtrl':
        ollama_cfg = sim.get(self.cfg, {}, "ollama")
        self.active = sim.get(ollama_cfg, False, "active")
        if not self.active:
            return self

        self.host = url = sim.get(ollama_cfg, None, "host")
        if url is None or len(url) <= 0:
            raise Exception("ollama host not found !")
        mapping = sim.get(ollama_cfg, None, domain)
        if mapping is None:
            raise Exception(f"ollama {domain} mapping not found !")
        self.agent = ollama.AsyncClient(host=self.host)
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

    def warmup_one(self):
        asyncio.run(self.translate(
            text="hello",
            lang_src="en",
            lang_des="zh"
        ))

    def warmup(self, domain):
        if not self.active:
            return
        target = self.domains.get(domain, None)
        if target is None:
            raise Exception(f"ollama domain not found: {domain}")
        for key, bot in target.items():
            try:
                self.warmup_one()
            except Exception as ex:
                self.logger.error(f"failed to warmup: {key} | {ex}", exc_info=True, stack_info=True)

    def get_bot(self, domain, lang_src):
        mapping = self.domains.get(domain, None)
        if mapping is None:
            raise Exception(f"ollama domain not found: {domain}")
        bot = mapping.get(lang_src, None)
        if bot is not None:
            return bot
        return mapping.get("all")

    async def translate(self, text, lang_src, lang_des):

        bot = self.get_bot("translate", lang_src)

        src_name = langutil.LANGUAGES[lang_src]
        des_name = langutil.LANGUAGES[lang_des]

        if bot.prompt_type == "none":
            prompt = text
        else:
            prompt = f"translate following {src_name} to {des_name} and return ONLY the translated text: {text}"

        message = {
            'role': 'user',
            'content': prompt,
        }
        result = await self.agent.chat(
            model=bot.id,
            messages=[message],
        )
        """
        async for part in await self.agent_ollama.chat(
                model=model,
                messages=[message],
                stream=True
        ):
            result += part['message'].get('content', '')
        """
        return sim.get(result, '', 'message', 'content')

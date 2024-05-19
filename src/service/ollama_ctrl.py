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

        target = self.domains[domain] = {}
        for lang_src, bot_info in mapping.items():
            target[lang_src] = rtask.RBot(
                key=lang_src,
                lang=lang_src,
                model=bot_info.get("model", "").lower(),
                bot_id=bot_info.get("id", "").lower(),
                prompt_type=bot_info.get("prompt_type", "").lower(),
            )

        self.agent = ollama.AsyncClient(host=self.host)
        return self

    async def warmup_one(self):
        await self.translate(text="hello", lang_src="en", lang_des="zh")

    async def warmup(self, domain):
        if not self.active:
            return
        target = self.domains.get(domain, None)
        if target is None:
            raise Exception(f"ollama domain not found: {domain}")
        for key, bot in target.items():
            try:
                await self.warmup_one()
                self.logger.info(f"warmed up: {key} -> {bot.id}")
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

        src_name = langutil.LANGUAGES.get(lang_src, "en")
        des_name = langutil.LANGUAGES.get(lang_des, "en")

        if bot.prompt_type == "none":
            prompt = text
        else:
            prompt = langutil.translate_prompt(text, src_name, des_name)

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

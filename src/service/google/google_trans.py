import logging

from src.common import sim
from src.service.google.translator import GoogleTranslator


class GoogleTransCtrl:

    def __init__(self, cfg):
        self.cfg = cfg
        self.agent = None
        self.active = False
        self.logger = logging.getLogger('google-trans')

    def configure(self) -> 'GoogleTransCtrl':
        google_cfg = sim.getv(self.cfg, {}, "translator", "agent_google")
        self.active = sim.getv(google_cfg, False, "active")
        if not self.active:
            return self
        domain = sim.getv(google_cfg, "hk", "domain")
        timeout = sim.getv(google_cfg, 5, "timeout")
        self.agent = GoogleTranslator(
            url_suffix=domain,
            timeout=timeout,
        )
        return self

    def translate(self, text, lang_src, lang_des):
        return self.agent.translate(
            text, lang_des, lang_src
        )

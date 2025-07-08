"""
Vibe Service

This module provides a service for running PyServe with VibeMode.
VibeMode is a mode that allows you to let PyServe manage static and server by LLM.

Example:
    1. You visit https://your-domain.com/home
    2. In special configuration file you have prompt for LLM to generate code of static files for this page
    3. LLM generates code of static files for this page on-the-fly
    4. You receive generated page
    5. Now you can save this page or just skip it

As you can understand, this is a very funny feature that allows you to create dynamic pages on-the-fly.
"""

from pyserve import AsyncHTTPServer, Configuration, get_logger
from .vibe_config import VibeConfig
from .cache import VibeCache
from .llm import VibeLLMClient
import asyncio
import aiohttp
import os

class VibeService:
    def __init__(self, server: AsyncHTTPServer, config: Configuration, vibe_config: VibeConfig):
        self.server = server
        self.config = config
        self.vibe_config = vibe_config
        self.cache = VibeCache()
        self.llm = VibeLLMClient(
            api_url=self.vibe_config.get_api_url(),
            model=self.vibe_config.settings.get('model', 'gpt-3.5-turbo')
        )
        self.cache_ttl = self.vibe_config.settings.get('cache_ttl', 3600)
        self.timeout = self.vibe_config.settings.get('timeout', 20)
        self.fallback_enabled = self.vibe_config.settings.get('fallback_enabled', True)

    async def run(self):
        from aiohttp import web
        logger = get_logger()

        async def handle(request):
            path = request.path
            client_ip = request.remote
            
            logger.info(f"PyVibeServe request: {client_ip} -> {path}")
            
            prompt = self.vibe_config.get_prompt(path)
            if not prompt:
                logger.warning(f"No prompt configured for path: {path}")
                return web.Response(status=404, text="Not found (Vibe-Serving)")
            
            cached = self.cache.get(path, self.cache_ttl)
            if cached:
                logger.info(f"Serving cached content for: {path}")
                return web.Response(text=cached, content_type="text/html")
            
            try:
                logger.info(f"Generating AI content for: {path}")
                html = await self.llm.generate(prompt, timeout=self.timeout)
                self.cache.set(path, html)
                logger.info(f"AI content generated and cached for: {path}")
                return web.Response(text=html, content_type="text/html")
            except Exception as e:
                logger.error(f"Failed to generate content for {path}: {e}")
                error_path = os.path.join("templates", "vibe_error.html")
                if os.path.exists(error_path):
                    with open(error_path, "r", encoding="utf-8") as f:
                        return web.Response(text=f.read(), content_type="text/html", status=504)
                return web.Response(text="Ошибка генерации страницы", status=504)

        app = web.Application()
        app.router.add_get('/{tail:.*}', handle)
        port = self.config.server_config.get('port', 8000)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        
        return runner

    def generate_page(self, path: str):
        # TODO: page generation logic
        pass

    def save_page(self, path: str, page: str):
        # TODO: page saving logic
        pass

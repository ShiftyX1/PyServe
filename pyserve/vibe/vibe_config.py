import yaml

class VibeConfig:
    def __init__(self):
        self.config = {}
        self.routes = {}
        self.settings = {}

    def load_config(self, config_path: str):
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        self.routes = self.config.get('routes', {})
        self.settings = self.config.get('settings', {})

    def get_config(self):
        return self.config

    def get_prompt(self, path: str):
        return self.routes.get(path)

    def get_timeout(self):
        return self.settings.get('timeout', 20)

    def get_api_url(self):
        return self.settings.get('api_url', None)
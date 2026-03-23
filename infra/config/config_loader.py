# 配置加载器
# infra/config/config_loader.py
import os
import re
import yaml
from pathlib import Path
from dotenv import load_dotenv

class ConfigLoader:
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            load_dotenv()  # 加载 .env 文件
            self._load_config()

    def _load_config(self):
        config_path = Path(__file__).parent / 'settings.yaml'
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # 替换环境变量占位符 ${VAR}
        pattern = re.compile(r'\${([^}]+)}')
        def repl(match):
            var = match.group(1)
            return os.getenv(var, '')
        content = pattern.sub(repl, content)
        self._config = yaml.safe_load(content)

    def get(self, key: str, default=None):
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

# 单例实例
config = ConfigLoader()
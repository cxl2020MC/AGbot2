import tomllib

from .types import bot_config


def load_config(fp):
    config = tomllib.load(fp)
    return bot_config.Config.model_validate(config)

config = load_config(open("config.toml", "rb"))
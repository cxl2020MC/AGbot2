import tomllib

from .types import bot_config


def load_config(config_file):
    with open(config_file, "r") as f:
        config = tomllib.loads(f.read())
    return bot_config.Config.model_validate(config)


config = load_config("config.toml")

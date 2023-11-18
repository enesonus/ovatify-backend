from django.apps import AppConfig

AppConfig.default = False


class SongsConfig(AppConfig):
    name = 'songs'
    label = 'songs'

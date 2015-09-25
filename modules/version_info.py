def init():
    event_handler.hook('bot:on_get_version', on_get_version)

def on_get_version(bot):
    return ' | '.join(bot.db.get_all('version_info'))

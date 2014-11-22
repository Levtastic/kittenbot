import logging

from responsebot import ResponseBot

def main():
	logging.basicConfig(
		filename = 'kittenbot.log',
		level = logging.INFO,
		format = '[%(asctime)s] %(message)s',
		datefmt = '%m/%d/%Y %H:%M:%S'
	)
	ResponseBot(
		nickname = 'kitten',
		realname = 'KittenBot (admin contact: Lev)',
		server = 'irc.foonetic.net',
		port = 6667,
		db_name = 'kittenbot.db',
		join_commands = [
			#('privmsg', {'target': 'AuthServ@Services.GameSurge.net', 'text': 'auth KittenBot nJPY9jP7'}),
		],
		command_aliases = {
			'sleep': 'die',
		},
		nick_aliases = [
			'kitten',
			'kitty',
		],
		random_timings = {
			'part': 6 * 60 * 60, # every 6 hours
			'join': 6 * 60 * 60, # every 6 hours
			'message': 60 * 60, # every 1 hour
		}
	).start()

if __name__ == '__main__':
    main()

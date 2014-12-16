import sys
import logging
import datetime

from responsebot import ResponseBot

def main():
	if len(sys.argv) != 3:
		print("Usage: kittenbot.py <server[:port]> <server name>")
		sys.exit(1)
	
	s = sys.argv[1].split(":", 1)
	server = s[0]
	if len(s) == 2 and s[1].isdigit():
		port = int(s[1])
	else:
		port = 6667
	
	logging.basicConfig(
		filename = 'logs/%s %s.log' % (sys.argv[2], datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')),
		level = logging.INFO,
		format = '[%(asctime)s] %(message)s\n',
		datefmt = '%m/%d/%Y %H:%M:%S'
	)
	ResponseBot(
		nickname = 'ResponseBot',
		realname = 'KittenBot (admin contact: Lev)',
		server_name = sys.argv[2],
		server = server,
		port = port,
		module_parameters = {
			'database:name': 'kittenbot.db',
		}
	).start()

if __name__ == '__main__':
    main()

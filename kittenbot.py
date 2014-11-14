"""
	cache user accounts by nick only for people in visible channels
	if not in visible channel, can't see nick changes to make sure is same person with access
	if person leaves all visible channels, remove from cache, look up every time
"""

from responsebot import ResponseBot

def main():
	ResponseBot(
		'KittenBot',
		'KittenBot (admin contact: Lev)',
		#'irc.foonetic.net',
		'irc.gamesurge.net',
		6667,
		'kittenbot.db',
		{
			'sleep': 'die',
		},
		[
			'kitten',
			'kitty',
		],
		{
			'part': 60 * 60,
			'join': 60 * 60,
			'action': 20 * 60,
		}
	).start()

if __name__ == '__main__':
    main()

import sqlite3
import os

db = sqlite3.connect('kittenbot.db')
c = db.cursor()

for filename in os.listdir('temp_response_files'):
	if filename[-4:] == '.txt':
		shortname = filename[6:-4].strip()
		if shortname == 'action':
			table_name = 'random_actions'
		elif shortname == 'affirm':
			table_name = 'completed_command_messages'
		elif shortname == 'deny':
			table_name = 'unknown_command_messages'
		elif shortname == 'entrances':
			table_name = 'join_messages'
		elif shortname == 'exits':
			table_name = 'part_messages'
		elif shortname == 'mentions':
			table_name = 'random_mentions'
		else:
			print(shortname)
			exit()
		
		c.execute("""
			DELETE FROM
				%s
		""" % table_name)
		
		with open('temp_response_files\\' + filename, 'r') as f:
			for line in f:
				if line[-1] == '.':
					line = line[:-1]
				c.execute("""
					INSERT INTO
						%s
						(message_text)
					VALUES
						(?)
				""" % table_name,
					(
						line
							.replace('kitten', '%(me)s')
							.replace('!SOMEONE', '%(someone)s')
							.replace('!someone', '%(someone)s')
							.replace('!who', '%(speaker)s')
							.strip()
					, )
				)

c.execute("""
	DELETE FROM
		response_messages
""")

for filename in os.listdir('temp_response_files\\factoids'):
	if filename[-4:] == '.txt':
		trigger = filename[:-4].replace('kitten', '%(me)s')
		
		with open('temp_response_files\\factoids\\' + filename, 'r') as f:
			for line in f:
				if line[-1] == '.':
					line = line[:-1]
				c.execute("""
					INSERT INTO
						response_messages
						(trigger, message_text, response_type_id)
					VALUES
						(?, ?, 1)
				""",
					(
						trigger.replace('_', ' ').strip(),
						line
							.replace('kitten', '%(me)s')
							.replace('!SOMEONE', '%(someone)s')
							.replace('!someone', '%(someone)s')
							.replace('!who', '%(speaker)s')
							.strip()
					)
				)

db.commit()

import logging
import sqlite3

from contextlib import closing

def init():
	bot.db = Database(bot.module_parameters['database:name'])

class Database():
	def __init__(self, db_name):
		self.last_random_ids = {}
		
		self.database = sqlite3.connect(db_name)
		self.database.create_function('message_match', 4, self.message_match)
		self.database.create_function('key_start', 1, self.key_start)
		if not self.database_exists():
			self.build_database()
	
	def __del__(self):
		try:
			self.database.close()
		except BaseException:
			pass
	
	def message_match(self, db_key, input_message, input_message_type_code, levenshtein_threshhold):
		try:
			message_type_matches = []
			
			for c in db_key:
				if c in ('~', '-', '*') and c not in message_type_matches:
					message_type_matches.append(c)
				else:
					break
			else:
				return False
			
			if not message_type_matches or not input_message_type_code in message_type_matches:
				return False
			
			db_message = db_key[db_key.index(message_type_matches[-1])+1:].lower()
			input_message = input_message.lower()
			if db_message[0] == ' ':
				db_message = db_message[1:]
			
			if '~' in message_type_matches and db_message in input_message:
				return True
			
			if self.relative_levenshtein(db_message, input_message) >= float(levenshtein_threshhold):
				return True
			
			return False
		except BaseException as e:
			error = 'Exception in message_match sql function: %s: %s' % (type(e).__name__, e)
			print(error)
			logging.exception(error)
			return False
	
	def relative_levenshtein(self, a, b):
		n, m = len(a), len(b)
		if n > m:
			a, b = b, a
			n, m = m, n
		
		current = range(n + 1)
		for i in range(1, m + 1):
			previous, current = current, [i] + [0] * n
			for j in range(1, n + 1):
				add, delete = previous[j] + 1, current[j - 1] + 1
				change = previous[j - 1]
				if a[j - 1] != b[i - 1]:
					change = change + 1
				current[j] = min(add, delete, change)
		
		return 1 - current[n] / m
	
	def key_start(self, key):
		split = '|'
		
		if split not in key:
			return key
		
		return key[:key.index(split)]
	
	def database_exists(self):
		with closing(self.database.cursor()) as cursor:
			cursor.execute("""
				SELECT
					COUNT(1)
				FROM
					sqlite_master
				WHERE
					type = 'table'
			""")
			return int(cursor.fetchone()[0]) > 0
	
	def build_database(self):
		with closing(self.database.cursor()) as cursor:
			cursor.execute("""
				CREATE TABLE
					vars
				(
					id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
					key TEXT NOT NULL,
					value TEXT NOT NULL
				)
			""")
			cursor.execute("""
				CREATE INDEX
					var_keys
				ON
					vars
				(
					key
				)
			""")
		
		self.database.commit()
	
	def get(self, key_filter, value_filter = '', default_value = ''):
		if not value_filter:
			value_filter = '%'
		
		with closing(self.database.cursor()) as cursor:
			cursor.execute("""
				SELECT
					value
				FROM
					vars
				WHERE
						key LIKE ?
					AND
						value LIKE ?
				ORDER BY
					id ASC
				LIMIT
					1
			""",
				(key_filter, value_filter)
			)
			result = cursor.fetchone()
		
		if result:
			return result[0]
		else:
			return default_value
	
	def get_key_value(self, key_filter, value_filter = '', default_value = (None, None)):
		if not value_filter:
			value_filter = '%'
		
		with closing(self.database.cursor()) as cursor:
			cursor.execute("""
				SELECT
					key,
					value
				FROM
					vars
				WHERE
						key LIKE ?
					AND
						value LIKE ?
				ORDER BY
					id ASC
				LIMIT
					1
			""",
				(key_filter, value_filter)
			)
			result = cursor.fetchone()
		
		if result:
			return (result[0], result[1])
		else:
			return default_value
	
	def get_random(self, key_filter, default_value = ''):
		if key_filter.lower() in self.last_random_ids:
			last_id = self.last_random_ids[key_filter.lower()]
		else:
			last_id = 0
		
		with closing(self.database.cursor()) as cursor:
			cursor.execute("""
				SELECT
					id,
					value
				FROM
					vars
				WHERE
					key LIKE ?
				ORDER BY
					CASE
						WHEN id = ? THEN 1
						ELSE 0
					END ASC,
					RANDOM()
				LIMIT
					1
			""",
				(key_filter, last_id)
			)
			result = cursor.fetchone()
		
		if result:
			self.last_random_ids[key_filter.lower()] = result[0]
			return result[1]
		else:
			return default_value
	
	def get_reply(self, message, message_type_code, default_value = ''):
		if message.lower() in self.last_random_ids:
			last_id = self.last_random_ids[message.lower()]
		else:
			last_id = 0
		
		with closing(self.database.cursor()) as cursor:
			cursor.execute("""
				SELECT
					id,
					value
				FROM
					vars
				WHERE
						SUBSTR(key, 1, 1) IN ('~', '-', '*')
					AND
						message_match(key, ?, ?, ?)
				ORDER BY
					CASE
						WHEN SUBSTR(key, 1, 1) = '~' THEN 1
						ELSE 0
					END ASC,
					CASE
						WHEN
								SUBSTR(key, 1, 2) NOT LIKE '%-%'
							OR
								SUBSTR(key, 1, 3) NOT LIKE '%*%'
							THEN 1
						ELSE 0
					END DESC,
					CASE
						WHEN id = ? THEN 1
						ELSE 0
					END ASC,
					RANDOM()
				LIMIT
					1
			""",
				(message, message_type_code, self.get('levenshtein_threshhold', default_value = 1), last_id)
			)
			result = cursor.fetchone()
		
		if result:
			self.last_random_ids[message.lower()] = result[0]
			return result[1]
		else:
			return default_value
	
	def get_all(self, key_filter, value_filter = '', default_value = []):
		if not value_filter:
			value_filter = '%'
		
		with closing(self.database.cursor()) as cursor:
			cursor.execute("""
				SELECT
					value
				FROM
					vars
				WHERE
						key LIKE ?
					AND
						value LIKE ?
				ORDER BY
					id ASC
			""",
				(key_filter, value_filter)
			)
			result = [row[0] for row in cursor]
		
		if result:
			return result
		else:
			return default_value
	
	def list(self, results_per_page, page_number, search_string, key_filter = '', messages_only = True, default_value = []):
		binary_comparison = 'AND'
		if not key_filter and search_string:
			key_filter = search_string
			binary_comparison = 'OR'
		elif not search_string and key_filter:
			search_string = key_filter
			binary_comparison = 'OR'
		elif not search_string:
			return default_value
		
		with closing(self.database.cursor()) as cursor:
			cursor.execute("""
				SELECT
					key,
					value
				FROM
					vars
				WHERE
						key LIKE ?
					%s
						value LIKE ?
			""" % binary_comparison + (
				messages_only and 'AND (key LIKE "~%" OR key LIKE "%-%" OR key LIKE "%*%")' or ''
			) + """
				ORDER BY
					id ASC
				LIMIT
					?, ?
			""",
				(
					'%' + key_filter + '%',
					'%' + search_string + '%',
					(page_number - 1) * results_per_page,
					results_per_page,
				)
			)
			result = [(row[0], row[1]) for row in cursor]
		
		if result:
			return result
		else:
			return default_value
	
	def list_keys(self, messages_only = True):
		with closing(self.database.cursor()) as cursor:
			cursor.execute("""
				SELECT DISTINCT
					key_start(key)
				FROM
					vars
				WHERE
					SUBSTR(key, 1, 1) NOT IN ('~', '-', '*')
				ORDER BY
					1
			""")
			result = [row[0] for row in cursor]
		
		return result
	
	def check_exists(self, key_filter, value_filter = ''):
		if not value_filter:
			value_filter = '%'
		
		with closing(self.database.cursor()) as cursor:
			cursor.execute("""
				SELECT
					COUNT(1)
				FROM
					vars
				WHERE
						key LIKE ?
					AND
						value LIKE ?
			""",
				(key_filter, value_filter)
			)
			return int(cursor.fetchone()[0])
	
	def set(self, key, value, value_filter = ''):
		if not isinstance(value, (list, str)):
			return False
		
		self.delete(key, value_filter, True)
		
		return self.add(key, value)
	
	def add(self, key, value):
		if not isinstance(value, (tuple, list, str)):
			return False
		
		if isinstance(value, str):
			value = (value, )
		
		for v in value:
			if self.check_exists(key, v):
				return False
		
		with closing(self.database.cursor()) as cursor:
			cursor.executemany("""
				INSERT INTO
					vars
					(key, value)
				VALUES
					(?, ?)
			""", 
				[(key, v) for v in value]
			)
		
		self.database.commit()
		return True
	
	def delete(self, key_filter, value_filter = '', override_check = False):
		if not value_filter:
			value_filter = '%'
		
		if not override_check and self.check_exists(key_filter, value_filter) != 1:
			return False
		
		with closing(self.database.cursor()) as cursor:
			cursor.execute("""
				DELETE FROM
					vars
				WHERE
						key LIKE ?
					AND
						value LIKE ?
			""",
				(key_filter, value_filter)
			)
		
		self.database.commit()
		return True
	
	def sql(self, connection, reply_target, command):
		cursor = self.database.cursor()
		
		try:
			cursor.execute(command)
		except BaseException as e:
			bot.send(connection, reply_target, '-' + str(e), None, False)
			return False
		
		if cursor.description:
			bot.send(connection, reply_target, ' | '.join(c[0] for c in cursor.description), None, False)
		
		for row in cursor:
			bot.send(connection, reply_target, ' | '.join(str(r) for r in row), None, False)
		
		self.database.commit()
		return True

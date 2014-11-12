import sqlite3

class ResponseDatabase():
	def __init__(self, db_name):
		self.database = sqlite3.connect(db_name)
		cursor = self.database.cursor()
		cursor.execute("""
			SELECT
				COUNT(1)
			FROM
				sqlite_master
			WHERE
				type = 'table'
		""")
		if cursor.fetchone()[0] < 1:
			from dbbuilder import DbBuilder
			db_builder = DbBuilder()
			db_builder.build_database(self.database)
	
	def get_whois_auth_level(self, account_name):
		cursor = self.database.cursor()
		cursor.execute("""
			SELECT
				ut.level
			FROM
				users AS u
			INNER JOIN
				user_types AS ut
				ON
					ut.id = u.user_type_id
			WHERE
				u.account_name = ?
			LIMIT
				1
		""",
			(account_name, )
		)
		result = cursor.fetchone()
		if result is not None:
			return result[0]
		
		return 0

	def get_channels(self, server_name, include_blacklisted = False):
		cursor = self.database.cursor()
		cursor.execute("""
			SELECT
				channel_name,
				blacklisted
			FROM
				channels
			WHERE
					blacklisted = 0
				AND
					server_name = ?
		""",
			(server_name, )
		)
		if include_blacklisted:
			return [row[0] for row in cursor]
		else:
			return [row[0] for row in cursor if row[1] == 0]

	def get_random(self, table_name, column_name = 'message_text'):
		cursor = self.database.cursor()
		cursor.execute("""
			SELECT
				%s
			FROM
				%s
			ORDER BY
				RANDOM()
			LIMIT
				1
		""" % (column_name, table_name)
		)
		result = cursor.fetchone()
		if result is not None:
			return result[0]
		
		return ''
	
	def get_random_response(self, trigger):
		cursor = self.database.cursor()
		cursor.execute("""
			SELECT
				message_text
			FROM
				response_messages
			WHERE
				trigger = ?
			ORDER BY
				RANDOM()
			LIMIT
				1
		""",
			(trigger, )
		)
		result = cursor.fetchone()
		if result is not None:
			return result[0]
		
		return ''

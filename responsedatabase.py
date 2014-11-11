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
	
	def get_whois_auth_level(self, whois_data):
		if len(whois_data) < 4:
			return 0
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
			(whois_data[4], )
		)
		result = cursor.fetchone()
		if result is not None:
			return result[0]
		
		return 0

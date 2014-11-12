class DbBuilder():
	def build_database(self, db):
		self.cursor = db.cursor()
		self.build_user_types()
		self.build_users()
		self.build_channels()
		self.build_join_messages()
		self.build_part_messages()
		self.build_unknown_command_messages()
		self.build_completed_command_messages()
		self.build_random_actions()
		self.build_random_mentions()
		self.build_response_types()
		self.build_response_messages()
		db.commit()
	
	def build_user_types(self):
		self.cursor.execute("""
			CREATE TABLE
				user_types
			(
				id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
				name TEXT NOT NULL,
				code TEXT NOT NULL,
				level INTEGER NOT NULL
			)
		""")
		self.cursor.executemany("""
			INSERT INTO
				user_types
				(name, code, level)
			VALUES
				(?, ?, ?)
		""", [
			('Administrator', 'admin', 100),
			('User', 'user', 50),
			('None', 'none', 0),
			('Blacklisted', 'blacklisted', -50),
		])
	
	def build_users(self):
		self.cursor.execute("""
			CREATE TABLE
				users
			(
				id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
				account_name TEXT NOT NULL,
				user_type_id INTEGER NOT NULL
			)
		""")
		self.cursor.execute("""
			INSERT INTO
				users
				(account_name, user_type_id)
			SELECT
				?, 
				id
			FROM
				user_types
			WHERE
				code = ?
			LIMIT
				1
		""",
			('Lev', 'admin')
		)
	
	def build_channels(self):
		self.cursor.execute("""
			CREATE TABLE
				channels
			(
				id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
				channel_name TEXT NOT NULL,
				server_name TEXT NOT NULL,
				blacklisted INTEGER NOT NULL DEFAULT 0,
				blacklist_reason TEXT NOT NULL DEFAULT ''
			)
		""")
	
	def build_join_messages(self):
		self.cursor.execute("""
			CREATE TABLE
				join_messages
			(
				id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
				message_text TEXT NOT NULL
			)
		""")
		self.cursor.execute("""
			INSERT INTO
				join_messages
				(message_text)
			VALUES
				(?)
		""",
			('enters the room', )
		)
	
	def build_part_messages(self):
		self.cursor.execute("""
			CREATE TABLE
				part_messages
			(
				id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
				message_text TEXT NOT NULL
			)
		""")
		self.cursor.execute("""
			INSERT INTO
				part_messages
				(message_text)
			VALUES
				(?)
		""",
			('leaves the room', )
		)
	
	def build_unknown_command_messages(self):
		self.cursor.execute("""
			CREATE TABLE
				unknown_command_messages
			(
				id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
				message_text TEXT NOT NULL
			)
		""")
		self.cursor.execute("""
			INSERT INTO
				unknown_command_messages
				(message_text)
			VALUES
				(?)
		""",
			('ignores %(speaker)s', )
		)
	
	def build_completed_command_messages(self):
		self.cursor.execute("""
			CREATE TABLE
				completed_command_messages
			(
				id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
				message_text TEXT NOT NULL
			)
		""")
		self.cursor.execute("""
			INSERT INTO
				completed_command_messages
				(message_text)
			VALUES
				(?)
		""",
			('acknowledges %(speaker)s', )
		)
	
	def build_random_actions(self):
		self.cursor.execute("""
			CREATE TABLE
				random_actions
			(
				id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
				message_text TEXT NOT NULL
			)
		""")
	
	def build_random_mentions(self):
		self.cursor.execute("""
			CREATE TABLE
				random_mentions
			(
				id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
				message_text TEXT NOT NULL
			)
		""")
	
	def build_response_types(self):
		self.cursor.execute("""
			CREATE TABLE
				response_types
			(
				id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
				name TEXT NOT NULL,
				code TEXT NOT NULL
			)
		""")
		self.cursor.executemany("""
			INSERT INTO
				response_types
				(name, code)
			VALUES
				(?, ?)
		""", [
			('Action', 'action'),
			('Message', 'message'),
			('Both', 'both'),
		])
	
	def build_response_messages(self):
		self.cursor.execute("""
			CREATE TABLE
				response_messages
			(
				id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
				trigger TEXT NOT NULL,
				message_text TEXT NOT NULL,
				response_type_id INTEGER NOT NULL,
				action_code TEXT NOT NULL DEFAULT ""
			)
		""")

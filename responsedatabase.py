import logging
import sqlite3
import re

class ResponseDatabase():
	last_random_ids = {
		'trigger': 0,
	}
	
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
			# if we don't have our tables, import the DB builder and run it - first time setup only
			from dbbuilder import DbBuilder
			DbBuilder().build_database(self.database)
	
	def get_whois_auth_level(self, account_name, server_name):
		cursor = self.database.cursor()
		cursor.execute("""
			SELECT
				auth_level
			FROM
				users
			WHERE
					account_name = ?
				AND
					server_name IN (?, '')
			LIMIT
				1
		""",
			(account_name, server_name)
		)
		result = cursor.fetchone()
		if result:
			return result[0]
		else:
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
	
	def get_random(self, table_name):
		if table_name in self.last_random_ids:
			last_id = self.last_random_ids[table_name]
		else:
			last_id = 0
		
		cursor = self.database.cursor()
		cursor.execute("""
			SELECT
				t.id,
				t.message_text,
				rt.code
			FROM
				%s AS t
			INNER JOIN
				response_types AS rt
				ON
					rt.id = t.response_type_id
			ORDER BY
				CASE
					WHEN t.id = ? THEN 1
					ELSE 0
				END ASC,
				RANDOM()
			LIMIT
				1
		""" % table_name, # NOT SQL PROTECTED - don't ever use user input with this function
			(last_id, )
		)
		result = cursor.fetchone()
		if result:
			id, message_text, code = result
			self.last_random_ids[table_name] = id
			return (message_text, code)
		else:
			return None
	
	def get_random_response(self, trigger, is_action):
		trigger_type = is_action and 'action' or 'message'
		cursor = self.database.cursor()
		cursor.execute("""
			SELECT
				rm.id,
				rm.message_text,
				rt.code
			FROM
				response_messages AS rm
			INNER JOIN
				trigger_types AS tt
				ON
					tt.id = rm.trigger_type_id
			INNER JOIN
				response_types AS rt
				ON
					rt.id = rm.response_type_id
			WHERE
					LOWER(rm.trigger) = LOWER(?)
				AND
					tt.code IN (?, 'both')
			ORDER BY
				CASE
					WHEN rm.id = ? THEN 1
					ELSE 0
				END ASC,
				RANDOM()
			LIMIT
				1
		""",
			(trigger.strip(), trigger_type, self.last_random_ids['trigger'])
		)
		result = cursor.fetchone()
		if result:
			id, message_text, code = result
			self.last_random_ids['trigger'] = id
			return (message_text, code)
		else:
			return None
	
	def set_channel_blacklist(self, channel, server, blacklisted = True, reason = ''):
		cursor = self.database.cursor()
		cursor.execute("""
			UPDATE
				channels
			SET
				blacklisted = ?,
				blacklist_reason = ?
			WHERE
					channel_name = ?
				AND
					server_name = ?
		""",
			(blacklisted, reason, channel, server)
		)
		self.database.commit()
	
	def do_command(self, connection, server_name, reply_target, table_aliases, command, parameters, auth_level, nicknames):
		params = parameters.strip().split(' ', 1)
		if not params:
			return False
		
		table = params[0]
		
		if len(params) > 1:
			parameters = params[1]
		else:
			parameters = ''
		
		if table in table_aliases:
			table = table_aliases[table]
		elif table[:-1] in table_aliases:
			table = table_aliases[table[:-1]]
		else:
			# don't allow random input for the table field
			# this field is directly inserted into SQL statements
			return False
		
		if command == 'remove':
			return self.remove_by_id_or_filter(server_name, table, parameters, auth_level)
		
		elif command == 'list':
			return self.list_records(connection, server_name, reply_target, table, parameters)
		
		elif command == 'add':
			if table == 'channels' and auth_level < 50:
				return False
			
			return self.add_record(server_name, table, auth_level, parameters, nicknames)
		
		else:
			return False
		
		return True
	
	def add_record(self, server_name, table, auth_level, parameters, nicknames):
		query = 'INSERT INTO %s ' % table
		
		if table == 'channels':
			query += '(channel_name, server_name) VALUES (?, ?)'
			if parameters[0] != '#':
				parameters = '#' + parameters.strip()
			query_params = (parameters.strip(), server_name)
		
		elif table == 'users':
			query += '(account_name, server_name, auth_level) VALUES (?, ?, ?)'
			
			params = parameters.strip().split(' ')
			if len(params) > 2:
				return False
				
			elif len(params) == 1:
				if not params[0]:
					return False
				
				auth_level = 30 # default
			
			else:
				auth_level = params[1]
			
			account_name = params[0]
			
			query_params = (account_name, server_name, auth_level)
		
		elif table == 'response_messages':
			params = parameters.strip().split(' ', 1)
			if len(params) == 1:
				return False
			
			trigger_type, parameters = params
			
			params = parameters.strip().split('=', 1)
			if len(params) == 1:
				return False
			
			trigger_text, parameters = params
			
			params = parameters.strip().split(' ', 1)
			if len(params) == 1:
				return False
			
			message_type, message_text = params
			
			trigger_type_id = self.get_response_type_id_by_code(trigger_type)
			message_type_id = self.get_response_type_id_by_code(message_type)
			
			if not trigger_type_id or not message_type_id:
				return False
			
			query += '(trigger, message_text, trigger_type_id, response_type_id) VALUES (?, ?, ?, ?)'
			query_params = (self.replace_name(trigger_text, nicknames).strip(), message_text, trigger_type_id, message_type_id)
		
		else:
			params = parameters.split(' ', 1)
			if len(params) == 1:
				return False
			
			message_type, message_text = params
			
			message_type_id = self.get_response_type_id_by_code(message_type)
			
			query += '(message_text, response_type_id) VALUES (?, ?)'
			query_params = (self.replace_name(message_text, nicknames).strip(), message_type_id)
		
		cursor = self.database.cursor()
		try:
			cursor.execute(query, query_params)
			self.database.commit()
		except BaseException as e:
			logging.error('%s %s, query: %s' % (type(e), e, query))
			return False
		
		return True
	
	def replace_name(self, message, names):
		for name in names:
			message = re.sub('(?i)' + re.escape(name), '!me', message)
		
		return message
	
	def get_response_type_id_by_code(self, code):
		cursor = self.database.cursor()
		cursor.execute("""
			SELECT
				id
			FROM
				response_types
			WHERE
				code = ?
			LIMIT
				1
		""",
			(code.strip().lower(), )
		)
		result = cursor.fetchone()
		if result:
			return result[0]
		else:
			return False
	
	def list_records(self, connection, server_name, reply_target, table, parameters):
		results_per_page = 5
		
		page = 1
		filter = ''
		
		for param in parameters.strip().split(' ', 1):
			if param.isdigit():
				page = int(param)
			else:
				filter = '%' + param + '%'
		
		if table == 'users':
			columns = ['id', 'Account Name', 'Auth Level']
			query = """
				SELECT
					id,
					account_name,
					auth_level
				FROM
					users
				WHERE
					server_name IN (:servername, '')
			"""
			if filter:
				query += """
					AND
						account_name LIKE :filter
				"""
			query += """
				ORDER BY
					auth_level DESC,
					account_name ASC
				LIMIT
					:limit1, :limit2
			"""
		
		elif table == 'channels':
			columns = ['id', 'Channel Name', 'Blacklisted', 'Blacklist Reason']
			query = """
				SELECT
					id,
					channel_name,
					blacklisted,
					blacklist_reason
				FROM
					channels
				WHERE
					server_name = :servername
			"""
			if filter:
				query += """
					AND
						channel_name LIKE :filter
				"""
			query += """
				ORDER BY
					channel_name ASC
				LIMIT
					:limit1, :limit2
			"""
		
		elif table == 'response_messages':
			columns = ['id', 'Trigger', 'Trigger Type', 'Message', 'Message Type']
			query = """
				SELECT
					rm.id,
					rm.trigger,
					tt.name,
					rm.message_text,
					rt.name
				FROM
					response_messages AS rm
				INNER JOIN
					trigger_types AS tt
					ON
						tt.id = rm.trigger_type_id
				INNER JOIN
					response_types AS rt
					ON
						rt.id = rm.response_type_id
			"""
			if filter:
				query += """
					WHERE
							rm.trigger LIKE :filter
						OR
							rm.message_text LIKE :filter
				"""
			query += """
				ORDER BY
					rm.trigger ASC,
					rm.message_text ASC,
					rt.code ASC,
					tt.code ASC,
					rm.id ASC
				LIMIT
					:limit1, :limit2
			"""
		
		else:
			columns = ['id', 'Message', 'Message Type']
			query = """
				SELECT
					t.id,
					t.message_text,
					rt.name
				FROM
					%s AS t
				INNER JOIN
					response_types AS rt
					ON
						rt.id = t.response_type_id
			""" % table
			if filter:
				query += """
					WHERE
						message_text LIKE :filter
				"""
			query += """
				ORDER BY
					t.message_text ASC,
					rt.code ASC,
					t.id ASC
				LIMIT
					:limit1, :limit2
			"""
		
		cursor = self.database.cursor()
		try:
			cursor.execute(query, {
				'filter': filter,
				'limit1': (page - 1) * results_per_page,
				'limit2': results_per_page,
				'servername': server_name,
			})
		except BaseException as e:
			logging.error('%s %s, query: %s' % (type(e), e, query))
			return False
		
		results = [row for row in cursor]
		if results:
			connection.privmsg(reply_target, 'Results page %d:' % page)
			connection.privmsg(reply_target, ' | '.join(columns))
			
			for row in results:
				connection.privmsg(reply_target, ' | '.join(str(r) for r in row))
		else:
			connection.privmsg(reply_target, 'Nothing found')
		
		return True
	
	def remove_by_id_or_filter(self, server_name, table, parameter, auth_level = None):
		if not parameter or (table == 'channels' and (not auth_level or auth_level < 50)):
			return False
		
		if parameter.isdigit():
			id = int(parameter)
			filter = ''
		else:
			id = None
			filter = '%' + parameter + '%'
		
		cursor = self.database.cursor()
		
		query = ' FROM %s WHERE ' % table
		
		if id:
			query += 'id = :id'
			
			if table == 'channels':
				query += ' AND server_name = :server'
		
		elif table == 'users':
			query += 'account_name LIKE :filter'
			cursor.execute('SELECT auth_level' + query,
				{
					'id': id,
					'filter': filter,
				}
			)
			results = [row for row in cursor]
			if len(results) != 1 or results[0][0] >= auth_level:
				return False
		
		else:
			if table == 'response_messages':
				query += 'trigger LIKE :filter OR message_text LIKE :filter'
			
			elif table == 'channels':
				query += 'channel_name LIKE :filter AND server_name = :server'
			
			else:
				query += 'message_text LIKE :filter'
			
			cursor.execute('SELECT COUNT(1)' + query,
				{
					'id': id,
					'filter': filter,
					'server': server_name,
				}
			)
			if cursor.fetchone()[0] != 1:
				return False
		
		cursor.execute('DELETE' + query,
			{
				'id': id,
				'filter': filter,
				'server': server_name,
			}
		)
		self.database.commit()
		
		return True
	
	def do_sql(self, connection, reply_target, command):
		cursor = self.database.cursor()
		
		try:
			cursor.execute(command)
		except BaseException as e:
			logging.error('%s %s, query: %s' % (type(e), e, command))
			return False
		
		if cursor.description:
			connection.privmsg(reply_target, ' | '.join(c[0] for c in cursor.description))
			
			for row in cursor:
				connection.privmsg(reply_target, ' | '.join(str(r) for r in row))
		
		self.database.commit()
		return True

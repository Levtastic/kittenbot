import sys
import logging
import datetime
import sqlite3

import os.path
 
from contextlib import closing
from irc.bot import ServerSpec
from responsebot import ResponseBot

db_name = 'kittenbot.db'

def main():
    if len(sys.argv) == 2:
        server_name = sys.argv[1]
        if server_name.lower().replace('-', '') in ('h', 'help'):
            die("Usage: kittenbot.py [<server[:port]>] <server name>")
        
        connection = get_connection_details(server_name)
        if not connection:
            die('Server name "%s" not found in the database' % server_name)
        
        s = connection.split("|", 2)
        server = ServerSpec(s[0], int(s[1]), s[2])
        
    elif len(sys.argv) == 3:
        s = sys.argv[1].split(":", 1)
        if len(s) == 2 and s[1].isdigit():
            port = int(s[1])
        else:
            port = 6667
        
        server = ServerSpec(s[0], port)
        server_name = sys.argv[2]
    else:
        die("Usage: kittenbot.py [<server[:port]>] <server name>")
    
    logging.basicConfig(
        filename = 'logs/%s %s.log' % (server_name, datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')),
        level = logging.INFO,
        format = '[%(asctime)s] %(message)s\n',
        datefmt = '%m/%d/%Y %H:%M:%S'
    )
    ResponseBot(
        nickname = 'KittenBot',
        realname = 'KittenBot (admin contact: Lev)',
        server_name = server_name,
        server = server,
        module_parameters = {
            'database:name': db_name,
        }
    ).start()

def get_connection_details(server_name):
    if not os.path.isfile(db_name):
        raise FileNotFoundError('Cannot connect without a server address before database exists')

    with closing(sqlite3.connect(db_name)) as database:
        with closing(database.cursor()) as cursor:
            cursor.execute("""
                SELECT
                    value
                FROM
                    vars
                WHERE
                    key = ?
                ORDER BY
                    id ASC
                LIMIT
                    1
            """,
                ('server|' + server_name, )
            )
            result = cursor.fetchone()
    
    if result:
        return result[0]
    else:
        raise KeyError('Unable to find server %s in the database' % server_name)

def die(message = ''):
    if message:
        print(message)
    
    sys.exit(1)

if __name__ == '__main__':
    main()

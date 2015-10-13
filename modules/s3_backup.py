import logging

imported = False
try:   
    import boto3.session
    import boto3.s3.transfer
    imported = True
except ImportError:
    logging.warning('Unable to import boto for s3 storage')

def init():
    if imported:
        S3Backup()

class S3Backup():
    auth_commands = {
        'backup': 70,
    }
    command_descriptions = {
        'backup': """
            Backs up the database to Amazon's S3 cloud servers
            Syntax: backup
        """,
    }
    
    def __init__(self):
        event_handler.hook('help:get_command_description', self.get_command_description)
        
        event_handler.hook('commands:get_auth_commands', self.get_auth_commands)
        event_handler.hook('commands:do_auth_command', self.do_auth_command)
    
    def get_command_description(self, bot, command):
        if command in self.command_descriptions:
            return self.command_descriptions[command]
    
    def get_auth_commands(self, bot):
        return self.auth_commands
    
    def do_auth_command(self, bot, connection, event, command, parameters, reply_target, auth_level):
        if command not in self.auth_commands:
            return False # not for us
        
        if command == 'backup':
            creds = bot.db.get('s3_credentials')
            # <access key>|<secret key>|<bucket name>|<uploaded file name>
            akey, skey, bname, uname = creds.split('|')
            
            session = boto3.session.Session(
                aws_access_key_id = akey,
                aws_secret_access_key = skey,
            )
            
            client = session.client('s3')
            transfer = boto3.s3.transfer.S3Transfer(client)
            
            transfer.upload_file(
                bot.module_parameters['database:name'],
                bname,
                uname,
                extra_args = {
                    'StorageClass': 'STANDARD_IA',
                },
            )
            
            bot.send(connection, reply_target, bot.db.get_random('yes'), event)
            return True
        
        return False

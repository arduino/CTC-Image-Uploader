import sqlite3

db_file="maindb.db"

class CTCPhotoDB:
	def __init__(self):
		self.conn=sqlite3.connect(db_file)
		self.cursor=self.conn.cursor()

	def createTables(self):
		cmds=['''
		CREATE TABLE photos(
			ID PRIMARY KEY,
			file_name CHAR(50),
			set_id INT,
			order_in_set INT,
			hosted_url CHAR(255),
			refering_url CHAR(125),
			last_updated DATETIME,
			synced TINYINT
		);
		''',
		'''
		CREATE TABLE sets(
			set_id PRIMARY KEY,
			name CHAR(125)
		);
		''']

		for cmd in cmds:
			self.cursor.execute(cmd)

		self.conn.commit()

if __name__=="__main__":
	query=CTCPhotoDB()
	query.createTables()
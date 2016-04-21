import sqlite3
import os

# insert the database name
filename = "LightroomCatalog.lrcat"
# insert the string to search for
str1 = "764993" # this is the folder for the fencing pictures
#str1 = "683635"  # this is the id_local for Block 02-03 Fencing
#str1 = "block_2-3_fencing"
#str1 = "Block 02-03 Fencing"
# verbose level
ver = 1
count = 0

with sqlite3.connect(filename) as conn:
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()    
    # create a virtual table to store results
    #cursor.execute("CREATE VIRTUAL TABLE result USING fts4(table_name);")

    # get the names of all tables in the database
    if ver == 1:
        print "List of tables: \n"
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    for tablerow in cursor.fetchall():
        table = tablerow[0]
        if ver == 1:
       	    print "searching for: " + str1 + " in " + table
        # check in each row (name of column is the row 0)
        cursor.execute("SELECT * FROM {t}".format(t = table))
        for row in cursor:
            for field in row.keys():
                if ver == 99:
                    print row[field]
                if type(row[field]) is int:
                    str2 = str(row[field])
                elif type(row[field]) is unicode:
                    str2 = (row[field]).encode('utf8')
                else:
                    str2 = str(row[field])
                # print the whole thing (you don't wanna do it)
                #print str2
                # perform a search and store ther results
                if str2.find(str1) > 0:
                   	print str(count) + " " + str1 + ": " + table + "\t" + field + "\t" + row[field]
                  	count = count + 1



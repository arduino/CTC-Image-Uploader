#
#	type codes:
#	y: youtube video
#	g: github code
#
#
import openpyxl
from mainDB import CTCPhotoDB
from CreateShortLinks import getShortURL

videoSheetLocation="data/CSV ctc vid.xlsx"
codeSheetLocation="data/Github bitly sheet.xlsx"

photoDB=CTCPhotoDB()

def getFullType(typeCode):
	return { \
		"y":"Youtube video", \
		"g":"Github code" \
	}[typeCode]

def getSheet(sheetLocation):
	wb = openpyxl.load_workbook(sheetLocation)
	sheet=wb.active
	return sheet

#print sheet.max_row, sheet.max_column

def getOrderInSet(shortCode):
	identifier=shortCode.split("-")[-2:]
	if identifier[0].isdigit():
		return int(identifier[1])-1
	else:
		return 0

def processVideoSheet():
	sheet=getSheet(videoSheetLocation)
	for row in range(1,sheet.max_row):
		name=sheet.cell(row=row,column=1).value
		link=sheet.cell(row=row,column=2).value
		shortCode=sheet.cell(row=row,column=3).value
		if shortCode!=None and link!=None:
			orderInSet=getOrderInSet(shortCode)
			shortCode="ctc-y-"+shortCode
			photoDB.addExtra({"name":name, "short_code":shortCode, "hosted_url":link, "type":"y", "order_in_set":orderInSet})
			print name, shortCode
	photoDB.commit()



def processCodeSheet():
	sheet=getSheet(codeSheetLocation)
	for row in range(4,sheet.max_row):
		name=sheet.cell(row=row,column=1).value
		link=sheet.cell(row=row,column=3).value
		shortCode=sheet.cell(row=row,column=5).value
		if shortCode!=None and link!=None:
			orderInSet=getOrderInSet(shortCode)
			shortCode="ctc-g-"+shortCode
			photoDB.addExtra({"name":name, "short_code":shortCode, "hosted_url":link, "type":"g", "order_in_set":orderInSet})
			print name, shortCode
	photoDB.commit()


def getShortURLForExtras():
	cmd="""
	SELECT * FROM extras
	WHERE state == 0
	"""
	toGet=photoDB.makeQuery(cmd)[0].fetchall()
	
	for one in toGet[0:1]:
		#print one["hosted_url"]
		getShortURL({ \
			"hosted_url":one["hosted_url"], \
			"keyword":one["short_code"], \
			"title":getFullType(one["type"])+" "+one["name"] \
			})
		photoDB.modifyExtraState(one["short_code"],1)
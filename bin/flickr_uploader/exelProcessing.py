import openpyxl
from mainDB import CTCPhotoDB
from CreateShortLinks import getShortURL

videoSheetLocation="data/CSV ctc vid.xlsx"
codeSheetLocation="data/Github bitly sheet.xlsx"

photoDB=CTCPhotoDB()

def getSheet(sheetLocation):
	wb = openpyxl.load_workbook(sheetLocation)
	sheet=wb.active
	return sheet

#print sheet.max_row, sheet.max_column

def processVideoSheet():
	sheet=getSheet(videoSheetLocation)
	auto_id=0
	for row in range(1,sheet.max_row):
		name=sheet["A{}".format(row)].value
		link=sheet["B{}".format(row)].value
		if name!=None and link!=None:
			photoDB.addExtra({"ID":auto_id,"name":name,"hosted_url":link, "type":"y"})
			auto_id=auto_id+1
			#print name, link

	photoDB.commit()

def processCodeSheet():
	sheet=getSheet(codeSheetLocation)
	for row in range(4,sheet.max_row):
		name=sheet["A{}".format(row)].value
		link=sheet["C{}".format(row)].value
		if name!=None and link!=None:
			print name,link
			

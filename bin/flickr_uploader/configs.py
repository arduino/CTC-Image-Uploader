flickr_api_key = u'93b8060c7cc7a47ae11c3644bf47703e'
flickr_api_secret = u'09befa602ac8cf81'

yourls_URL="http://verkstad.cc/urler"
yourls_signature = u'3e2e8e1efb'


#
# extras_def
# These definitions are used for generating shortURLs for extra files. They are used
# by exelProcessing.py
#
# name: a name given to the sheet. Used for generating titles when making shortURL
# book_name: file path of the corresponding Exel file
# sheet_name: If there're multiple sheets in the Exel file, use it to identify the sheet.
# 			  When left empty, it'll use the default sheet.
# type_code: Used for generating the shortURL
# full_type: Used for generating titles when making shortURL
#
# sheet_settings values:
#  [nameCol, linkCol, shortCodeCol, rangeStart]
# 
#  nameCol: column of item names
#  linkCol: column of item original links
#  shortCodeCol: column of item shortCodes
#  rangeStart: first row of data beginning
#
#
extras_def=[
	{
		"name":"Youtube",
		"book_name":"data/CSV ctc vid.xlsx",
		"sheet_name":"",
		"type_code":"y",
		"full_type":"Youtube video",
		"sheet_settings":[1,2,3,1]
	},

	{
		"name":"Github",
		"book_name":"data/Github bitly sheet.xlsx",
		"sheet_name":"",
		"type_code":"g",
		"full_type":"Github code",
		"sheet_settings":[1,3,5,4]
	},

	{
		"name":"Fritzing",
		"book_name":"data/Github bitly sheet.xlsx",
		"sheet_name":"fritzingImages",
		"type_code":"frz",
		"full_type":"Fritzing Image",
		"sheet_settings":[1,2,3,1]
	},

	{
		"name":"Icon",
		"book_name":"data/Github bitly sheet.xlsx",
		"sheet_name":"icons",
		"type_code":"ico",
		"full_type":"Icon",
		"sheet_settings":[1,2,3,1]
	},

	{
		"name":"Downloads",
		"book_name":"data/Github bitly sheet.xlsx",
		"sheet_name":"downloads",
		"type_code":"dld",
		"full_type":"Downloads",
		"sheet_settings":[1,3,4,13]
	},
]
	

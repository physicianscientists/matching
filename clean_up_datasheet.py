
#
# Command to run 
# 	python clean_up_datasheet.py filename.csv
#
#
# Assumptions
# csv file
# Will find duplicates
# Will find email mismatches
# 
# these will be printed as warnings
# deletion of duplicates must be done manually for safety
#

import sys
import csv
from uszipcode import SearchEngine
zipsearch = SearchEngine(simple_zipcode=True)

all_names = set()
all_emails = set()

southeast_states = set(['AL','AR','FL','GA','KY','LA','MS','NC','SC','TN','VA','WV'])
midwest_states = set(['IL','IN','IA','KS','MI','MN','MO','NE','ND','OH','SD','WI'])
northeast_states = set(['CT','DE','ME','MD','MA','NH','NJ','NY','PA','RI','VT','DC'])
mountain_states = set(['CO','ID','MT','NV','UT','WY'])
westcoast_states = set(['AK','CA','HI','OR','WA'])
south_states = set(['AZ','NM','OK','TX'])
def getAPSARegionFromState(state):
	if state in southeast_states:
		return 'Southeast'
	if state in midwest_states:
		return 'Midwest'
	if state in northeast_states:
		return 'Northeast'
	if state in mountain_states:
		return 'Mountain'
	if state in westcoast_states:
		return 'West'
	if state in south_states:
		return 'South'
	print "state err", state
	return 'null'

with open(sys.argv[1], mode='r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:

    	name = row['First Name'].lower().strip()+row['Last Name'].lower().strip()
    	email = row['Email Address'].lower().strip()

    	if name in all_names:
    		print "Possible duplicate: ",row['First Name'],row['Last Name']
    	elif email in all_emails:
    		print "Possible duplicate email: ",row['First Name'],row['Last Name'], email
    	all_names.add(name)
    	all_emails.add(email)

    	if row['Email Address'].lower().strip() != row['Confirm Email Address'].lower().strip():
    		print "Emails don't match" , row['Email Address'] , row['Confirm Email Address']

    	zipcode = zipsearch.by_zipcode(row['School Zip/Postal Code'].lower().strip())
    	try:
    		region = getAPSARegionFromState(zipcode.state_abbr)
	    	if region is 'null':
	    		print "bad zipcode?",row['School Zip/Postal Code'].lower().strip()
    	except Exception as e:
    		print "bad zipcode?",row['School Zip/Postal Code'].lower().strip()
    	




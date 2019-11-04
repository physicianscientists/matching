#from openpyxl import load_workbook
import copy
import sys
import csv
#import zipcode
from uszipcode import SearchEngine
zipsearch = SearchEngine(simple_zipcode=True)

#
# Command to run (assuming files present in same folder) is
# 	python3 apsa_mentor_mentee_matching.py 
#
#
# Assumptions
# 1. No duplicates (prefilter these), clean emails and zip codes...
#    see clean_up_datasheet.py code 
#

# What tags are
TAG_FIRST_NAME ='First Name'
TAG_LAST_NAME ='Last Name'
TAG_EMAIL ='Email Address'
TAG_SCHOOL ='School Currently Attended'
TAG_ZIP ='School Zip/Postal Code'
TAG_INTEREST ='Areas of Interest'
TAG_GENDER ='Gender'
TAG_ETHNICITY ='Ethnicity'
TAG_RACE ='Race'
TAG_PARENT ='Parent\'s Highest Education Level'
TAG_INCOME ='Parent\'s Annual Household Income'
TAG_1GEN ='Are you a first-generation college student in your family?'
TAG_2MENTEE ='How many undergraduate students would you be willing to mentor?'






# convert state to APSA region
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
	return null

def getUSHalfFromRegion(region):
	eastern = set(['Southeast', 'Midwest', 'Northeast'])
	if region in eastern:
		return 'East'
	return 'West'

# the key to a bin by specified categories (ethnicity, region, gender, etc.)
def generate_bin_key(indiv, key_item_list):
	key = ""
	for key_item in key_item_list:
		key += indiv[key_item]
	return key

# select ideal mentor; preference for mentor with no student
def select_mentor(potential_mentors_list, tags_to_avoid, student, allow_dual_mentor):
	# first try to pick a mentor who doesn't already have 1 student
	for mentor in potential_mentors_list:
		if(not mentor['id'].startswith("2_")):
			something_bad_matches = False
			for avoid in tags_to_avoid:
				something_bad_matches = something_bad_matches or mentor[avoid] == student[avoid]
			if not something_bad_matches:
				return mentor
	# pick dual mentor since none available (if allowed)
	if(allow_dual_mentor):
		for mentor in potential_mentors_list:
			return mentor
	return 'none'

# actual matching using mentor/mentee lists, specified categories, and option for using dual mentor
def match_on_key(mentors, mentees, new_key_list, tags_to_avoid, allow_dual_mentor):
	potential_mentors = {}
	
	# find mentors with no students
	for mentor in mentors:
		if(mentor['link']=='none'):
			# create bin using categories
			key = generate_bin_key(mentor, new_key_list)
			if(key not in potential_mentors):
				# start new bin
				potential_mentors[key] = []
			potential_mentors[key].append(mentor)

	# only use unassigned students
	for student in mentees:
		if(student['link']=='none'):
			# get appropriate bin using categories
			key = generate_bin_key(student, new_key_list)
			if(key in potential_mentors):
				# ensure mentors haven't run out for bin
				if(len(potential_mentors[key]) > 0):
					# select ideal mentor
					ideal_mentor = select_mentor(potential_mentors[key],tags_to_avoid,student, allow_dual_mentor)
					if(not ideal_mentor == 'none'):
						# link mentor and mentee
						ideal_mentor['link'] = student
						student['link'] = ideal_mentor
						# remove from bin
						potential_mentors[key].remove(ideal_mentor)

# load data from excel workbook
def parse_worksheet_from_csv(filepath, is_mentor_sheet):
	with open(filepath, mode='r') as csv_file:
		csv_reader = csv.DictReader(csv_file)
		members = list()
		# represent each mentee/mentor as a dict and save in list
		for row in csv_reader:
			for key in row.keys():
				if 'Level' in key:
					TAG_PARENT = key
				elif 'Income' in key:
					TAG_INCOME = key
			new_member = {}
			name = row[TAG_FIRST_NAME]+" "+row[TAG_LAST_NAME]
			new_member['name'] = name
			email = row[TAG_EMAIL].lower().strip()
			new_member['email'] = email
			new_member['id'] = name+"_"+email # id is full name + email
			new_member['first-gen'] = str(row[TAG_1GEN].lower() == "yes")
			new_member['income'] = row[TAG_INCOME].lower()
			#myzip = zipcode.isequal(row[TAG_ZIP].lower().strip())
			new_member['zip'] = row[TAG_ZIP].lower().strip()
			new_member['school'] = row[TAG_SCHOOL].lower().strip()
			zipcode = zipsearch.by_zipcode(new_member['zip'])
			new_member['region'] = getAPSARegionFromState(zipcode.state_abbr)
			new_member['ushalf'] = getUSHalfFromRegion(new_member['region'])
			new_member['state'] = zipcode.state_abbr
			new_member['city'] = zipcode.major_city
			new_member['gender'] = row[TAG_GENDER].lower()
			new_member['link'] = 'none'

			# based on description in doc, these are effectively one category
			if(row[TAG_ETHNICITY].lower().strip().startswith("not")):
				new_member['ethnicity.race'] = row[TAG_RACE].lower().strip()
			else:
				new_member['ethnicity.race'] = row[TAG_ETHNICITY].lower().strip()

			members.append(new_member)

			# handling dual mentors
			if(is_mentor_sheet):
				if(int(row[TAG_2MENTEE].lower().strip()) > 1):
					# effectively the same as having a new mentor; just change id
					dual_mentor = copy.deepcopy(new_member)
					dual_mentor['id'] = "2_"+dual_mentor['id'] # for dual mentors
					members.append(dual_mentor)
	return members

# read data
# build dictionary of mentees and mentors

print "parse mentees"
mentees = parse_worksheet_from_csv(sys.argv[1], False)

print "parse mentors"
mentors = parse_worksheet_from_csv(sys.argv[2], True)


### this section below first ignores the possibility of dual mentors
### runs through all categories while ignoring the dual mentors second position
### this is to minimize number of mentors with no students
### just comment out the next 16 lines if you don't want this rule
dont_match_list = ['school','zip']
new_key_list = ['ethnicity.race','first-gen','income','region','state','city','gender']
match_on_key(mentors, mentees, new_key_list, dont_match_list, False)
new_key_list = ['ethnicity.race','first-gen','income','region','state','city']
match_on_key(mentors, mentees, new_key_list, dont_match_list, False)
new_key_list = ['ethnicity.race','first-gen','income','region','state','gender']
match_on_key(mentors, mentees, new_key_list, dont_match_list, False)
new_key_list = ['ethnicity.race','first-gen','income','region','state']
match_on_key(mentors, mentees, new_key_list, dont_match_list, False)
new_key_list = ['ethnicity.race','first-gen','income','region']
match_on_key(mentors, mentees, new_key_list, dont_match_list, False)
new_key_list = ['ushalf','ethnicity.race','gender']
match_on_key(mentors, mentees, new_key_list, dont_match_list, False)
new_key_list = ['ushalf','ethnicity.race']
match_on_key(mentors, mentees, new_key_list, dont_match_list, False)
new_key_list = ['ethnicity.race']
match_on_key(mentors, mentees, new_key_list, dont_match_list, False)
new_key_list = ['ushalf','gender']
match_on_key(mentors, mentees, new_key_list, dont_match_list, False)
new_key_list = ['gender']
match_on_key(mentors, mentees, new_key_list, dont_match_list, False)
new_key_list = ['city']
match_on_key(mentors, mentees, new_key_list, dont_match_list, False)
new_key_list = ['state']
match_on_key(mentors, mentees, new_key_list, dont_match_list, False)
new_key_list = ['region']
match_on_key(mentors, mentees, new_key_list, dont_match_list, False)	
new_key_list = ['ushalf','first-gen']
match_on_key(mentors, mentees, new_key_list, dont_match_list, False)	
new_key_list = ['ushalf','income']
match_on_key(mentors, mentees, new_key_list, dont_match_list, False)	
new_key_list = ['first-gen']
match_on_key(mentors, mentees, new_key_list, dont_match_list, False)	
new_key_list = ['income']
match_on_key(mentors, mentees, new_key_list, dont_match_list, False)	

### this is the actual algorithm describes; allows the possibility of dual mentors
### runs through all categories with possibility of dual mentors

new_key_list = ['ethnicity.race','first-gen','income','region','state','city','gender']
match_on_key(mentors, mentees, new_key_list, dont_match_list, True)
new_key_list = ['ethnicity.race','first-gen','income','region','state','city']
match_on_key(mentors, mentees, new_key_list, dont_match_list, True)
new_key_list = ['ethnicity.race','first-gen','income','region','state','gender']
match_on_key(mentors, mentees, new_key_list, dont_match_list, True)
new_key_list = ['ethnicity.race','first-gen','income','region','state']
match_on_key(mentors, mentees, new_key_list, dont_match_list, True)
new_key_list = ['ethnicity.race','first-gen','income','region']
match_on_key(mentors, mentees, new_key_list, dont_match_list, True)
new_key_list = ['ushalf','ethnicity.race','gender']
match_on_key(mentors, mentees, new_key_list, dont_match_list, True)
new_key_list = ['ushalf','ethnicity.race']
match_on_key(mentors, mentees, new_key_list, dont_match_list, True)
new_key_list = ['ethnicity.race']
match_on_key(mentors, mentees, new_key_list, dont_match_list, True)
new_key_list = ['ushalf','gender']
match_on_key(mentors, mentees, new_key_list, dont_match_list, True)
new_key_list = ['gender']
match_on_key(mentors, mentees, new_key_list, dont_match_list, True)
new_key_list = ['city']
match_on_key(mentors, mentees, new_key_list, dont_match_list, True)
new_key_list = ['state']
match_on_key(mentors, mentees, new_key_list, dont_match_list, True)
new_key_list = ['region']
match_on_key(mentors, mentees, new_key_list, dont_match_list, True)	
new_key_list = ['ushalf','first-gen']
match_on_key(mentors, mentees, new_key_list, dont_match_list, True)	
new_key_list = ['ushalf','income']
match_on_key(mentors, mentees, new_key_list, dont_match_list, True)	
new_key_list = ['first-gen']
match_on_key(mentors, mentees, new_key_list, dont_match_list, True)	
new_key_list = ['income']
match_on_key(mentors, mentees, new_key_list, dont_match_list, True)	


# some stats

num_student_without_mentor = 0
for student in mentees:
	if(student['link']=='none'):
		num_student_without_mentor += 1

num_mentors_with_no_student = 0
num_mentors_with_2_students = 0
for mentor in mentors:
	if(not mentor['id'].startswith('2_') and mentor['link']=='none'):
		num_mentors_with_no_student += 1
		print("Has no student: "+mentor['id'])
	elif(mentor['id'].startswith('2_') and not mentor['link']=='none'):
		num_mentors_with_2_students += 1

print("Num of mentees is "+str(len(mentees)))
print("Num of potential effective mentors is "+str(len(mentors)))
print("Num of students without mentor is "+str(num_student_without_mentor) )
print("Num of mentors without student is "+str(num_mentors_with_no_student) )
print("Num of dual mentors is "+str(num_mentors_with_2_students) )


output_file = open("student_to_mentor_match_none_left_behind.tsv","w") 
output_file.write("Student name\tEmail\tMentor Name\tEmail\n") 
for student in mentees:
	result_text = student['name'] + "\t" + student['email'] + "\t" + student['link']['name'] + "\t" + student['link']['email'] + "\t" + student['school'] + "\t" + student['link']['school'] + "\n"
	output_file.write(result_text)
output_file.close() 


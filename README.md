# For matching APSA mentors and mentees.

First run the clean up script `python clean_up_datasheet.py filename.csv`

The assumptions are that this is a YM formatted csv file. The script will find and 
print potential duplicates and email mismatches. These will be output as warnings.


The deletion of duplicates must be done manually to avoid accidentally missing a potential
mentor or mentee.

After the csv has been cleaned, run the actuall matching algorithm (notes/details in the notes folder)

`python apsa_mentor_mentee_matching.py`

The code is not optimized, but we only run on a few hundred mentors/mentees, so it'll run quickly.

"""
This is a quick & dirty HTML parser for the sole purpose of parsing the Iowa
caucus results.

CLOWN WARNING:
* I threw this together in a night. Don't tell me it's incomprehensible. I know.

LICENSE: 
* Licensed under GNU GPLv3: https://choosealicense.com/licenses/gpl-3.0/

AUTHOR:
* Twitter: @CharlesPaulTX
"""
from urllib2 import urlopen
from collections import defaultdict
from csv import writer

NONE = -1
HEADER = 0
SUBHEADER = 1
PRECINCT_DATA = 2
RAW_DATA = 3

should_print_all = False
def print_depth(depth, tag):
    if should_print_all:
        print ("\t"*depth)+tag

resp = urlopen("https://results.thecaucuses.org/")
data = resp.read()
depth = -1
is_comment = False
mode = NONE
candidates = []
precincts = []
precinct_index = 0

# Candidate => Key (e.g. "First") => Precinct => # 
out = {}

def set_out():
    """
    Sets the "out" map
    """
    for candidate in candidates:
        out[candidate] = {
            "First": defaultdict(int),
            "Final": defaultdict(int),
            "SDE": defaultdict(int)
        }

# This is the second-most clowny way to parse HTML.
# The clown crown, of course, belongs to parsing HTML with regex. 
for tag in data.split("<")[1:]:
    tag = "<"+tag

    # Deal with comments
    if "<!--" in tag:
        if "-->" not in tag:
            is_comment = True
        continue
    if is_comment:
        if "-->" in tag:
            is_comment = False
        continue


    # Get candidate order from header
    if "<ul" in tag and "class=\"thead\"" in tag:
        mode = HEADER
    if mode == HEADER:
        if "ul>" in tag: # End of header
            set_out()
            mode = NONE
        else:
            val = tag.split(">")[1]
            if val != "" and val != "County" and val != "Precinct":
                candidates.append(val)

    # If it's announcing a group of precincts:
    if "class=\"precinct-data\"" in tag:
        mode = PRECINCT_DATA
    if mode == PRECINCT_DATA:
        if "</div>" in tag:
            mode = NONE
        # Make sure not to 
        if "<ul>" in tag and "total-row" not in tag:
            mode = RAW_DATA
            precinct_index = -1

    if mode == RAW_DATA:
        if "</ul>" in tag:
            mode = PRECINCT_DATA

        if "/>" not in tag and "</" not in tag:
            val = tag.split(">")[1]
            if val != "":
                precinct_index += 1
                if precinct_index == 0:
                    precinct_name = val
                    precincts.append(precinct_name)
                else:
                    # Floor div
                    candidate = candidates[(precinct_index-1) / 3]
                    sub = (precinct_index-1) % 3
                    if sub == 0:
                        key = "First"
                        out[candidate][key][precinct_name] += int(val)
                    elif sub == 1:
                        key = "Final"
                        out[candidate][key][precinct_name] += int(val)

                    elif sub == 2:
                        key = "SDE"
                        out[candidate][key][precinct_name] += float(val)
    # Print pretty
    if "</" in tag:
        depth -= 1
        print_depth(depth, tag)
    elif "/>" in tag:
        print_depth(depth, tag)
    else:
        print_depth(depth, tag)
        depth += 1

# Precinct, ResultType, Candidates...
# 1NW ADAIR, First, Candidates...
# 1NW ADAIR, Final, Candidates...
# 1NW ADAIR, SDE, Candidates...
# ...

out_file = open("iowa.csv", "w")
out_writer = writer(out_file)

title_row = ["Precinct", "ResultType"] + candidates
out_writer.writerow(title_row)

for precinct in precincts:
    for result_type in ["First", "Final", "SDE"]:
        row = [precinct, result_type]
        for candidate in candidates:
            row.append(out[candidate][result_type][precinct])
        out_writer.writerow(row)

def print_by_key(key):
    print "\n"+key+"\n"
    def get_val(candidate):
        return sum(out[candidate][key].values())

    total = sum(map(lambda a: get_val(a), candidates))
    # Multiply by 100 to deal with truncation
    sorter = lambda a, b: int((get_val(b) - get_val(a)) * 100)
    for candidate in sorted(candidates, sorter):
        val = get_val(candidate)
        print candidate+":", val, val/float(total)

print_by_key("First")
print_by_key("Final")
print_by_key("SDE")

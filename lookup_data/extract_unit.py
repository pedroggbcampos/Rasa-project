import re
import yaml

file1 = open('../data/nlu/lookup_unit.yml', 'r')
Lines = file1.readlines()
NewLines = []

for i, line in enumerate(Lines):
    if i > 2:
        line = line + s
        NewLines.append(line)

NewLines = list(set(NewLines))


with open('../data/nlu/lookup_unit.yml', 'a') as outfile:
    outfile.writelines(NewLines)

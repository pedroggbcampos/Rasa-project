import re
import yaml

file1 = open('grocery_item_data.txt', 'r')
Lines = file1.readlines()
Items = []

for line in Lines:
    line = re.sub('".*?"', '', line) #remove anything inside quotes
    line = line.split(",")
    if line[2] != "":
        Items.append(line[2])

Items = list(set(Items))

lookup = {'nlu:': Items}

with open('../data/nlu/lookup_grocery_item.yml', 'w') as outfile:
    yaml.dump(lookup, outfile)

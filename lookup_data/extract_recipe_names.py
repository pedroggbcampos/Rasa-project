# some of the code inte this file is copied from: https://deepnote.com/publish/2cc2d19c-c3ac-4321-8853-0bcf2ef565b3

import re
import yaml
import pandas as pd

#import foods in dataframe
food_df = pd.read_csv("food.csv")

# disqualify foods with special chars, lowercase and extract results from "description" column
foods = food_df[food_df["description"].str.contains("[^a-zA-Z ]") == False]["description"].apply(lambda food: food.lower())

# filter out foods with more than 3 words, drop any duplicates
foods = foods[foods.str.split().apply(len) <= 3].drop_duplicates()

FoodList = foods.tolist()

lookup = {'nlu:': FoodList}

with open('../data/nlu/lookup_requested_recipe.yml', 'w') as outfile:
    yaml.dump(lookup, outfile)

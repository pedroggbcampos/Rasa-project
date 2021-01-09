# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
import requests

# Dummy grocery list
GROCERY_ITEM_DB = ["milk", "butter", "coffee"]
RECIPE_DB = ["lasagna"]
UNIT_DB = ["liter","liters", "package", "packages", "gram","grams", "kilogram","kilograms"]

class ValidateGroceryForm(FormValidationAction):
    """
    Action used in Forms in order to validate the slots.
    - If the grocery item not in the inventory we reset that slot and ask the user again.
    - If the amount is a negative value we ask the user for another amount.
    """

    def name(self) -> Text:
        return "validate_grocery_form"

    @staticmethod
    def grocery_item_db() -> List[Text]:
        """Database of dummie groceries"""
        return GROCERY_ITEM_DB

    @staticmethod
    def unit_db() -> List[Text]:
        """Database of dummie units"""
        return UNIT_DB

    def validate_grocery_item(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print(slot_value)
        return {"grocery_item": slot_value}
        # if slot_value.lower() in self.grocery_item_db():
        #     return {"grocery_item": slot_value}
        # else:
        #     dispatcher.utter_message(
        #         template="utter_not_valid_grocery_item", requested_grocery=slot_value
        #     )
        #     return {"grocery_item": None}

    def validate_amount(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print(slot_value)
        if int(slot_value) > 0:
            return {"amount": slot_value}
        else:
            dispatcher.utter_message(
                template="utter_not_valid_amount", requested_amount=slot_value
            )
            return {"amount": None}

    def validate_unit(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print(slot_value)
        if slot_value.lower() in self.unit_db():
            return {"unit": slot_value}
        else:
            dispatcher.utter_message(
                template="utter_not_valid_unit", requested_unit=slot_value
            )
            return {"unit": None}

class ValidateRecipeForm(FormValidationAction):
    """
    Action used in Forms in order to validate the slots.
    - If the recipe does not exist we reset that slot and ask the user again.
    - If it exists it is validated
    """

    def name(self) -> Text:
        return "validate_recipe_form"

    @staticmethod
    def recipe_db() -> List[Text]:
        """Database of dummie recipes"""
        return RECIPE_DB

    def validate_requested_recipe(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print(slot_value)
        url = "https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/search"

        querystring = {"query":slot_value,"number":"10","type":"main course"}

        headers = {
            'x-rapidapi-key': "b792f6ab4fmshfdfe21f7bc6866dp145eedjsnb54fbbf7d1bc",
            'x-rapidapi-host': "spoonacular-recipe-food-nutrition-v1.p.rapidapi.com"
            }

        response = requests.request("GET", url, headers=headers, params=querystring)

        print(response.text)
        print("\n\n")

        response_dic = response.json()

        print(response_dic["totalResults"])

        n_results = response_dic["totalResults"]
        if n_results > 0:
            name=response_dic["results"][0]["title"]
            id=response_dic["results"][0]["id"]
            dispatcher.utter_message(
                template="utter_recipe_available", requested_recipe=name
            )
            return {"requested_recipe": name, "recipe_amount": n_results,"id_recipe": id}
        else:
            dispatcher.utter_message(
                template="utter_recipe_not_available", recipe=slot_value
            )
            return {"requested_recipe": None, "recipe_amount": 0,"id_recipe": None}

class AddItemsToGroceryList(Action):
    """
    Action that adds slot values grocery_item, amount and unit to grocery list
    """

    def name(self) -> Text:
        return "action_grocery_item_added"

    async def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        grocery_item = tracker.get_slot("grocery_item")
        print("this is the grocery item {}".format(grocery_item))
        amount = tracker.get_slot("amount")
        unit = tracker.get_slot("unit")
        print("this is the grocery unit {}".format(unit))
        grocery_list = tracker.get_slot("grocery_list")
        if grocery_list is None:
            grocery_list = []

        if grocery_item is not None and amount is not None and unit is not None:
            grocery_list.append({"grocery_item": grocery_item, "amount": amount, "unit": unit})

        if len(grocery_list) > 0:
            dispatcher.utter_message(
                template="utter_grocery_item_added", grocery_item=grocery_item, amount=amount, unit=unit
            )
        return [
            SlotSet("grocery_list", grocery_list),
            SlotSet("grocery_item", None),
            SlotSet("amount", None),
            SlotSet("unit", None)
        ]


class TellGroceryList(Action):
    def name(self) -> Text:
        return "action_tell_grocery_list"

    async def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        grocery_list = tracker.get_slot("grocery_list")

        if grocery_list is None or len(grocery_list) == 0:
            dispatcher.utter_message(text="Your grocery list is currently empty")
            return []

        # condensed_grosery_list = {}
        # for item in grocery_list:
        #     grocery_item = item["grocery_item"]
        #     if grocery_item in condensed_grocery_list:
        #         condensed_grocery_list[grocery_item] += item["amount"]
        #     else:
        #         condensed_grocery_list[grocery_item] = item["amount"]
        #     condensed_grocery_list[grocery_item]

        text = "The items in your grocery list are:\n"
        for item in grocery_list:
            text += str(item["amount"]) + " " + str(item["unit"]) + " of " + str(item["grocery_item"]) + "\n"
        # text += "Have a nice day!"
        dispatcher.utter_message(text=text)
        return []



class give_ingredient(Action):
    def name(self) -> Text:
        return "action_give_ingredients"

    async def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        id = tracker.get_slot("id_recipe")
        url_food = "https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/{}/information".format(id)
        headers = {
            'x-rapidapi-key': "b792f6ab4fmshfdfe21f7bc6866dp145eedjsnb54fbbf7d1bc",
            'x-rapidapi-host': "spoonacular-recipe-food-nutrition-v1.p.rapidapi.com"
            }
        response = requests.request("GET", url_food, headers=headers)
        response_recette = response.json()
        text=""
        for ingredient in response_recette["extendedIngredients"]:
            if ingredient["unit"]=="":
                text+=str(ingredient['amount'])+" "+str(ingredient["name"])+"\n"
            else:
                text+=str(round(ingredient['amount'],1))+" "+str(ingredient["unit"])+" of "+str(ingredient["name"])+"\n"

            #text+=str(ingredient["original"])+ "\n"
        # condensed_grosery_list = {}
        # for item in grocery_list:
        #     grocery_item = item["grocery_item"]
        #     if grocery_item in condensed_grocery_list:
        #         condensed_grocery_list[grocery_item] += item["amount"]
        #     else:
        #         condensed_grocery_list[grocery_item] = item["amount"]
        #     condensed_grocery_list[grocery_item]

        dispatcher.utter_message(text=text)
        return []

class give_instructions(Action):
    def name(self) -> Text:
        return "action_give_instructions"

    async def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        id = tracker.get_slot("id_recipe")
        url_food = "https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/{}/information".format(id)
        headers = {
            'x-rapidapi-key': "b792f6ab4fmshfdfe21f7bc6866dp145eedjsnb54fbbf7d1bc",
            'x-rapidapi-host': "spoonacular-recipe-food-nutrition-v1.p.rapidapi.com"
            }
        response = requests.request("GET", url_food, headers=headers)
        response_recette = response.json()
        text="Here is the instruction to follow : \n {}".format(response_recette["instructions"])

            #text+=str(ingredient["original"])+ "\n"
        # condensed_grosery_list = {}
        # for item in grocery_list:
        #     grocery_item = item["grocery_item"]
        #     if grocery_item in condensed_grocery_list:
        #         condensed_grocery_list[grocery_item] += item["amount"]
        #     else:
        #         condensed_grocery_list[grocery_item] = item["amount"]
        #     condensed_grocery_list[grocery_item]

        dispatcher.utter_message(text=text)
        return []


class food_joke(Action):
    def name(self) -> Text:
        return "action_food_joke"

    async def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        url_joke = "https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/food/jokes/random"
        headers = {
            'x-rapidapi-key': "b792f6ab4fmshfdfe21f7bc6866dp145eedjsnb54fbbf7d1bc",
            'x-rapidapi-host': "spoonacular-recipe-food-nutrition-v1.p.rapidapi.com"
            }
        response = requests.request("GET", url_joke, headers=headers)
        joke=response.json()

        dispatcher.utter_message(text=joke["text"])
        return []

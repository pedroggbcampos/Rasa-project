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
UNIT_DB = ["litre", "package", "gram", "kilogram"]

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
        """Database of dummie groceries"""
        return UNIT_DB

    def validate_grocery_item(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print(slot_value)
        if slot_value.lower() in self.grocery_item_db():
            return {"grocery_item": slot_value}
        else:
            dispatcher.utter_message(
                template="utter_not_valid_grocery_item", requested_grocery=slot_value
            )
            return {"grocery_item": None}

    def validate_amount(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print(slot_value)
        if slot_value > 0:
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
            dispatcher.utter_message(
                template="utter_recipe_available", recipe_amount=n_results, recipe=slot_value
            )
            return {"recipe": slot_value, "requested_recipe": None, "recipe_amount": n_results}
        else:
            dispatcher.utter_message(
                template="utter_recipe_not_available", recipe=slot_value
            )
            return {"recipe": None, "requested_recipe": None, "recipe_amount": 0}

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
        amount = tracker.get_slot("amount")
        unit = tracker.get_slot("unit")
        grocery_list = tracker.get_slot("grocery_list")
        if grocery_list is None:
            grocery_list = []

        if grocery_item is not None and amount is not None and unit is not None:
            grocery_list.append({"grocery_item": grocery_item, "amount": amount, "unit": unit})

        if len(cart) > 0:
            dispatcher.utter_message(
                template="utter_grocery_item_added", grocery_item=grocery_item, amount=amount, unit=unit
            )
        return [
            SlotSet("grocery_list", grocery_list),
            SlotSet("fruit", None),
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

        if grocery_list is None or len(cart) == 0:
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
            text += item["amount"] + " " + item["unit"] + " " + item["grocery_item"] + "\n"
            text += " and "
        #remove last and
        text = text[:-5]
        # text += "Have a nice day!"
        dispatcher.utter_message(text=text)
        return []
'''
class CheckRecipeAvailability(Action):
    def name(self) -> Text:
        return "check_recipe_availability"

    async def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        food = next(tracker.get_latest_entity_values("recipe"), None)
        print(food)
        print(slot_value)
        # Check if recipe exists (IN PROGRESS)

        # rec = getRecipe()
        # if rec:
            # recipe = rec
            # recipe_amount = getRecipeAmount()
        # else if rec == null
            # recipe = None
            # recipe_amount = getRecipeAmount()
        # for now...
        recipe_amount = 1

        return [
            SlotSet("recipe_amount", recipe_amount),
            SlotSet("recipe", food)
        ]
'''
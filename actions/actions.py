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
import smtplib, ssl

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
        url = "https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/search"
        print(slot_value)
        querystring = {"query":slot_value,"number":"3","type":"main course"}

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
                template="utter_number_recipe_available", number_recipe=len(response_dic["results"])
            )
            return {"requested_recipe": slot_value,"recipe_amount":len(response_dic["results"])}
        else:
            dispatcher.utter_message(
                template="utter_recipe_not_available", recipe=slot_value
            )
            return {"requested_recipe": None, "recipe_amount": 0}

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
        number = tracker.get_slot("number")
        unit = tracker.get_slot("unit")
        print("this is the grocery unit {}".format(unit))
        grocery_list = tracker.get_slot("grocery_list")
        if grocery_list is None:
            grocery_list = []

        if type(grocery_item) == list:
            concatItems = ""
            for item in grocery_item:
                if item not in concatItems:
                    concatItems += item + " "

            grocery_item = concatItems

        if grocery_item is not None and number is not None and unit is not None:
            grocery_list.append({"grocery_item": grocery_item, "amount": number, "unit": unit})

        if len(grocery_list) > 0:
            dispatcher.utter_message(
                template="utter_grocery_item_added", grocery_item=grocery_item, number=number, unit=unit
            )
        return [
            SlotSet("grocery_list", grocery_list),
            SlotSet("grocery_item", None),
            SlotSet("number", None),
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
        print("here is the id".format(id))
        url_food = "https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/{}/information".format(id)
        headers = {
            'x-rapidapi-key': "b792f6ab4fmshfdfe21f7bc6866dp145eedjsnb54fbbf7d1bc",
            'x-rapidapi-host': "spoonacular-recipe-food-nutrition-v1.p.rapidapi.com"
            }
        response = requests.request("GET", url_food, headers=headers)
        response_recette = response.json()
        print(response_recette)
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
        return [SlotSet("grocery_list_from_request",[response_recette["extendedIngredients"]])]

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
        print("id result {}".format(id))
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


class choose_recipe(Action):
    def name(self) -> Text:
        return "action_choose_recipe"

    async def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        url = "https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/search"
        slot_value=tracker.get_slot("requested_recipe")
        querystring = {"query":slot_value,"number":"3","type":"main course"}

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
        buttons = []
        list_id=[]

        if n_results > 0:
            for i in range(len(response_dic["results"])):
                name=response_dic["results"][i]["title"]
                print(name)
                id=response_dic["results"][i]["id"]
                list_id.append(id)
                payload="/inform{\"id_recipe\":\""+str(id)+"\"}"
                print(payload)
                buttons.append({"title": name, "payload": payload})
            dispatcher.utter_message(text="Choose between these choice (Choose the name of the recipe)",buttons=buttons)

            print("recipe result {}".format(tracker.get_slot("id_recipe")))
        return []


class AddItemsToGroceryListFromRequest(Action):
    """
    Action that adds slot values grocery_item, amount and unit to grocery list
    """

    def name(self) -> Text:
        return "action_add_on_grocery_list"

    async def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        grocery_list=tracker.get_slot("grocery_list")
        grocery_list_from_request=tracker.get_slot("grocery_list_from_request")
        grocery_list_from_request_json=grocery_list_from_request[0]
        if grocery_list is None:
            grocery_list = []
        for ingredient in grocery_list_from_request_json:
            grocery_item=ingredient["name"]
            unit=ingredient["unit"]
            amount=round(ingredient['amount'],1)
            if grocery_item is not None and amount is not None and unit is not None:
                grocery_list.append({"grocery_item": grocery_item, "amount": amount, "unit": unit})
            if len(grocery_list) > 0: # a changer
                dispatcher.utter_message(
                    template="utter_grocery_item_added", grocery_item=grocery_item
                )

        return [
            SlotSet("grocery_list", grocery_list),
            SlotSet("grocery_item", None),
            SlotSet("number", None),
            SlotSet("unit", None)
        ]

class SendGroceryListMail(Action):
    """
    Action that adds slot values grocery_item, amount and unit to grocery list
    """

    def name(self) -> Text:
        return "action_send_grocerylist"

    async def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        grocery_list=tracker.get_slot("grocery_list")
        email=tracker.get_slot("email")
        port = 465  # For SSL
        smtp_server = "smtp.gmail.com"
        sender_email = "meal.planner.infos@gmail.com"  # Enter your address
        receiver_email = email  # Enter receiver address
        password = "mealplanner123"
        SUBJECT= " Grocery list"
        text = "The items in your grocery list are:\n"
        for item in grocery_list:
            text += str(item["amount"]) + " " + str(item["unit"]) + " of " + str(item["grocery_item"]) + "\n"

        message = 'Subject: {}\n\n{}'.format(SUBJECT, text)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)
        dispatcher.utter_message("I send your grocery list to the mail "+receiver_email)
        return []

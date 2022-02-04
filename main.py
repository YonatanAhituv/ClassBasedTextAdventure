from random import randint
from time import sleep
from sys import stdout
import copy  # Ok I really need to chill at this point huh
# import playsound

# Basic Definitions
class Helper():
    def __init__(self, interact=None):
        self.interact = interact
        pass

    # def playSound(self, name):
    #     playsound.playsound(name, False)

    def lowerList(self, inputList):
        outputList = []
        for item in inputList:
            outputList.append(item.lower())
        return outputList

    def lowerToNormal(self, inputList, inputString):
        index = Helper().lowerList(inputList).index(inputString.lower())  # Get index of connected room in keys
        entry = list(inputList)[index]  # Get normal case version
        return entry

    def listInput(self, inputs, prompt):
        i = 1
        for option in inputs:
            self.slowPrint(str(i) + ". " + option)
            i += 1
        while True:
            userInput = input(prompt)
            if userInput.isdigit():
                userInput = int(userInput)
                if userInput in range(1, i + 1):
                    userInput = inputs[userInput - 1]  # Set to corresponding key
            if userInput.lower() in self.lowerList(inputs):
                userInput = self.lowerToNormal(inputs, userInput)
                break
        return userInput

    def formatString(self, inputStr, names):
        # names = {
        # "value": val }
        # inputStr = ${value}
        for word in names:
            inputStr = inputStr.replace("${" + word + "}", names[word])
        return inputStr

    def slowPrint(self, inputStr):
        for char in inputStr:
            stdout.write(char)
            stdout.flush()
            sleep(0.025)
        print()


class Player():
    def __init__(self, room, stats, inventory=[]):
        self.room = room
        self.stats = stats
        self.inventory = inventory

    def pickup(self, interact):
        invInteract = copy.deepcopy(interact.grab())  # No python I do not want the refrence to the object from the room how many times do I have to tell you why is this so complicated I'm literally returning it in a function why should I even need to do this
        invInteract.visible = True  # Slight hack to keep it still visible
        self.inventory.append(invInteract)

class Room():
    def __init__(self, welcomeMessage, interacts, connectedRooms):
        self.interacts = interacts
        self.welcomeMessage = welcomeMessage
        self.connectedRooms = connectedRooms

    def welcome(self):
        Helper().slowPrint(self.welcomeMessage)

class Interactable():
    def __init__(self, name, fanfare="", actions={}, data={}, preface="", obtainable=True, visible=True):
        self.name = name
        self.fanfare = fanfare
        self.obtainable = obtainable
        self.visible = visible
        self.actions = actions
        self.data = data
        self.preface = preface

    def grab(self):
        if self.obtainable:
            Helper().slowPrint(self.fanfare)
            self.visible = False
            return self


class Purchase():
    def __init__(self, name, price, item):
        self.name = name
        self.price = price
        self.item = item

    def purchase(self, speaker, player, room):  # NPC-related function
        speaker = speaker.name
        for item in player.inventory:  # Ensure item hasn't already been bought
            if item.name == self.item.name:
                Helper().slowPrint("You already have this item!")
                return
        Helper().slowPrint(speaker + " would like to sell you " + self.name + " for $" + str(self.price))
        Helper().slowPrint("You have: $" + str(player.stats["money"]))
        userInput = Helper().listInput(["Purchase", "Reject Offer"], "What would you like to do: >>> ")
        if userInput == "Purchase":
            if player.stats["money"] < self.price:
                Helper().slowPrint("The item is too expensive!")
                return
            player.stats["money"] -= self.price
            Helper().slowPrint("You new balance: $" + str(player.stats["money"]))
            for interact in room.interacts:  # Remove interact from the room if it already exists
                if interact.name == self.name:
                    interact.visible = False
            player.pickup(self.item)
        else:
            Helper().slowPrint("Offer Rejected!")
        return


class InteractModification():
    def __init__(self, interact, value):
        self.interact = interact
        self.value = value
        pass

    def setInteractVisibility(self, speaker, player, room):
        speaker = speaker.name
        interactList = room.interacts
        for i, interact in enumerate(interactList):
            if interact.name == self.interact:
                interactList[i].visible = self.value

class Dialogue():
    def __init__(self, prompt, options, prologue="", epilogue="", speaker=True):
        self.prompt = prompt
        self.options = options
        self.prologue = prologue
        self.epilogue = epilogue
        self.speaker = speaker

    def speak(self, speaker, player, room):
        while True:
            if self.prologue != "":
                Helper().slowPrint(self.prologue)
            if self.speaker:
                Helper().slowPrint(speaker.name + ": " + self.prompt)
            else:
                Helper().slowPrint(self.prompt)
            if self.epilogue != "":
                print(self.epilogue)
            option = self.options[Helper().listInput(list(self.options.keys()), "You: ")]
            print()
            if option is False or option is True:  # Close if False
                return option
            else:
                returnValue = option(speaker, player, room)  # Call nested function
                if returnValue is not True:
                    break


class BasicInteractable(Interactable):
    def performAction(self, action, player, room):
        if action in self.data.keys():
            Helper().slowPrint(self.data[action])


class AdvancedInteractable(Interactable):
    def performAction(self, action, player, room):
        if action in self.actions.keys():
            selectedAction = self.data[action]
            calls = [selectedAction["call1"], selectedAction["call2"]]
            for i, call in enumerate(calls):
                if call == "${player}":
                    calls[i] = player
            if calls[1] is None:
                selectedAction["function"](calls[0])
            else:
                selectedAction["function"](calls[0], calls[1])

class PurchasableInteractable(Interactable):
    def __init__(self, name, data={}, obtainable=False, preface="", visible=True):
        self.name = name
        self.actions = {
            "pickup": ["grab", "look at", "admire", "check", "pick up", "try on", "try"],
            "buy": ["buy", "purchase", "collect"]
        }
        self.data = data
        self.obtainable = obtainable
        self.preface = preface
        self.visible = visible

    def performAction(self, action, player, room):
        if action == "pickup":
            Helper().slowPrint(self.data["pickup"])
        elif action == "buy":
            Purchase(self.name, self.data["price"], self.data["item"]).purchase(self.data["speaker"], player, room)


class NPC():  # Still an interactable but so specific it has no need to inherit from the Interactable class
    def __init__(self, name, data={}, preface="A ", obtainable=False, visible=True, fightName=None):
        self.name = name
        if fightName is None:
            fightName = name
        self.fightName = fightName
        self.actions = {
            'talk': ['talk', 'talk to', 'speak to'],
            'fight': ['fight', 'attack', 'hit']
        }
        self.data = data
        self.obtainable = obtainable
        self.visible = visible
        self.preface = preface

    def calculateAttack(self, attack, power, enemyName, hp, message):
        attackDamage = attack["damage"] + randint(-attack["random"], attack["random"])
        attackDamage = round(attackDamage * (power / 10))
        Helper().slowPrint(Helper().formatString(attack["message"], {"enemyName": enemyName, "attackDamage": str(attackDamage)}))
        newHP = hp - attackDamage
        if newHP < 0: 
            newHP = 0 
        Helper().slowPrint(message + " " + str(newHP))
        return newHP


    def fight(self, playerStats, enemyStats):
        while True:
            Helper().slowPrint("\nYou've entered a fight with: " + self.fightName + "!")
            Helper().slowPrint("Their Health: " + str(enemyStats["hp"]))
            Helper().slowPrint("Your HP: " + str(playerStats["hp"]) + " | " + "Your Power: " + str(playerStats["power"]))
            attack = Helper().listInput(list(playerStats["attacks"].keys()), "You can: ")
            attack = playerStats["attacks"][attack]
            # damage: 10, random: 4, message: "stuff ${enemyname} ${hp}"
            enemyStats["hp"] = self.calculateAttack(attack, playerStats["power"], self.fightName, enemyStats["hp"], self.fightName + " health: ")
            if enemyStats["hp"] <= 0:
                Helper().slowPrint("You win!\n")
                self.visible = False
                return

            attacks = list(enemyStats["attacks"].keys())
            attack = attacks[randint(0, len(attacks) - 1)]  # Pick random attack
            attack = enemyStats["attacks"][attack]
            playerStats["hp"] = self.calculateAttack(attack, 10, self.fightName, playerStats["hp"], "Your health: ")
            if playerStats["hp"] <= 0:
                Helper().slowPrint("You died!")
                return

    def fightViaDialogue(self, speaker, player, room):
        self.fight(player.stats, self.data["stats"])

    def performAction(self, action, player, room):
        if action == "talk":
            self.data["dialogue"](self, player, room)
        elif action == "fight":
            self.fight(player.stats, self.data["stats"])


# Data
rooms = {
    "start": Room(
        "You see a mall looming in front of you. Your car is parked outside.",
        [
            NPC(
                "Mall Greeter",
                {
                    "dialogue": Dialogue(
                        "Welcome to the mall!",
                        {
                            '"Thanks! What stores do you have here?"': Dialogue(
                                "A Lot! By the way, would you like to buy my dog?",
                                {
                                    '"Yes"': Purchase(
                                        "his dog",
                                        10,
                                        BasicInteractable(
                                            "Some guys dog",
                                            "Uhm, ok I guess you got this dog now",
                                            {"pet": ["pet", "talk to", "check on"]},
                                            {"pet": "You pet the dog, it seems happy."},
                                        ),
                                    ).purchase,
                                    '"No"': False,
                                },
                            ).speak,  # Nested Classes (:
                            '"Cool! When was this mall built?"': Dialogue(
                                "1962, by George, no last name.", {"Leave": False}
                            ).speak,
                            '"No thanks, I didn\'t want to know"': False,
                        },
                    ).speak,
                    "stats": {
                        "hp": 50,
                        "attacks": {
                            "punch": {
                                "damage": 5,
                                "random": 2,
                                "message": "${enemyName} goes in for a punch! They hit you for ${attackDamage} HP!",
                            }
                        },
                    },
                },
            ),
            BasicInteractable(
                "Your Car",
                "You muster up the strength and put the car in your backpack. Somehow, no one bothered to make the car unobtainable.",
                {"start": ["drive", "start", "take", "use"]},
                {
                    "start": "You place the keys into the ignition, and try to start the car, but the engine doesn't start. You start to regret not buying a car with a start engine button, which are naturally immune to such problems. You leave the car and go back to the mall entrance, pushed by some sort of narrative force."
                },
            ),
        ],
        {"Enter the Mall": "mall"},
    ),
    "mall": Room(
        "It’s May of 2005, and you’ve decided to go to the mall, welcome! Where would you like to go?",
        [],
        {
            "Enter Gucci Store": "gucci",
            "Enter Bathing Ape Store": "bathingApe",
            "Go to Food Court": "foodCourt",
            "Exit": "start",
        },
    ),
    "gucci": Room(
        "You enter the gucci store, everything has a beautiful gold tint.",
        [
            BasicInteractable(
                "Gucci Tissue",
                "No thanks",
                {
                    "pickup": ["grab", "look at", "admire", "check", "pick up"],
                    "buy": ["buy", "purchase", "collect"],
                },
                {
                    "pickup": "You pick up the Gucci Tissue and admire it. However, you are rudely interrupted by bad looks from the staff.",
                    "buy": "You go to look at the price tag of the Gucci Tissue, but are physically thrown back by what you see.",
                },
                obtainable=False,
            ),
            NPC(
                "Valued Customer",
                {
                    "dialogue": Dialogue(
                        "Thank you, I appreciate that, here I'll buy you something from this store, anything you want.",
                        {
                            "\"Oh no it's quite alright you don't have to do that\"": False,
                            '"I\'d like this gucci tissue please"': Purchase(
                                "Gucci Tissue",
                                0,
                                BasicInteractable(
                                    "Gucci Tissue",
                                    "You bought the Gucci Tissues!",
                                    {"use": ["use", "grab a"]},
                                    {
                                        "use": "You grab a tissue from your Gucci Tissue box, being too scared to use it however, you place it right back in."
                                    },
                                ),
                            ).purchase,
                        },
                        prologue='Whoaa!! The valued customer turns out to be none other than 50 Cent!!\n"I\'m a Huge fan Mr. 50 cent sir!!"',
                    ).speak,
                    "stats": {
                        "hp": 1000,
                        "attacks": {
                            "glance": {
                                "damage": 1000,
                                "random": 5,
                                "message": "50 Cent glances angrily at you! He hits you for ${attackDamage} HP!",
                            }
                        },
                    },
                },
                visible=False,
                fightName="50 Cent",
            ),
            NPC(
                "Store Clerk",
                {
                    "dialogue": Dialogue(
                        "Hi, what can I help you with today?",
                        {
                            '"Who is that over there?"': Dialogue(
                                "That's one of our most valued customers!",
                                {
                                    "Leave": InteractModification(
                                        "Valued Customer", True
                                    ).setInteractVisibility
                                },
                            ).speak,
                            '"Nothing"': False,
                        },
                    ).speak,
                    "stats": {
                        "hp": 30,
                        "attacks": {
                            "gucciBelt": {
                                "damage": 15,
                                "random": 5,
                                "message": "${enemyName} grabs his gucci belt and attacks you with it! They hit you for ${attackDamage} HP!",
                            }
                        },
                    },
                },
            ),
        ],
        {"Exit": "mall"},
    ),
    "bathingApe": Room(
        "You enter the bathing ape store, music is blaring on the overhead speakers, and you're sourrounded by bright colors.",
        [
            PurchasableInteractable(
                "Brightly Colored Shoes",
                {
                    "pickup": "You pick up the brighly colored shoes and check them out. They look nice!",
                    "price": 300,
                    "speaker": "Bathing Ape Store",
                    "item": BasicInteractable(
                        "Bathing Ape Shoes",
                        "You bought the Bathing Ape Shoes!",
                        {"use": ["use", "put on", "try on"]},
                        {
                            "use": "You put on the Bathing Ape Shoes. The colors are beautiful and it glistens in the light!"
                        },
                    ),
                },
            ),
            PurchasableInteractable(
                "Brightly Colored Shirt",
                {
                    "pickup": "You pick up the brighly colored shirt and check it out. The bathing ape logo is clearly visible, sourrounded by beautiful colors.",
                    "price": 100,
                    "speaker": "Bathing Ape Store",
                    "item": BasicInteractable(
                        "Bathing Ape Shirt",
                        "You bought the Bathing Ape Shirt!",
                        {"use": ["use", "put on", "try on"]},
                        {
                            "use": "You put on the Bathing Ape Shirt. The colors are almost overwhelming, and the bathing ape logo stands proud in the center."
                        },
                    ),
                },
            ),
            PurchasableInteractable(
                "Brightly Colored Sweatshirt",
                {
                    "pickup": "You pick up the brighly colored sweatshirt and check it out. It's patterned blue, and the hoodie is shaped like a shark. It's a shark hoodie, as one might say.",
                    "price": 200,
                    "speaker": "Bathing Ape Store",
                    "item": BasicInteractable(
                        "Bathing Ape Sweatshirt",
                        "You bought the Bathing Ape Sweatshirt!",
                        {"use": ["use", "put on", "try on"]},
                        {
                            "use": "You put on the Bathing Ape Sweatshirt and zip up the hoodie. You are a shark."
                        },
                    ),
                },
            ),
            NPC(
                "Person Shopping",
                {
                    "dialogue": Dialogue(
                        "Ay man, i appreciate that mane, Ima buy you whateva u want in this store bruh",
                        {
                            '"No, that’s quite alright, I really appreciate it though"': False,
                            '"Thank you so much, can I please get this blue sweatshirt?"': Purchase(
                                "Bathing Ape Sweatshirt",
                                0,
                                BasicInteractable(
                                    "Bathing Ape Sweatshirt",
                                    'You: "Thank you so much, Soulja Boy!"\nSOULJA BOY: "Ya ofc buddy boy, I’m the first rapper to ever give back to my fans"',
                                    {"use": ["use", "put on", "try on"]},
                                    {
                                        "use": "You put on the Bathing Ape Sweatshirt and zip up the hoodie. You are a shark."
                                    },
                                ),
                            ).purchase,
                        },
                        prologue='As you approach the shopper, sourrounded by a group of people, music starts playing through the store’s speakers. It turns out to be SOULJA BOY!!\n"Oh my goodness I’m such a big fan Soulja Boy!"',
                    ).speak,
                    "stats": {
                        "hp": 100,
                        "attacks": {
                            "glance": {
                                "damage": 100,
                                "random": 30,
                                "message": "Souja Boy turns up his music! He hits you for ${attackDamage} HP!",
                            }
                        },
                    },
                },
                visible=False,
                preface="The ",
                fightName="Soulja Boy",
            ),
            NPC(
                "Store Clerk",
                {
                    "dialogue": Dialogue(
                        "Hey What’s up do you need help? Are you looking for anything in particular?",
                        {
                            '"What’s that commotion over there?"': Dialogue(
                                "That’s just some guy shopping",
                                {
                                    "Leave": InteractModification(
                                        "Person Shopping", True
                                    ).setInteractVisibility
                                },
                            ).speak,
                            '"No, not really anything specifically I’m just looking around"': False,
                        },
                    ).speak,
                    "stats": {
                        "hp": 40,
                        "attacks": {
                            "theApe": {
                                "damage": 70,
                                "random": 20,
                                "message": "${enemyName} grabs THE bathing ape and it goes in for the attack! They hit you for ${attackDamage} HP!",
                            }
                        },
                    },
                },
            ),
        ],
        {"Exit": "mall"},
    ),
    "foodCourt": Room(
        "You enter the food court, and are overwhelmed by the choice of resturants.",
        [],
        {
            "Enter Panda Express": "pandaExpress",
            "Enter McDonald's": "mcDonalds",
            "Exit": "mall",
        },
    ),
    "pandaExpress": Room(
        "You enter the Panda Express. Loud music is blaring on the speakers, and a cashier seems ready to take your order",
        [
            NPC(
                "Cashier",
                {
                    "dialogue": Dialogue(
                        "Welcome to Panda Express What would you like to order?",
                        {
                            '"Fried Rice"': Dialogue(
                                "Would you like to add Coke to that?",
                                {
                                    '"Yes"': Dialogue(
                                        "You enjoy the fried rice and coke and feel energized to further explore the mall",
                                        {"Go explore": False},
                                        speaker=False,
                                    ).speak,
                                    '"No"': Dialogue(
                                        '"You enjoy your Fried Rice, but eating it made you thirsty and so you ordered a coke anyways and feel energized to explore the mall further"',
                                        {"Go explore": False},
                                        speaker=False,
                                    ).speak,
                                },
                            ).speak,
                            '"Just Coke"': Dialogue(
                                '"Drinking the Sweet drink made you realize how hungry you actually were, so you ordered some fried rice anyways, You enjoy the fried rice and coke and feel energized to further explore the mall"',
                                {"Go explore": False},
                                speaker=False,
                            ).speak,
                            '"Nothing"': False,
                        },
                    ).speak,
                    "stats": {
                        "hp": 40,
                        "attacks": {
                            "thePanda": {
                                "damage": 5,
                                "random": 2,
                                "message": "${enemyName} grabs the panda express panda from the back and it goes in for the attack! They hit you for ${attackDamage} HP!",
                            }
                        },
                    },
                },
            )
        ],
        {"Exit": "foodCourt"},
    ),
    "mcDonalds": Room(
        "You enter McDonald's. The smell of windex and fries overpowers your nostrils.",
        [
            NPC(
                "Cashier",
                {
                    "dialogue": Dialogue(
                        "Welcome to McDonald's. We hope you leave soon. What would you like?",
                        {
                            '"Ice Cream"': Dialogue(
                                "Im finna keep it a buck witchu bruh, ice cream machine broke",
                                {
                                    "Offer to Fix the Machine": Dialogue(
                                        "Alright, but if you mess it up even more they gonna kick you out the mall!",
                                        {
                                            "Unplug the Ice Cream Machine": Dialogue(
                                                'You unplug the machine and go back to the front counter and tell the person at the front "yea that machine broken fr i couldn’t fix it"',
                                                {"Leave": False},
                                                speaker=False,
                                            ),
                                            "Eat the Ice Cream Spewing out of the Machine": Dialogue(
                                                "You put your mouth right under the dispensing nozzle, and begin to eat all of the ice cream. You sit there for a while, and eventually your stomach gives in and you must stop.",
                                                {"Stop": False},
                                            ),
                                        },
                                        prologue='You: "Im somewhat of an engineer myself, i bet i could fix it"',
                                        epilogue="you cautiously tinker around under the machine and realize that it wasn’t even plugged in. You plug the machine in, it awakens from its slumber with a unpleasant hum, and starts dispensing ice cream nonstop",
                                    ).speak,
                                },
                            ).speak,
                            "Big Mac": Dialogue(
                                "Your order comes and you indulge in one of the most underwhelming burgers of your life, still hungry you hunt for another restaurant to try",
                                {"Go explore": False},
                                speaker=False,
                            ).speak,
                            '"Just Sprite"': Dialogue(
                                '"Ay ur sure u wanna try this sprite?? It’s wayy different from regular sprite just look at what it did to that guy over there"',
                                {
                                    "Order Something Else": True,
                                    "Look at the Guy He was Talking About": Dialogue(
                                        "You see a crocodile laying belly up on one of the tables drenched in what you assume to be none other than the infamous sprite “dat mcdonalds sprite done got to him” a nearby person eating a big mac tells you",
                                        {
                                            "Order the Sprite Despite Everyone's Warnings": Dialogue(
                                                "You order the sprite and take a sip immediately it feels as if the soul has exited your body your eyes finally open and you find yourself in outer space surrounded by monarch butterflies you look at the earth spinning and pulsing through all of the colors of the rainbow below you, you eventually start blinking rapidly and find yourself back in the mcdonalds covered in the sprite right next to the crocodile. Crazy times. Everything has a purple glow and you have never felt more alive before. Drinking the mcdonald’s sprite completely energized you, you look back into the cup and see a little bit of the sprite left which hadn’t drenched you. Do you want to finish it off?",
                                                {
                                                    "Stop Drinking": False,
                                                    "Keep Drinking": Dialogue(
                                                        "you drink the last of it and once again once you open your eyes you find yourself in space except something is different this time.. As you look around you find a bubble gun in your hand and an approaching group of toy story aliens each in their own little flying saucers. The words SPACE INVADERS shows up in bright yellow comic sans font above your head.",
                                                        {
                                                            "Fight": NPC(
                                                                "Space Invaders",
                                                                {
                                                                    "dialogue": False,
                                                                    "stats": {
                                                                        "hp": 50,
                                                                        "attacks": {
                                                                            "beam": {
                                                                                "damage": 20,
                                                                                "random": 5,
                                                                                "message": "The ${enemyName} go all out, firing a beam at you. You lose ${attackDamage} HP!",
                                                                            },
                                                                            "bubble": {
                                                                                "damage": 10,
                                                                                "random": 50,
                                                                                "message": "The ${enemyName} combine and throw a bubble at you. You lose ${attackDamage} HP!",
                                                                            },
                                                                        },
                                                                    },
                                                                },
                                                            ).fightViaDialogue
                                                        },
                                                    ).speak,
                                                },
                                            ).speak,
                                            "Give Up on the Sprite": False,
                                        },
                                        speaker=False,
                                    ).speak,
                                },
                            ).speak,
                            '"Nothing"': False,
                        },
                    ).speak,
                    "stats": {
                        "hp": 40,
                        "attacks": {
                            "bigMac": {
                                "damage": 20,
                                "random": 5,
                                "message": "${enemyName} starts throwing big macs at you! They hit you for ${attackDamage} HP!",
                            }
                        },
                    },
                },
            )
        ],
        {"Exit": "foodCourt"},
    ),
}




possibilities = {
    "take": ["grab", "pick up", "collect", "retrieve", "take", "obtain"],
    "travel": ["go", "travel", "leave", "walk", "exit", "run", "go to", "go up"],
    "quit": ["quit", "exit", "quit game", "stop"]
} 

# Engine

def getAllInteracts(interactList, preface=False):
    interactables = []
    for interact in interactList:
        if not interact.visible:
            continue
        interactables.append(interact.name)
        if preface:
            interactables.append(interact.preface + interact.name)
    return interactables

def removeInteractByObject(interactList, interactObj):
    for i, interact in enumerate(interactList):
        if interactObj == interact:
            interactList.pop(i)
            break
    return interactList

def getInteractByName(name, interactList):
    for interact in interactList:
        if name.lower() == interact.name.lower() or name.lower() == interact.preface.lower() + interact.name.lower():
            return interact

def listToStr(inputList):
    output = ""
    for item in inputList:
        output += item + ", "
    return output[:-2]

def checkStart(inputStr, possibilites):
    matches = []
    for possibility in possibilites:
        if possibility in inputStr:
            if inputStr.split(possibility)[0] == '':
                matches.append(possibility) 
    if len(matches) == 0:
        return ""
    highestLength = matches[0]  # Find the match with the most characters, fixes bug with 'talk' vs 'talk to' 
    for match in matches:
        if len(match) > len(highestLength):
            highestLength = match
    return highestLength

def printInteracts(message, interactList):
    output = ""
    for interact in interactList:
        if not interact.visible:
            continue
        output += interact.preface + interact.name + ", "

    if output != "":
        Helper().slowPrint(message + " " + output[:-2])

def printRooms(message, roomList):
    Helper().slowPrint(message + " " + listToStr(list(currentRoom.connectedRooms.keys())))

def isValidRoom(rooms, location):
    xVals = rooms.keys()
    if location[0] in xVals:
        yVals = rooms[location[0]].keys()
        if location[1] in yVals:
            return True
    return False

def copyListValue(inputList, interact=False):
    outputList = []
    for item in inputList:
        if interact and item.visible is False:  # If list is interact list and item is not visible, don't add it
            continue
        outputList.append(item)
    return outputList

def orderActions(interactables):
    actions = {}
    for interactable in interactables:
        if not interactable.visible:
            continue
        actions[interactable.name] = {}
        for option in interactable.actions:
            actions[interactable.name][option] = interactable.actions[option]
    return actions


currentPlayer = Player(rooms["mall"], {
    "hp": 100, 
    "power": 10,
    "money": 100,
    "attacks": {
        "Kick": {
            "damage": 4,
            "random": 2,
            "message": "You go in for a kick, hitting ${enemyName} for ${attackDamage} HP!" 
        },
        "Flail About!": {
            "damage": 2,
            "random": 1,
            "message": "You flail about randomly, ${enemyName} looks at you, confused, losing ${attackDamage} HP!" 
        },
        "Super fast mega spinny attack": {
            "damage": 5,
            "random": 0,
            "message": "You put out your arms and start spinning in circles, gaining more and more speed. ${enemyName} is hit for ${attackDamage} HP!" 
        }
    }
})

# Helper().playSound("An Yong Tong.mp3")

while True:
    if currentPlayer.stats["hp"] == 0:  # If dead
        break

    command = ""
    info = ""

    # Set current room, and give info
    currentRoom = currentPlayer.room
    currentRoom.welcome()

    # Organize interacts
    usableInteracts = copyListValue(currentRoom.interacts, interact=True)  # Start with rooms interacts
    for interact in currentPlayer.inventory:
        if interact.visible:
            usableInteracts.append(interact)  # Add inventory interacts

    # Create dictonary of possibilities
    actionDict = orderActions(usableInteracts)
    for interact in actionDict:  # { "interact": { "action1" : ["possibility1", "2", "etc"] } }
        for action in actionDict[interact]:
            potentialInputs = actionDict[interact][action]
            possibilities[action] = potentialInputs

    obtainableInteracts = []  # Make list of interacts which you can actually pickup
    for interact in currentRoom.interacts:
        if interact.obtainable:
            obtainableInteracts.append(interact)

    
    printInteracts("In Your Backpack:", currentPlayer.inventory)

    printInteracts("You see:", currentRoom.interacts)

    printRooms("You can:", currentRoom.connectedRooms)

    userSelection = input("HP: " + str(currentPlayer.stats["hp"]) + " | Money: $" + str(currentPlayer.stats["money"]) + ": ").lower()

    for item in possibilities:  # Split up input
        command = checkStart(userSelection, possibilities[item])
        if command != "":
            if len(userSelection.split(command + " ")) > 1:
                info = userSelection.split(command + " ")[1]
            break
    
    if command in possibilities["take"] and info in Helper().lowerList(getAllInteracts(obtainableInteracts)):  # Handle item taking
        currentPlayer.pickup(getInteractByName(info, obtainableInteracts))

    elif userSelection in Helper().lowerList(list(currentRoom.connectedRooms.keys())):  # Handle travel
        key = Helper().lowerToNormal(list(currentRoom.connectedRooms.keys()), userSelection)
        currentPlayer.room = rooms[currentRoom.connectedRooms[key]]

    elif info in Helper().lowerList(getAllInteracts(usableInteracts, preface=True)):  # Handle custom interactions
        selectedInteract = getInteractByName(info, usableInteracts)  # Get interact object by name

        for action in selectedInteract.actions:  # Go over possible actions
            for possibility in selectedInteract.actions[action]:  # Go over action's text possibilities
                if possibility == command:
                    selectedInteract.performAction(action, currentPlayer, currentRoom)
                    break
    elif command in possibilities["quit"]:
        print("Bye!")
        break
    else:
        Helper().slowPrint("Command not recognized!")

    print()  # Newline

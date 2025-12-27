## Example Visual Novel - Main Script
## This is a simple example game for testing translation workflows

# Define characters
define narrator = Character(None)
define mc = Character("[player_name]", color="#c8ffc8")
define sarah = Character("Sarah", color="#ff69b4")
define alex = Character("Alex", color="#4169e1")

# Default player name
default player_name = "Alex"

# The game starts here
label start:

    # Welcome message
    narrator "Welcome to our visual novel!"

    mc "Hi, my name is [player_name]."

    narrator "{size=18}{color=#808080}Academy - Main Hall{/color}{/size}"

    # Menu for player choice
    menu:
        "What's your name?"

        "{color=#4169e1}Explore the academy{/color}":
            jump explore_academy

        "{color=#ff69b4}Talk to Sarah{/color}":
            jump meet_sarah

        "Go to the library":
            jump library

label meet_sarah:

    sarah "Oh, hello! Are you the new student?"

    mc "Yes, I just transferred here. Nice to meet you!"

    sarah "I'm Sarah. Let me show you around the campus."

    mc "That would be {b}wonderful{/b}, thank you!"

label tour:

    sarah "This is the library. You'll spend a lot of time here studying."

    mc "Do they have good books on history?"

    sarah "Absolutely! The history section is my {color=#ff69b4}favorite{/color} spot."

label cafeteria:

    narrator "{size=18}{color=#808080}Cafeteria - Lunch Time{/color}{/size}"

    sarah "Let's grab some lunch. I'm starving!"

    mc "The food here looks amazing. What do you recommend?"

    # Food choice menu
    menu:
        sarah "What would you like?"

        "Order pasta":
            sarah "Try the pasta! It's the chef's specialty."

        "Order salad":
            sarah "Good choice! Fresh and healthy."

label friends:

    alex "Hey Sarah! Is this the new student?"

    sarah "Yes! [player_name], this is Alex, my best friend."

    alex "Welcome to the academy! Hope you like it here."

    mc "Thanks! Everyone has been so {b}kind{/b} and welcoming."

label ending:

    narrator "And so begins your adventure at the academy..."

    narrator "{size=24}{color=#4169e1}Chapter 1 Complete{/color}{/size}"

    return

# Alternative paths
label explore_academy:
    narrator "You explore the academy on your own..."
    jump tour

label library:
    narrator "You head straight to the library..."
    jump tour

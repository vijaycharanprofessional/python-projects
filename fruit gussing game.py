import random

class FruitGuessingGame:
    def __init__(self):
        self.fruits = {
            'apple': {
                'color': 'red or green',
                'shape': 'round',
                'taste': 'sweet and crunchy',
                'hint': 'Keeps the doctor away'
            },
            'banana': {
                'color': 'yellow',
                'shape': 'long and curved',
                'taste': 'sweet and soft',
                'hint': 'Monkeys love this fruit'
            },
            'orange': {
                'color': 'orange',
                'shape': 'round',
                'taste': 'citrus and juicy',
                'hint': 'Same name as a color'
            },
            'strawberry': {
                'color': 'red with seeds',
                'shape': 'heart-shaped',
                'taste': 'sweet and slightly tart',
                'hint': 'Has seeds on the outside'
            },
            'pineapple': {
                'color': 'yellow and brown',
                'shape': 'oval with spiky leaves',
                'taste': 'sweet and tangy',
                'hint': 'Wears a crown'
            },
            'watermelon': {
                'color': 'green outside, red inside',
                'shape': 'large and oval',
                'taste': 'very sweet and watery',
                'hint': 'Perfect for summer picnics'
            },
            'grape': {
                'color': 'purple or green',
                'shape': 'small and round',
                'taste': 'sweet and juicy',
                'hint': 'Comes in bunches'
            },
            'mango': {
                'color': 'yellow-orange',
                'shape': 'oval with large seed',
                'taste': 'sweet and tropical',
                'hint': 'King of fruits'
            }
        }
        
        self.score = 0
        self.total_questions = 0
        
    def display_welcome(self):
        print("=" * 50)
        print("       🍎 FRUIT GUESSING GAME 🍌")
        print("=" * 50)
        print("Guess the fruit based on the hints given!")
        print("Type 'quit' to exit the game")
        print("=" * 50)
        
    def get_random_fruit(self):
        return random.choice(list(self.fruits.keys()))
    
    def give_hint(self, fruit, hint_level):
        hints = [
            f"Color: {self.fruits[fruit]['color']}",
            f"Shape: {self.fruits[fruit]['shape']}",
            f"Taste: {self.fruits[fruit]['taste']}",
            f"Hint: {self.fruits[fruit]['hint']}"
        ]
        return hints[hint_level]
    
    def play_round(self):
        fruit = self.get_random_fruit()
        attempts = 0
        max_attempts = 4
        
        print(f"\n🎯 Round {self.total_questions + 1}")
        print("I'm thinking of a fruit...")
        
        while attempts < max_attempts:
            hint = self.give_hint(fruit, attempts)
            print(f"\n💡 Hint {attempts + 1}: {hint}")
            
            guess = input("\nWhat fruit am I thinking of? ").lower().strip()
            
            if guess == 'quit':
                return False
            elif guess == fruit:
                self.score += 1
                self.total_questions += 1
                print(f"\n🎉 Correct! It's a {fruit}!")
                print(f"⭐ You guessed it in {attempts + 1} hint(s)!")
                return True
            else:
                attempts += 1
                if attempts < max_attempts:
                    print("❌ Not quite! Here's another hint...")
                else:
                    print(f"\n💔 Game over! The fruit was: {fruit}")
                    self.total_questions += 1
                    return True
    
    def show_score(self):
        print(f"\n📊 Your Score: {self.score}/{self.total_questions}")
        if self.total_questions > 0:
            percentage = (self.score / self.total_questions) * 100
            print(f"📈 Success rate: {percentage:.1f}%")
            
        if self.score == self.total_questions and self.total_questions > 0:
            print("🏆 Perfect score! You're a fruit expert!")
        elif self.score / self.total_questions >= 0.7:
            print("👍 Great job! You know your fruits well!")
        elif self.score / self.total_questions >= 0.5:
            print("😊 Good effort! Keep practicing!")
        else:
            print("🌱 Keep learning about fruits!")
    
    def play_game(self):
        self.display_welcome()
        
        while True:
            continue_game = self.play_round()
            if not continue_game:
                break
                
            play_again = input("\nWould you like to play another round? (y/n): ").lower().strip()
            if play_again != 'y':
                break
        
        print("\n" + "=" * 50)
        print("           GAME OVER - FINAL SCORE")
        print("=" * 50)
        self.show_score()
        print("\nThanks for playing! 🍓🍊🍇")

# Run the game
if __name__ == "__main__":
    game = FruitGuessingGame()
    game.play_game()
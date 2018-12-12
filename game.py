from mode import Mode
from dal import Types, Difficulties
import numpy as np


class Game(Mode):
    """
    The main game mode.
    A session is one set of questions presented to the player according to his/her chosen setup.
    Restarting a session will ask the same player for a new setup for another set of questions.
    """

    def __init__(self):
        super().__init__()
        self._questions = []
        self._user = None
        self._restart = True

    def start(self):
        if not self.db.get_categories():
            self.ui.confirm("There are currently no available questions. "
                            "Please enter in admin mode to add questions.")
            self._restart = False
            return
        if not self._user:
            self.get_username()
        self.ui.alert("Choose options for the game setup.")
        self.setup_game()
        self.ask_questions()

    def get_username(self):
        """ Asks the user to enter his/her username."""
        username = self.ui.get_user_input("Enter your username:")
        try:
            self._user = self.db.add_user(username)
        except ValueError:
            self.ui.alert("Username cannot be empty.")
            if self.ui.retry():
                self.get_username()

    def setup_game(self):
        """ Asks the user to choose amount of questions, category and difficulty.
        Sets the _questions attribute to the questions matching the options.
        If the amount of questions available for the given options is less than the amount
            given by the player, alerts the player with the actual number of questions matched.
        """
        amount = int(self.ui.get_user_input("How many questions would you like to try?",
                                            self._validate_pos_num))
        category = self._choose_category("Choose category:")
        difficulty = self.ui.get_user_choice(self.db.get_difficulties(category), "Choose difficulty:")
        self._questions = self.db.get_questions(amount, category, difficulty)
        if len(self._questions) < amount:
            self.ui.alert(f"There are {len(self._questions)} questions in category {category} "
                          f"with difficulty {difficulty}.")

    def ask_questions(self):
        """ Iterates over the list of questions and presents the question with its possible answers
                to the player.
            For each question, updates the database whether the player answered correctly.
        """
        for i, q in enumerate(self._questions):
            answers = [q['correct_answer']]
            if q['type'] == Types.boolean.name:
                answers.append("False" if answers[0] == "True" else "True")
            else:
                for a in q['wrong_answers']:
                    answers.append(a)
            user_answer = self.ui.get_user_choice(np.random.permutation(answers),
                                                  f"Question {i + 1}: {q['question']}")

            # update the database whether the user answered correctly or not
            if user_answer == q['correct_answer']:
                self.db.update_correct(q['id'], self._user, 1)
                self.ui.alert("Correct! Well done.")
            else:
                self.db.update_correct(q['id'], self._user, 0)
                self.ui.alert("Incorrect! Maybe next time.")

    def restart(self):
        """
        Asks the player if he wants to play again.

        Returns:
             bool: True if the player chose yes, False if he chose no.
        """
        return self._restart and self.ui.yes_no("Would you like to play again?")

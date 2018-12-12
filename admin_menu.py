from mode import Mode
from dal import Types, Difficulties


class AdminMenu(Mode):
    """ This class represents the administrative menu."""

    main_menu_options = [
        "Add category",
        "Remove category",
        "Add question",
        "Import questions",
        "Get game statistics"
    ]

    MAX_WRONG_ANSWERS = 3
    N_TOP_USERS = 3

    def __init__(self):
        super().__init__()

    def start(self):
        self.ui.alert("-- Admin menu --")
        self.ui.alert("What would you like to do?")
        self.main()

    def restart(self):
        """ Asks the admin if he wants to do something else.

            Returns:
                bool: True if the player chose yes, False if he chose no.
        """
        return self.ui.yes_no("Would you like to do something else?")

    def main(self):
        """ Request the admin to choose one of the AdminMenu.main_menu_options."""
        choice = self.ui.get_user_choice(self.main_menu_options)
        if choice:
            choice = '_'.join(choice.lower().split())
            self.__getattribute__(choice)()

    def add_category(self):
        """ Request the admin to enter a new category name.
            If the name already exists, ask the admin if he wants to retry.
            Otherwise, add the new category to the database.
        """
        name = self.ui.get_user_input("Enter category name:")
        if name:
            try:
                self.db.add_category(name)
            except ValueError:
                self.ui.alert("There is already a category with that name.")
                if self.ui.retry():
                    self.add_category()
            else:
                self.ui.alert("Category added successfully.")

    def remove_category(self):
        """ Asks the admin to choose a category to remove from the database."""
        category = self._choose_category("Please choose a category to remove.")
        if category:
            self.db.remove_category(category)
            self.ui.alert("Category removed.")

    def add_question(self):
        """
        Asks the admin to enter the new question details.
            If all the details are valid, add the new question to the database.
            Otherwise, ask the admin if he wants to try again.
        """
        category = self._choose_category("Choose a category for the question:")
        if category:
            q_type = self.ui.get_user_choice(self.db.types, "Type of question:")
            difficulty = self.ui.get_user_choice(self.db.difficulties, "Question difficulty:")
            question = self.ui.get_user_input("Enter the question:")
            if q_type == Types.boolean.name:
                correct_answer = self.ui.get_user_choice(["True", "False"], "Choose the correct answer:")
                wrong_answers = None
            else:
                correct_answer = self.ui.get_user_input("Enter the correct answer:")
                n_wrong = int(self.ui.get_user_input(f"Number of wrong answers (1-{self.MAX_WRONG_ANSWERS}):",
                                                     self._validate_wrong_answer_count))
                wrong_answers = []
                for i in range(n_wrong):
                    wrong_answers.append(self.ui.get_user_input("Enter answer:"))

            # add the question to the database
            try:
                self.db.add_question(category, q_type, difficulty, question, correct_answer, wrong_answers)
            except ValueError as e:
                self.ui.alert("Something went wrong when trying to add the question to the database.")
                self.ui.alert(e)
                if self.ui.retry():
                    self.add_question()
            else:
                self.ui.alert("Question added successfully.")

    def import_questions(self):
        """
        Asks the admin to choose the amount of questions(max: 50), a category
            from the available categories of the api, and difficulty from the available
            difficulties as given by the data access layer Difficulties class.
            Lets the admin know how many questions were added as some might be duplicates.
        """
        extra_options = ["Random"]
        amount = self.ui.get_user_input(f"How many questions would you like to import? "
                                        f"(max: {self.db.MAX_IMPORT_AMOUNT}, default: 1):",
                                        self._validate_pos_num)
        category = self.ui.get_user_choice(self.db.get_opentdb_categories() + extra_options,
                                           f"Choose category or {', '.join(extra_options)}:")
        difficulty = self.ui.get_user_choice(self.db.difficulties + extra_options,
                                             f"Choose difficulty or {', '.join(extra_options)}:")
        import_options = {}
        if amount != "":
            import_options['amount'] = int(amount)
        if difficulty in self.db.difficulties:
            import_options['difficulty'] = difficulty
        if category in self.db.get_opentdb_categories():
            import_options['category'] = category
        try:
            count = self.db.import_questions(**import_options)
            self.ui.alert(f"Import successful. {count} questions were added to the database.")
        except ConnectionError:
            self.ui.alert("Something went wrong when trying to import from opentdb. Try again later.")

    def get_game_statistics(self):
        """
        Asks the admin to choose which statistics to show from a list of available options.
        Displays the chosen option using the ui.show_data method.
        """
        options = ["Show correct/incorrect answers by category",
                   "Show correct/incorrect answers by difficulty",
                   f"Show top {self.N_TOP_USERS} users"]
        choice = self.ui.get_user_choice(options)
        if choice == options[0]:
            result = self.db.get_results_by('category')
            #result = result.sort_values('Category')
        elif choice == options[1]:
            result = self.db.get_results_by('difficulty')
            # the order is lexicographic but we want it ordered by difficulty.
            result['Difficulty'] = result['Difficulty'].map(lambda x: Difficulties[x])
            result = result.sort_values('Difficulty')
        elif choice == options[2]:
            result = self.db.get_results_by('user', limit=self.N_TOP_USERS, order_by='Correct', ascending=False)
        if len(result) > 0:
            self.ui.show_data(result, bar=choice != options[2])
        else:  # no data
            self.ui.alert("There is currently no data to show.")

    def _validate_wrong_answer_count(self, count):
        # a validation method to use with the ui.get_user_input method
        # validates that the input is a number between 1 and MAX_WRONG_ANSWERS
        error = f"Invalid input. Must be a number between (1-{self.MAX_WRONG_ANSWERS}."
        try:
            count = int(count)
        except TypeError:
            return error
        if not (0 < count <= self.MAX_WRONG_ANSWERS):
            return error

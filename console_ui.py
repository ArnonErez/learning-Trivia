import os
import html
import matplotlib.pyplot as plt


class ConsoleUI:
    """
    A command-line UI for the trivia game.
    """

    def get_user_choice(self, options, message=None):
        """
        Displays a list of options to the user to choose from.

        Args:
            options: iterable of options to choose from.
            message (str, optional): A message to display before the list of options.

        Returns: The chosen option name (str) or False if 0 (abort) was chosen.

        """
        options = [html.unescape(o) for o in options]
        if message:
            self.alert(html.unescape(message))
        # print the list of options
        print()  # padding top
        for i, o in enumerate(options):
            print(f"\t{i + 1}. {o.capitalize()}")

        # get the user choice
        choice = int(self.get_user_input("Please choose one of the options above.",
                                         lambda c: self._choice_validator(c, len(options))))
        if choice == 0:
            return False
        return options[choice - 1]

    def get_user_input(self, query, validate=None):
        """
        Request the user to enter input for the given query.

        Args:
            query (str): The query to present to the user
            validate(func, optional): A function to validate the input with.
                The function should return an error message
                    if the input is not valid, None or False otherwise.
        """
        print()  # padding top
        response = input(query + ' ')
        if validate:
            error = validate(response)
            if error:
                self.alert(error)
                return self.get_user_input(query, validate)
        return response

    def welcome(self, message):
        """ Displays a welcome message to the user."""
        self.restart()
        print(self.big_title(message))
        self.alert("Good luck!")

    def big_title(self, message):
        wrapper_width = len(message) + 6
        line = '#' * wrapper_width
        msg = '\t' * 3 + line + '\n'
        msg += '\t' * 3 + '#  ' + message + '  #' + '\n'
        msg += '\t' * 3 + line
        return msg

    def alert(self, message):
        """ Displays the given message.

        Args:
            message (str): The message to display.

        """
        print()  # padding top
        print(message)

    def retry(self):
        """
        Presents the user with the option to retry their last action.

        Returns:
            bool: True if the user wants to retry, False otherwise.

        """
        return self.yes_no("Would you like to try again?")

    def yes_no(self, query):
        """
        Presents the user with the given query with either Yes or No option.

        Args:
            query (str): The query to display.

        Returns:
            bool: True if the user chose yes, False otherwise.

        """
        options = ["Yes", "No"]
        choice = self.get_user_choice(options, query)
        return choice == "Yes"

    def restart(self):
        """ Clears the screen of all text."""
        os.system('cls')

    def confirm(self, message):
        """
        Displays a confirmation message to the user.

        Args:
            message (str): The message to display.

        """
        self.alert(message)
        input("Click Enter to continue...")

    def show_data(self, data, bar=False):
        """
        Displays the data as a table or a bar plot (opened in a popup window).

        Args:
            data (pandas.DataFrame): The data to display.
                Assumes the categorical data is in the first column and the numerical data in the rest.
            bar (bool): If True, a horizontal bar plot will be displayed. Otherwise a table will be displayed.
                Defaults to False.

        """
        if bar:
            data.plot.barh(x=0, figsize=(8, 6), xticks=range(data.iloc[:, 1:].values.max() + 1))
            plt.tight_layout()
            plt.show()
        else:
            self._print_table(data)

    def _print_table(self, df):
        # helper method for show_data to display the table.
        cell_width = 12
        name_len = max(cell_width, df.loc[0].str.len().max())
        sep = '+' + ('-' * name_len + '+') + ('-' * cell_width + '+') * (len(df.columns) - 1)
        head = self._row_to_line(df.columns, cell_width, name_len, is_head=True)
        body = ""
        for row in df.values:
            body += self._row_to_line(row, cell_width, name_len) + '\n'
        body = body[:-1]
        print(sep)
        print(head)
        print(sep)
        print(body)
        print(sep)

    def _row_to_line(self, row, cell_width, name_len, is_head=False):
        # helper method for the print_table to turn a data entry (row) to a table line.
        line = '|'
        for i, cell in enumerate(row):
            line += f"{cell:{'^' if is_head else ''}{cell_width if i > 0 else name_len}}|"
        return line

    def _choice_validator(self, choice, n_options):
        # validates that the entered choice is one of the possible options or 0.
        try:
            if int(choice) in range(n_options + 1):
                return False  # valid choice
        except ValueError:
            pass  # not a number
        return "Invalid choice."

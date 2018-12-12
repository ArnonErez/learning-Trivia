from abc import ABC, abstractmethod
from db_sql_server import DbSqlServer
from db_mongodb import DbMongodb
from console_ui import ConsoleUI


class Mode(ABC):
    """
    Abstract class representing an activation mode of the trivia game.
    Some mode examples are administrative menu, predefined game setups and more.
    """

    possible_dbs = {
        'mongodb': DbMongodb,
        'sql_server': DbSqlServer
    }

    def __init__(self, db='mongodb'):
        """
        Initiates the current game mode.

        Args:
            db: The database to run the game with. One of Mode.possible_dbs
        """
        self.ui = ConsoleUI()
        self.db = self.possible_dbs[db]()

    @abstractmethod
    def start(self):
        """
        Starts a new session.

        """
        pass

    @abstractmethod
    def restart(self):
        """
        Asks the user if he/she wants to restart the current session.

        Returns:
             bool: True if the user chose yes, False otherwise.

        """
        pass

    @staticmethod
    def _validate_pos_num(val):
        # a validation method to use with the ui.get_user_input method
        if val == "":  # empty string is allowed. default value will be used.
            return
        try:
            if int(val) <= 0:
                return "Invalid input. Must be positive."
        except ValueError:
            return "Invalid input. Must be a positive number."

    def _choose_category(self, message):
        categories = self.db.get_categories()
        if len(categories) == 0:
            self.ui.alert("There are currently no categories in the database.")
        else:
            return self.ui.get_user_choice(sorted(categories), message)

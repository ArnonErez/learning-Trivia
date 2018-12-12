from abc import ABC, abstractmethod
import requests
from enum import Enum, unique


@unique
class Difficulties(Enum):

    easy = 1
    medium = 2
    hard = 3

    def __str__(self):
        return self.name.capitalize()

    def __lt__(self, other):
        return self.value < other.value


@unique
class Types(Enum):

    boolean = 1
    multiple = 2


class DAL(ABC):
    """ A Data Abstract Layer that supplies the functions used to interact with the database.

    Attributes:
        difficulties (list): A list of the possible difficulties defined by the Difficulties enum.
        types (list): A list of the possible types defined by the Types enum.

    """

    MAX_IMPORT_AMOUNT = 50

    def __init__(self):
        self.opentdb_api = "https://opentdb.com/api.php"
        self._opentdb_categories = None
        self.difficulties = list(Difficulties.__members__.keys())
        self.types = list(Types.__members__.keys())

    @abstractmethod
    def add_question(self, category, q_type, difficulty, question, correct_answer, wrong_answers=None):
        """
        Adds a question to the database.

        Args:
            category (str): The category of the question.
            q_type (str): The type of the question. One of the Types enum keys.
            difficulty (str): The difficulty of the question. One of the dal.Difficulties enum keys.
            question (str): The text of the question to be added.
            correct_answer: The correct answer.
            wrong_answers (list): If the question type is multiple, a list of the incorrect answers.
                For boolean questions, this is assumed to be None.

        Raises:
            ValueError: If any of the parameters is invalid or if the question already exists.
                Certain implementations may define valid differently. (e.g. maximum length)

        """
        pass

    @abstractmethod
    def import_questions(self, amount=1, difficulty=None, category=None):
        """
        Imports questions from https://opentdb.com and adds them to the database.

        Args:
            amount (int): Number of questions to import. This is limited to 50 by the api. Defaults to 1.
            difficulty (str): If specified, the imported questions will be of the specified difficulty.
                If None, the imported questions will have a random difficulty. Defaults to None.
            category (str, optional):If specified, the imported questions will be of the specified category.
                If None, the imported questions will have a random category. Defaults to None.

        Returns:
            int: The number of questions successfully added to the database. This is not guaranteed to be
                equal to amount as some questions may already be in the database.

        Raises:
            ValueError: If the given difficulty or category are invalid.
            ConnectionError: If the import failed due to unknown reasons (e.g. no internet connection).

        """
        pass

    @abstractmethod
    def add_category(self, name):
        """
        Adds a category to the database.

        Args:
            name (str): The name of the category to be added.

        Returns:
            The id of the inserted (or already existing) category.

        """
        pass

    @abstractmethod
    def remove_category(self, name):
        """
        Removes a category from the database. This will also remove all questions under that category,
            along with any other reference of these questions. (e.g. score records)
            If the category does not exist, does nothing.

        Args:
            name (str): The name of the category to be removed.

        """
        pass

    @abstractmethod
    def get_categories(self):
        """
        Get all the categories in the database.

        Returns:
            list: A list of all the categories in the database.

        """
        pass

    @abstractmethod
    def get_difficulties(self, category):
        """
        Get the difficulties that are available for the given category.

        Args:
            category (str): The name of the category.

        Returns:
            list: A list of the difficulties available in the given category.

        """
        pass

    @abstractmethod
    def get_questions(self, amount, category, difficulty):
        """
        Gets questions from the database.

        Args:
            amount (int): The amount of questions to get.
            category (str): The category of the questions to get.
            difficulty (str): The difficulty of the questions to get.

        Returns:
            list: A list of the questions available for the given criteria.
                The length of the list may be less the the give amount.
                The questions are a dictionary with the keys:
                    [id, type, question, correct_answer, wrong_answers(if type is multiple)]

        """
        pass

    @abstractmethod
    def add_user(self, name):
        """
        Adds a user to the database.

        Args:
            name (str): The name of the user to be added.

        Returns:
            The id of the inserted (or already existing) user.

        """
        pass

    @abstractmethod
    def update_correct(self, question, user, correct):
        """
        Updates the database whether the user answered the question correctly or not.

        Args:
            question: The question id
            user: The user id
            correct (bool or int): True (or 1) if the user answered correctly, False (or 0) otherwise.

        Raises:
            ValueError: If the question or user are not in the database or if correct is invalid.
        """
        pass

    @abstractmethod
    def get_results_by(self, by, order_by=None, ascending=True, limit=None):
        """
        Gets the number of correct/incorrect questions grouped by the given parameter.

        Args:
            by (str): The parameter to group by. Should be one of [user, category, difficulty]
            order_by (str): The order of the returned data.
                The possible options can change between different implementations.
                If None, the order will be lexicographically ascending by the given parameter 'by'.
                Defaults to None.
            ascending (bool): If True, order will be ascending, otherwise order will be descending.
                Defaults to True.
            limit (int): The number of entries to return. The returned entries will be chosen as the
                top #limit entries in the sorted data.

        Returns:
            pandas.DataFrame: The DataFrame will have 3 columns.
                The first will be the name of the parameter 'by'.
                The others will be the number of correct/incorrect answers respectively.
                All column names will be capitalized.

        """
        pass

    def get_opentdb_categories(self):
        """
        Gets all the categories available at https://opentdb.com.

        Returns:
            list: A list of the names of the categories.

        """
        # on the first call to this method, the categories will be kept in a dictionary
        # with the name as key and the id (as provided by the api) as value.
        # the categories are unlikely to be changed during a game session so there is no need
        # to do it more than once.
        if self._opentdb_categories is None:
            self._opentdb_categories = dict()
            with requests.get(r"https://opentdb.com/api_category.php") as result:
                for cat in result.json()['trivia_categories']:
                    self._opentdb_categories[cat['name']] = cat['id']
        return list(self._opentdb_categories.keys())

    def _import_questions_from_opentdb(self, amount=1, difficulty=None, category=None):
        # The code below is shared among different implementations of this class.
        # It returns a list of question objects represented as dictionary
        # Classes that implement this interface should call the parent method to get the
        # list and then save it in the database.

        # prepare the query string
        api_query = self.opentdb_api + f"?amount={amount}"

        if difficulty:  # not default (i.e random)
            try:
                api_query += f"&difficulty={Difficulties[difficulty].name}"
            except KeyError:
                raise ValueError(f"Invalid difficulty {difficulty}."
                                 f" The possible difficulties are {self.difficulties}")

        if category:  # not default (i.e random)
            if category not in self.get_opentdb_categories():
                raise ValueError(f"Invalid category {category}.")
            else:
                api_query += f"&category={self._opentdb_categories[category]}"  # the api category id

        # try to get the requested questions from opentdb
        with requests.get(api_query) as result:
            result = result.json()
            if result["response_code"] != 0:
                raise(ConnectionError("There was an error when trying to get the questions from opentdb"))
            return result['results']

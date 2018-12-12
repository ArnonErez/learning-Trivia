from dal import *
import pyodbc
import pandas as pd


class DbSqlServer(DAL):
    """
    Implementation of the DAL using sql-server with pyodbc.
    """

    DB_NAME = 'Trivia'
    SERVER = 'localhost\SQLEXPRESS'
    MAX_QUESTION_LENGTH = 300
    MAX_ANSWER_LENGTH = 150

    # Must change the Server attribute according to the device
    _conn_str = "Driver={ODBC Driver 13 for SQL Server};" \
                f"Server={SERVER};" \
                f"Database={DB_NAME};" \
                "Trusted_Connection=yes;"

    # sql for the get_results_by method.
    _sql_get_results_by = {
        'category': """
            SELECT c.CategoryName as Category, SUM(r.Correct) as Correct, SUM(1 - r.Correct) as Incorrect
            FROM Categories c JOIN Questions q
            ON c.CategoryID = q.CategoryID
            JOIN Records r
            ON r.QuestionID = q.QuestionID
            GROUP BY c.CategoryName
        """,
        'difficulty': """
            SELECT q.Difficulty, SUM(r.Correct) as Correct, SUM(1 - r.Correct) as Incorrect
            FROM Questions q JOIN Records r
            ON r.QuestionID = q.QuestionID
            GROUP BY q.Difficulty
        """,
        'user': """
            SELECT u.UserName, SUM(r.Correct) as Correct, SUM(1 - r.Correct) as Incorrect
            FROM Users u JOIN Records r
            ON r.UserID = u.UserID 
            GROUP BY u.UserName
        """
    }

    def __init__(self):
        super().__init__()

    def add_question(self, category, q_type, difficulty, question, correct_answer, wrong_answers=None):
        if self._is_duplicate(question):
            raise ValueError("Question already in the database.")
        conn = pyodbc.connect(self._conn_str())
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO Questions
                OUTPUT INSERTED.QuestionID
                VALUES (?, ?, ?, ?, ?)
            """
            try:
                cat_id = self.add_category(category)  # add the category if it doesn't exist and get its id
                q_id = cursor.execute(sql, cat_id, Types[q_type].value, Difficulties[difficulty].value,
                                      question, correct_answer).fetchval()
            except KeyError:
                raise ValueError(f"Invalid question type {q_type} or difficulty {difficulty}.")
            except pyodbc.DataError:
                raise ValueError("Too many characters for the question (max: {}) or the correct answer (max: {})."
                                 .format(self.MAX_QUESTION_LENGTH, self.MAX_ANSWER_LENGTH))
            except pyodbc.IntegrityError:
                raise ValueError(f"Category {category} does not exist.")
            if q_type == Types.multiple:
                self._add_answers(q_id, wrong_answers, conn)

    def add_category(self, name, conn=None):
        if not conn:
            conn = pyodbc.connect(self._conn_str())
        with conn.cursor() as cursor:
            sql = """
                IF EXISTS (SELECT 1 FROM Categories WHERE CategoryName = ?)
                    BEGIN
                        SELECT CategoryID
                        FROM Categories
                        WHERE CategoryName = ?
                    END
                ELSE
                    BEGIN
                        INSERT INTO Categories
                        OUTPUT INSERTED.CategoryID
                        VALUES (?)
                    END
            """
            try:
                return cursor.execute(sql, name, name, name).fetchval()
            except pyodbc.IntegrityError:  # empty name
                raise ValueError("Category name cannot be empty.")

    def remove_category(self, category):
        conn = pyodbc.connect(self._conn_str())
        with conn.cursor() as cursor:
            sql = """
                DELETE FROM Categories
                WHERE CategoryName = ?
            """
            cursor.execute(sql, category)

    def get_categories(self):
        conn = pyodbc.connect(self._conn_str())
        with conn.cursor() as cursor:
            sql = """
                SELECT CategoryName
                FROM Categories
            """
            return [cat[0] for cat in cursor.execute(sql).fetchall()]

    def import_questions(self, amount=1, difficulty=None, category=None):
        # import questions from the opentdb website
        questions = super()._import_questions_from_opentdb(amount, difficulty, category)

        # add the questions to the database
        count = 0  # some questions can be duplicates so count how many were added
        for q in questions:
            try:
                self.add_question(q['category'], Types[q['type']].name,
                                  Difficulties[q['difficulty']].name,
                                  q['question'], q['correct_answer'], q['incorrect_answers'])
                count += 1
            except ValueError:  # duplicate or too long question/answer
                pass
        return count

    def get_questions(self, amount, category, difficulty):
        conn = pyodbc.connect(self._conn_str())
        sql = """
            SELECT TOP (?) q.QuestionID, q.QuestionType, q.Question, q.CorrectAnswer
            FROM Questions q JOIN Categories c
            ON q.CategoryID = c.CategoryID
            WHERE c.CategoryName = ? AND q.Difficulty = ?
            ORDER BY NEWID()
        """
        out = []
        print(difficulty)
        with conn.cursor() as cursor:
            questions = cursor.execute(sql, amount, category, Difficulties[difficulty].value).fetchall()
        for q in questions:
            question = {
                'id': q.QuestionID,
                'type': Types(q.QuestionType).name,
                'question': q.Question,
                'correct_answer': q.CorrectAnswer
            }
            if question['type'] == 'multiple':
                question['wrong_answers'] = self._get_answers(q.QuestionID, conn)
            out.append(question)
        return out

    def get_difficulties(self, category):
        conn = pyodbc.connect(self._conn_str())
        with conn.cursor() as cursor:
            sql = """
                SELECT DISTINCT q.Difficulty
                FROM Questions q JOIN Categories c
                ON q.CategoryID = c.CategoryID
                WHERE c.CategoryName = ?
            """
            difficulties =  cursor.execute(sql, category).fetchall()
            return [Difficulties(d[0]).name for d in difficulties]

    def add_user(self, name):
        conn = pyodbc.connect(self._conn_str())
        with conn.cursor() as cursor:
            sql = """
                IF EXISTS (SELECT 1 FROM Users WHERE UserName = ?)
                    BEGIN
                        SELECT UserID
                        FROM Users
                        WHERE UserName = ?
                    END
                ELSE
                    BEGIN
                        INSERT INTO Users
                        OUTPUT INSERTED.UserID
                        VALUES (?)
                    END
            """
            try:
                return cursor.execute(sql, name, name, name).fetchval()
            except pyodbc.IntegrityError:  # empty name
                raise ValueError("Username cannot be empty.")

    def update_correct(self, question, user, correct):
        conn = pyodbc.connect(self._conn_str())
        with conn.cursor() as cursor:
            sql = """
                IF EXISTS (SELECT 1 FROM Records WHERE QuestionID = ? AND UserID = ?)
                    BEGIN
                        UPDATE Records
                        SET Correct = ?
                        WHERE QuestionID = ? AND UserID = ?
                    END
                ELSE
                    BEGIN
                        INSERT INTO Records
                        VALUES (?, ?, ?)
                    END
            """
            try:
                cursor.execute(sql, question, user, correct, question, user, question, user, correct)
            except pyodbc.IntegrityError:
                # user or question does not exist
                raise ValueError(f"Invalid question or user id.")

    def get_results_by(self, by, order_by=None, ascending=True, limit=None):
        # validate params
        if order_by and order_by not in {'Correct', 'Incorrect'}:
            raise ValueError("order_by must be either 'Correct' or 'Incorrect' (case-sensitive)")
        if by not in {'category', 'difficulty', 'user'}:
            raise ValueError(f"Invalid value {by} for parameter by."
                             f"Can only return results by category, difficulty or user.")

        sql = self._sql_get_results_by[by].strip()
        params = []
        if limit:
            sql = sql[:6] + " TOP (?)" + sql[6:]
            params.append(limit)

        if order_by:
            if order_by.lower() == 'correct':
                sql += "\nORDER BY Correct"
            else:
                sql += "\nORDER BY Incorrect"
            if not ascending:
                sql += " DESC"

        conn = pyodbc.connect(self._conn_str())
        result = pd.read_sql(sql, conn, params=params)
        if by == 'difficulty':
            result['Difficulty'] = result['Difficulty'].map(lambda x: Difficulties(x).name)
        return result

    def _add_answers(self, q_id, wrong_answers, conn):
        # helper method to add answers to the database for multiple type questions
        sql = """
            INSERT INTO Answers
            VALUES (?, ?)
        """
        params = [(q_id, a) for a in wrong_answers]
        with conn.cursor() as cursor:
            try:
                cursor.executemany(sql, params)
            except pyodbc.IntegrityError:
                raise ValueError("Invalid question id.")
            except pyodbc.DataError:
                raise ValueError("Too many characters for one of the wrong answers. (max: {})."
                                 .format(self.MAX_ANSWER_LENGTH))

    def _get_answers(self, q_id, conn):
        # helper method for get_questions. gets the incorrect answers for the given question
        with conn.cursor() as cursor:
            sql = """
                SELECT Answer
                FROM Answers
                WHERE QuestionID = ?
            """
            return [a[0] for a in cursor.execute(sql, q_id).fetchall()]

    def _is_duplicate(self, question):
        # helper method for add_question. checks if a given question is already in the database.
        conn = pyodbc.connect(self._conn_str())
        with conn.cursor() as cursor:
            sql = """
                SELECT QuestionID
                FROM Questions
                WHERE Question = ?
            """
            return cursor.execute(sql, question).fetchval() is not None


if __name__ == "__main__":
    pass

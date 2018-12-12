from dal import *
import pandas as pd
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, WriteError


class DbMongodb(DAL):
    """
    Implementation of the DAL using mongodb with pymongo.
    """

    def __init__(self):
        super().__init__()
        with MongoClient() as client:
            db = client['trivia']
            # creating indexes for fields that should be unique.
            # this also allows faster find operations on these fields.
            db.categories.create_index("name", unique=True)
            db.questions.create_index("question", unique=True)
            db.users.create_index("name", unique=True)

    def add_question(self, category, q_type, difficulty, question, correct_answer, wrong_answers=None):
        q = {
            "category": category,
            "type": q_type,
            "difficulty": difficulty,
            "question": question,
            "correct_answer": correct_answer
        }
        if wrong_answers:
            q["wrong_answers"] = wrong_answers
        with MongoClient() as client:
            db = client['trivia']
            self.add_category(category)
            try:
                db.questions.insert_one(q)
            except DuplicateKeyError:
                raise ValueError("Question already exists.")
            except WriteError:
                # at the time of writing this code, document validation error (jsonSchema) doesn't supply
                # additional information about the specific field that failed validation.
                # can add some checks on type and difficulty here to narrow it down
                raise ValueError("Validation failed. Check that all the parameters are valid.")

    def import_questions(self, amount=1, difficulty=None, category=None):
        # import questions from the opentdb website
        questions = super()._import_questions_from_opentdb(amount, difficulty, category)

        # add the questions to the database
        count = 0  # some questions can be duplicates so count how many were added
        for q in questions:
            try:
                self.add_question(q['category'], q['type'], q['difficulty'], q['question'],
                                  q['correct_answer'], q['incorrect_answers'])
                count += 1
            except ValueError:  # duplicate question
                pass
        return count

    def add_category(self, name):
        with MongoClient() as client:
            db = client['trivia']
            try:
                return db.categories.insert_one({"name": name}).inserted_id
            except DuplicateKeyError:
                return db.categories.find_one({"name": name})['_id']
            except WriteError:
                raise ValueError("Category name cannot be empty.")

    def remove_category(self, name):
        with MongoClient() as client:
            db = client['trivia']
            # delete records of questions answered in the given category
            records_in_category = db.users.aggregate([
                {"$unwind": "$questions"},
                {"$lookup": {
                    "from": "questions",
                    "localField": "questions.question_id",
                    "foreignField": "_id",
                    "as": "details"
                }},
                {"$unwind": "$details"},
                {"$match": {"details.category": name}},
                {"$project": {"question_id": "$questions.question_id"}},
                {"$group": {"_id": "$_id", "questions": {"$push": "$question_id"}}}
            ])
            for record in records_in_category:
                db.users.update_one(
                    {"_id": record["_id"]},
                    {"$pull": {"questions": {"question_id": {"$in": record["questions"]}}}}
                )
            # delete questions of the given category
            db.questions.delete_many({"category": name})
            # delete the category
            db.categories.delete_one({"name": name})

    def get_categories(self):
        with MongoClient() as client:
            db = client['trivia']
            return [cat['name'] for cat in db.categories.find()]

    def get_difficulties(self, category):
        with MongoClient() as client:
            db = client['trivia']
            difficulties = db.questions.distinct("difficulty", {"category": category})
            return sorted([d for d in difficulties], key=lambda x: Difficulties[x].value)

    def get_questions(self, amount, category, difficulty):
        with MongoClient() as client:
            db = client['trivia']
            questions = db.questions.aggregate([
                {"$match": {"category": category, "difficulty": difficulty}},
                {"$sample": {"size": amount}},
                {"$project": {"_id": 0, "id": "$_id", "type": 1, "question": 1, "correct_answer": 1, "wrong_answers": 1}}
            ])
            return [q for q in questions]

    def add_user(self, name):
        with MongoClient() as client:
            db = client['trivia']
            try:
                return db.users.insert_one({"name": name}).inserted_id
            except DuplicateKeyError:
                return db.users.find_one({"name": name})['_id']
            except WriteError:
                raise ValueError("Username cannot be empty.")

    def update_correct(self, question, user, correct):
        with MongoClient() as client:
            db = client['trivia']
            result = db.users.update_one({"_id": user, "questions": {"$elemMatch": {"question_id": question}}}, {
                "$set": {"questions.$.correct": correct}
            })
            if result.matched_count == 0:
                db.users.update_one({"_id": user}, {
                    "$addToSet": {"questions": {"question_id": question, "correct": correct}}
                })

    def get_results_by(self, by, order_by=None, ascending=True, limit=None):
        pipeline = [{"$unwind": "$questions"}]
        if by != 'user':
            pipeline.append({"$lookup": {
                "from": "questions",
                "localField": "questions.question_id",
                "foreignField": "_id",
                "as": "details"
            }})
            pipeline.append({"$unwind": "$details"})
            pipeline.append({"$project": {"_id": 0, f"{by}": f"$details.{by}", "questions": 1}})
        else:
            by = "name"
        pipeline.append({"$group": {
            "_id": f"${by}",
            "correct": {"$sum": "$questions.correct"},
            "incorrect": {"$sum": {"$add": [1, {"$multiply": ["$questions.correct", -1]}]}}
        }})
        pipeline.append({"$project": {
            "_id": 0,
            f"{by.capitalize()}": "$_id",
            "Correct": "$correct",
            "Incorrect": "$incorrect"}
        })
        order = order_by.capitalize() if order_by else by.capitalize()
        pipeline.append({"$sort": {f"{order}": 1 if ascending else -1}})
        if limit is not None:
            pipeline.append({"$limit": limit})

        with MongoClient() as client:
            db = client['trivia']
            results = db.users.aggregate(pipeline)
            return pd.DataFrame(list(results), columns=[by.capitalize(), "Correct", "Incorrect"])


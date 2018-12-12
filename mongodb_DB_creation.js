db = db.getSisterDB("trivia");

db.createCollection("categories", {
	validator: {
		$jsonSchema: {
			bsonType: "object",
			required: [ "name" ],
			properties: {
				name: {
					bsonType: "string",
					minLength: 1,
					description: "must be a string and is required"
				}
			}
		}
	}
});

db.createCollection("users", {
	validator: {
		$jsonSchema: {
			bsonType: "object",
			required: [ "name" ],
			properties: {
				name: {
					bsonType: "string",
					minLength: 1,
					description: "must be a string and is required"
				},
				questions: {
					bsonType: "array",
					description: "must be an array (list) and is not required"
				}
			}
		}
	}
});

db.createCollection("questions", {
	validator: {
		$jsonSchema: {
			bsonType: "object",
			required: [ "category" , "type", "difficulty", "question", "correct_answer"],
			properties: {
				category: {
					bsonType: "string",
					description: "must be a string and is required"
				},
				type: {
					enum: [ "boolean", "multiple" ],
					description: "can only be one of the enum values and is required"
				},
				difficulty: {
					enum: [ "easy", "medium", "hard" ],
					description: "can only be one of the enum values and is required"
				},
				question: {
					bsonType: "string",
					description: "must be a string and is required"
				},
				correct_answer: {
					bsonType: "string",
					description: "must be a string and is required"
				},
				wrong_answers: {
					bsonType: "array",
					description: "must be a list of unique values and is not required"
				}
			}
		}
	}
});
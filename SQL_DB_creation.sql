USE master
GO

CREATE DATABASE Trivia
GO

USE Trivia
GO

CREATE TABLE Categories (
    CategoryID INT PRIMARY KEY IDENTITY,
    CategoryName NVARCHAR(40) NOT NULL UNIQUE CHECK (LEN(CategoryName) > 0)
)
GO

CREATE TABLE Questions (
    QuestionID INT PRIMARY KEY IDENTITY,
    CategoryID INT FOREIGN KEY REFERENCES Categories(CategoryID) ON DELETE CASCADE,
    QuestionType SMALLINT NOT NULL CHECK (QuestionType IN (1, 2)),
    Difficulty SMALLINT NOT NULL CHECK (Difficulty IN (1, 2, 3)),
    Question NVARCHAR(300) NOT NULL,
    CorrectAnswer NVARCHAR(150) NOT NULL
)
GO

CREATE TABLE Answers (
    AnswerID INT PRIMARY KEY IDENTITY,
    QuestionID INT FOREIGN KEY REFERENCES Questions(QuestionID) ON DELETE CASCADE,
    Answer NVARCHAR(150) NOT NULL
)
GO

CREATE TABLE Users (
    UserID INT PRIMARY KEY IDENTITY,
    UserName NVARCHAR(15) NOT NULL UNIQUE CHECK (LEN(UserName) > 0)
)
GO

CREATE TABLE Records (
    QuestionID INT FOREIGN KEY REFERENCES Questions(QuestionID) ON DELETE CASCADE,
	UserID INT FOREIGN KEY REFERENCES Users(UserID) ON DELETE CASCADE,
    Correct SMALLINT CHECK (Correct IN (0, 1)),
    PRIMARY KEY (UserID, QuestionID)
)
GO

USE Master
GO
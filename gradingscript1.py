#!/usr/bin/env python3
"""Grading Check 1 Quiz: GitLab commit history secret.

Answers are stored only as salted PBKDF2 hashes, so they cannot be read
(or decoded) from this file. Answers are not case sensitive.
"""
import hashlib
import sys

# (question, salt, hash)
QUESTIONS = [
    (
        'What is the hash of the commit that contains the leaked secret?',
        '880b3ce40b47f8b7',
        'd2ba5d952cb823c1773c4410c3369abc073408a8ede6538e3b40627692c4e510',
    ),
    (
        'What is the value of DB_PASSWORD in the leaked commit?',
        'c0cf2bc558e28818',
        'f89c926341700f6e15f9daebae62dc382170017f554a322b9a6f7756b83275ac',
    ),
    (
        'What is the value of SECRET_KEY in the leaked commit?',
        'b1222935769533bd',
        'a0eaf0ebe5a5e4e811340538d55f8f7905ca90ea11fdb8f339964fc80cfdbd4c',
    ),
]


def check(salt, answer, expected):
    digest = hashlib.pbkdf2_hmac(
        "sha256", answer.strip().lower().encode(), bytes.fromhex(salt), 200_000
    ).hex()
    return digest == expected


def main():
    print("=" * 50)
    print(" Grading Check 1 Quiz")
    print("=" * 50)
    score = 0
    for i, (question, salt, expected) in enumerate(QUESTIONS, 1):
        print(f"\nQuestion {i}: {question}")
        answer = input("Answer: ")
        if check(salt, answer, expected):
            print("  Correct!")
            score += 1
        else:
            print("  Incorrect.")
    print(f"\nScore: {score}/{len(QUESTIONS)}")
    if score == len(QUESTIONS):
        print("All correct. You passed grading check 1!")
    else:
        print("Review the GitLab commit history and try again.")
    return 0 if score == len(QUESTIONS) else 1


if __name__ == "__main__":
    sys.exit(main())
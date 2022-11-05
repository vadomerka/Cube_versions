from data import db_session
from data.tests import Tests, TestsToUsers
from data.users import User
from data.trainers import Trainers
import datetime as dt


def create_tests():
    db_session.global_init("db/users.db")
    session = db_session.create_session()
    for t in session.query(Tests).all():
        session.delete(t)
    for t in session.query(Trainers).all():
        session.delete(t)
    tests = [(1, "иероглиф - перевод", 0, 1),
             (2, "перевод - иероглиф", 1, 0),
             (3, "картинка - иероглиф", 5, 0),
             (4, "иероглиф - картинка", 0, 5),
             (5, "иероглиф - транскрипция", 0, 2),
             (6, "транскрипция - иероглиф", 2, 0),
             (7, "транскрипция - картинка", 2, 5),
             (8, "картинка - транскрипция", 5, 2),
             (9, "словосочетание - перевод", 3, 4),
             (10, "перевод - словосочетание", 4, 3),
             (11, "аудио - иероглиф", 6, 0),
             (12, "аудио - словосочетание", 7, 3),
             (13, "общий тест", -1, -1)]

    trainers = [(1, "иероглиф - перевод", 0, 1),
             (2, "перевод - иероглиф", 1, 0),
             (3, "картинка - иероглиф", 5, 0),
             (4, "иероглиф - картинка", 0, 5),
             (5, "иероглиф - транскрипция", 0, 2),
             (6, "транскрипция - иероглиф", 2, 0),
             (7, "транскрипция - картинка", 2, 5),
             (8, "картинка - транскрипция", 5, 2),
             (9, "словосочетание - перевод", 3, 4),
             (10, "перевод - словосочетание", 4, 3),
             (11, "аудио - иероглиф", 6, 0),
             (12, "аудио - словосочетание", 7, 3)]

    for i in range(len(tests)):
        new_test = Tests(
            name=tests[i][1],
            check_side=tests[i][2],
            ans_side=tests[i][3]
        )
        session.add(new_test)
    for i in range(len(trainers)):
        new_trainer = Trainers(
            name=trainers[i][1],
            check_side=trainers[i][2],
            ans_side=trainers[i][3]
        )
        session.add(new_trainer)
    session.commit()
    session.close()

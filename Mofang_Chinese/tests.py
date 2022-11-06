from create_first_course import create_first_course, create_one_lesson
from create_first_words import create_first_words, create_one_word
from create_first_users import create_first_users, create_one_user
from create_tests import create_tests
import unittest
from requests import get, post, delete, put

root = "http://localhost:5000"


def db_sess_start_data():
    create_first_users()
    create_first_words()
    create_tests()
    create_first_course()


class Test1UserResourses(unittest.TestCase):
    def test_1_get_all_users(self):
        req = len(get(root + '/rest_users').json()["users"])
        self.assertEqual(req, 0)

    def test_2_get_wrong_user(self):
        wrong_user_id = 1000
        req = get(root + '/rest_user/' + str(wrong_user_id)).json()
        self.assertEqual(req, {'message': 'Object not found'})

    def test_3_get_user(self):
        create_one_user("test_user", "test_user@gmail.com")
        user_id = 1
        req = get(root + '/rest_user/' + str(user_id)).json()["user"]["id"]
        self.assertEqual(req, user_id)

    def test_4_delete_wrong_user(self):
        wrong_user_id = 1000
        req = delete(root + f'/rest_user/{wrong_user_id}').json()
        self.assertEqual(req, {'message': 'Object not found'})

    def test_5_delete_user(self):
        user_id = 1
        req = delete(root + f'/rest_user/{user_id}').json()
        self.assertEqual(req, {'success': 'OK'})

    def test_6_check_users_number(self):
        create_first_users()
        req = len(get(root + '/rest_users').json()["users"])
        self.assertEqual(req, 3)


class Test2DictResourses(unittest.TestCase):
    def test_1_get_all_words(self):
        req = len(get(root + '/rest_dict').json()["words"])
        self.assertEqual(req, 0)

    def test_2_get_wrong_word(self):
        wrong_id = 1000
        req = get(root + f'/rest_word/{wrong_id}').json()
        self.assertEqual(req, {'message': 'Object not found'})

    def test_3_get_word(self):
        create_one_word()
        word_id = 1
        req = get(root + f'/rest_word/{word_id}').json()["word"]["id"]
        self.assertEqual(req, word_id)

    def test_4_delete_wrong_word(self):
        wrong_id = 1000
        req = delete(root + f'/rest_word/{wrong_id}').json()
        self.assertEqual(req, {'message': 'Object not found'})

    def test_5_delete_word(self):
        word_id = 1
        req = delete(root + f'/rest_word/{word_id}').json()
        self.assertEqual(req, {'success': 'OK'})

    def test_6_check_words_number(self):
        req = len(get(root + '/rest_dict').json()["words"])
        self.assertEqual(req, 0)


class Test3WordToUserResourses(unittest.TestCase):
    def test_1_get_wrong_word_to_user(self):
        wrong_user_id = 1000
        wrong_word_id = 1000
        req = get(root + f'/rest_word_view_recording/{wrong_user_id}/{wrong_word_id}').json()
        self.assertEqual(req, {'message': 'Object not found'})

    def test_2_get_word_to_user(self):
        create_one_word()
        user_id = 1
        word_id = 1
        req = get(root + f'/rest_word_view_recording/{user_id}/{word_id}').json()["word_to_user"]
        self.assertEqual([req["users"], req["words"], req["learn_state"]],
                         [user_id, word_id, 0])

    def test_3_post_wrong_word_to_user(self):
        wrong_user_id = 1000
        wrong_word_id = 1000
        req = post(root + f'/rest_word_view_recording/{wrong_user_id}/{wrong_word_id}').json()
        self.assertEqual(req, {'message': 'Object not found'})

    def test_4_post_word_to_user(self):
        user_id = 1
        word_id = 1
        req = post(root + f'/rest_word_view_recording/{user_id}/{word_id}').json()
        self.assertEqual(req, {'success': 'OK'})

    def test_5_get_word_to_user(self):
        user_id = 1
        word_id = 1
        req = get(root + f'/rest_word_view_recording/{user_id}/{word_id}').json()["word_to_user"]
        self.assertEqual([req["users"], req["words"], req["learn_state"]],
                         [user_id, word_id, 1])

    def test_7_check_word_to_user(self):
        user_id = 1
        word_id = 1
        deleting_word = delete(root + f'/rest_word/{word_id}').json()
        req = get(root + f'/rest_word_view_recording/{user_id}/{word_id}').json()
        self.assertEqual(req, {'message': 'Object not found'})


class Test4CourseResourses(unittest.TestCase):
    def test_1_get_wrong_user_courses(self):
        wrong_id = 1000
        req = get(root + f'/rest_courses/{wrong_id}').json()
        self.assertEqual(req, {'message': 'Object not found'})

    def test_2_get_user_courses(self):
        user_id = 1
        req = len(get(root + f'/rest_courses/{user_id}').json()["courses"])
        self.assertEqual(req, 0)

    def test_3_get_wrong_course(self):
        wrong_id = 1000
        req = get(root + f'/rest_course/{wrong_id}').json()
        self.assertEqual(req, {'message': 'Object not found'})

    def test_4_get_course(self):
        create_first_course()
        course_id = 1
        req = get(root + f'/rest_course/{course_id}').json()["course"]["id"]
        self.assertEqual(req, course_id)

    def test_5_delete_wrong_course(self):
        wrong_id = 1000
        req = delete(root + f'/rest_course/{wrong_id}').json()
        self.assertEqual(req, {'message': 'Object not found'})

    def test_6_delete_course(self):
        course_id = 1
        req = delete(root + f'/rest_course/{course_id}').json()
        self.assertEqual(req, {'success': 'OK'})

    def test_7_check_courses_number(self):
        user_id = 1
        req = len(get(root + f'/rest_courses/{user_id}').json()["courses"])
        self.assertEqual(req, 1)


class Test5LessonResourses(unittest.TestCase):
    def test_1_get_all_lessons(self):
        req = len(get(root + f'/rest_lessons').json()["lessons"])
        self.assertEqual(req, 0)

    def test_2_get_wrong_user_lessons(self):
        wrong_user_id = 1000
        req = get(root + f'/rest_user_lessons/{wrong_user_id}').json()
        self.assertEqual(req, {"message": "Object not found"})

    def test_3_get_user_lessons(self):
        create_one_lesson()
        user_id = 1
        req = len(get(root + f'/rest_user_lessons/{user_id}').json()["user_lessons"])
        self.assertEqual(req, 1)

    def test_4_get_wrong_lesson(self):
        wrong_id = 1000
        req = get(root + f'/rest_lesson/{wrong_id}').json()
        self.assertEqual(req, {'message': 'Object not found'})

    def test_5_get_lesson(self):
        lesson_id = 1
        req = get(root + f'/rest_lesson/{lesson_id}').json()["lesson"]["id"]
        self.assertEqual(req, lesson_id)

    def test_6_delete_wrong_lesson(self):
        wrong_id = 1000
        req = delete(root + f'/rest_lesson/{wrong_id}').json()
        self.assertEqual(req,  {'message': 'Object not found'})

    def test_7_delete_lesson(self):
        lesson_id = 1
        req = delete(root + f'/rest_lesson/{lesson_id}').json()
        self.assertEqual(req, {'success': 'OK'})

    def test_8_check_lessons_number(self):
        req = len(get(root + f'/rest_lessons').json()["lessons"])
        self.assertEqual(req, 0)


if __name__ == '__main__':
    unittest.main()

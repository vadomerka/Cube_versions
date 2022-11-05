from create_first_course import create_first_course
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
        self.assertEqual(req, {'message': 'Object not found', 'id': wrong_user_id})

    def test_3_get_user(self):
        create_one_user("test_user", "test_user@gmail.com")
        user_id = 1
        req = get(root + '/rest_user/' + str(user_id)).json()["user"]["id"]
        self.assertEqual(req, user_id)

    def test_4_delete_wrong_user(self):
        wrong_user_id = 1000
        req = delete(root + f'/rest_user/{wrong_user_id}').json()
        self.assertEqual(req,  {'message': 'Object not found', 'id': wrong_user_id})

    def test_5_delete_user(self):
        user_id = 1
        req = delete(root + f'/rest_user/{user_id}').json()
        self.assertEqual(req, {'success': 'OK'})

    def test_6_check_users_number(self):
        create_first_users()
        req = len(get(root + '/rest_users').json()["users"])
        self.assertEqual(req, 2)


class Test2DictResourses(unittest.TestCase):
    def test_1_get_all_words(self):
        req = len(get(root + '/rest_dict').json()["words"])
        self.assertEqual(req, 0)

    def test_2_get_wrong_word(self):
        wrong_id = 1000
        req = get(root + f'/rest_word/{wrong_id}').json()
        self.assertEqual(req, {'message': 'Object not found', 'id': wrong_id})

    def test_3_get_word(self):
        create_one_word()
        word_id = 1
        # print(get(root + f'/rest_word/{word_id}').json())
        req = get(root + f'/rest_word/{word_id}').json()["word"]["id"]
        self.assertEqual(req, word_id)

    def test_4_delete_wrong_word(self):
        wrong_id = 1000
        req = delete(root + f'/rest_word/{wrong_id}').json()
        self.assertEqual(req,  {'message': 'Object not found', 'id': wrong_id})

    def test_5_delete_word(self):
        word_id = 1
        req = delete(root + f'/rest_word/{word_id}').json()
        self.assertEqual(req, {'success': 'OK'})

    def test_6_check_words_number(self):
        req = len(get(root + '/rest_dict').json()["words"])
        self.assertEqual(req, 0)


class Test3CourseResourses(unittest.TestCase):
    def test_1_get_user_courses(self):
        user_id = 1
        req = len(get(root + f'/rest_courses/{user_id}').json()["courses"])
        self.assertEqual(req, 0)

    def test_2_get_wrong_course(self):
        wrong_id = 1000
        req = get(root + f'/rest_course/{wrong_id}').json()
        self.assertEqual(req, {'message': 'Object not found', 'id': wrong_id})

    def test_3_get_course(self):
        create_first_course()
        course_id = 1
        req = get(root + f'/rest_course/{course_id}').json()["course"]["id"]
        self.assertEqual(req, course_id)

    def test_4_delete_wrong_course(self):
        wrong_id = 1000
        req = delete(root + f'/rest_course/{wrong_id}').json()
        self.assertEqual(req,  {'message': 'Object not found', 'id': wrong_id})

    def test_5_delete_word(self):
        course_id = 1
        req = delete(root + f'/rest_course/{course_id}').json()
        self.assertEqual(req, {'success': 'OK'})

    def test_6_check_words_number(self):
        user_id = 1
        req = len(get(root + f'/rest_courses/{user_id}').json()["courses"])
        self.assertEqual(req, 0)


"""
class TestCourseResourses(unittest.TestCase):
    def test_1empty_post_course(self):
        self.assertEqual(post('http://localhost:5000/rest_courses/1').json(),
                         {'error': 'Empty request'})

    def test_2bad_post_course(self):
        self.assertEqual(post('http://localhost:5000/rest_courses/1', json={'id': 2}).json(),
                         {'error': 'Bad request'})

    def test_3post_course(self):
        self.assertEqual(post('http://localhost:5000/rest_courses/1',
                              json={'name': 'post course',
                                    'about': "1"}).json(), {'success': 'OK'})

    def test_4get_course_1(self):
        # session = db_session.create_session()
        # id = max([c.id for c in session.query(Courses)])
        self.assertEqual(get('http://localhost:5000/rest_course/' + str(id)).json(),
                         {'course': {'about': '1', 'id': id, 'lessons': [], 'name': 'post course'}})

    def test_5delete_course(self):
        # session = db_session.create_session()
        # id = max([c.id for c in session.query(Courses)])
        self.assertEqual(delete('http://localhost:5000/rest_course/' + str(id)).json(),
                         {'success': 'OK'})

    def test_6get_course_2(self):
        # session = db_session.create_session()
        # id = max([c.id for c in session.query(Courses)])
        self.assertEqual(get('http://localhost:5000/rest_course/' + str(id)).json(),
                         {'message': 'Course ' + str(id) + ' not found'})
"""
if __name__ == '__main__':
    unittest.main()


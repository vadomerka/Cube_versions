import unittest
from requests import get, post, delete, put

id = 13


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


if __name__ == '__main__':
    unittest.main()

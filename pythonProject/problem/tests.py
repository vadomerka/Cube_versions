import unittest
from requests import get, post, delete, put


class TestCourseResourses(unittest.TestCase):
    def test_empty_post_course(self):
        assert post('http://localhost:5000/rest_courses/1').json() == {'error': 'Empty request'}

    def test_bad_post_course(self):
        assert post('http://localhost:5000/rest_courses/1', json={'id': 2}).json() == {
            'error': 'Bad request'}

    def test_post_course(self):
        self.assertEqual(post('http://localhost:5000/rest_courses/1',
                              json={'name': 'post course',
                                    'about': "1"}).json(), {'success': 'OK'})

    def test_delete_course(self):
        self.assertEqual(get('/rest_courses/1',
                              json={'name': 'post course',
                                    'about': "1"}).json(), {'success': 'OK'})
        # with self.assertRaises(TypeError):
        #     reverse(42)


if __name__ == '__main__':
    unittest.main()

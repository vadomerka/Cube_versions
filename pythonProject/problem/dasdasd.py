import unittest
from requests import get, post, delete, put

print(post('http://localhost:5000/rest_dict',
           json={'id': 2,
                 'translation': "a"}).json())


class TestDictResourses(unittest.TestCase):
    def test_1get_dict(self):
        self.assertEqual(get('http://localhost:5000/rest_dict').json(), {'words': [
            {'author': 1, 'down_side': '1_down.png', 'front_side': '1_front.png',
             'front_side_audio': None, 'hieroglyph': '你', 'id': 1, 'left_side': '1_left.png',
             'right_side': '1_right.png', 'right_side_audio': '1_trans_audio.mp3',
             'translation': 'ты', 'up_side': '1_up.png', 'up_side_audio': '1_phrase_audio.mp3'},
            {'author': 1, 'down_side': '1_down.png', 'front_side': '1_front.png',
             'front_side_audio': None, 'hieroglyph': 'иероглиф 2', 'id': 2,
             'left_side': '1_left.png', 'right_side': '1_right.png',
             'right_side_audio': '1_trans_audio.mp3', 'translation': 'перевод 3',
             'up_side': '1_up.png', 'up_side_audio': '1_phrase_audio.mp3'}]}
                         )

    def test_2empty_post_dict(self):
        self.assertEqual(post('http://localhost:5000/rest_dict').json(), {'error': 'Empty request'})

    def test_3bad_post_dict(self):
        self.assertEqual(post('http://localhost:5000/rest_dict',
                              json={'id': 2,
                                    'translation': "a"}).json(), {'error': 'Bad request'})

    def test_4post_dict(self):
        self.assertEqual(post('http://localhost:5000/rest_dict/',
                              json={"id": 4,
                                    "hieroglyph": "post word",
                                    "tranlation": "post word",
                                    "front_side": "post word",
                                    "left_side": "post word",
                                    "right_side": "post word",
                                    "up_side": "post word",
                                    "down_side": "post word",
                                    "front_side_audio": "post word",
                                    "right_side_audio": "post word",
                                    "up_side_audio": "post word"
                                    }).json(), {'success': 'OK'})

    def test_5get_word(self):
        print(get('http://localhost:5000/rest_dict/4'))
        self.assertEqual(get('http://localhost:5000/rest_dict/4'), {'success': 'OK'})

    def test_6delete_dict(self):
        self.assertEqual(get('/rest_dict/1',
                             json={'name': 'post course',
                                   'about': "1"}).json(), {'success': 'OK'})

    def test_7get_word(self):
        self.assertEqual(get('http://localhost:5000/rest_dict/4'), {'success': 'OK'})


if __name__ == '__main__':
    unittest.main()

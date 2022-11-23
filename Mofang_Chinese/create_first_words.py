from data import db_session
from data.courses import Courses, users_to_course
from data.words import Words, WordsToUsers
from data.users import User
import datetime as dt


def create_first_words():
    db_session.global_init("db/users.db")
    session = db_session.create_session()
    new_words = [
        ("你", "ты", "Nǐ", "你好", "Здравствуйте"),
        ("好", "хорошо", "hǎo", "你好", "Здравствуйте"),
        ("我", "я", "Wǒ", "我很好", "у меня все очень хорошо"),
        ("很", "очень", "Hěn", "我很好", "у меня все очень хорошо"),
        ("也", "тоже", "Yě", "妈妈也很好", "у мамы тоже все хорошо"),
        ("忙", "занятой", "máng", "我很忙", "я очень занят"),
        ("不", "нет", "Bù", "我不忙", "я не занят"),
        ("哥哥", "старший брат", "Gēgē", "你哥哥忙吗？", "твой старший брат занят?"),
        ("弟弟", "младший брат", "Dìdì", "你弟弟忙吗？", "твой младший брат занят?"),
        ("他", "он", "Tā", "他很忙？", "он занят?"),
        ("她", "она", "Tā", "我不是她哥哥，我是她朋友。", "я не ее старший брат, я ее друг"),
        ("他们", "они", "Tāmen", "他们也不忙。", "они тоже не заняты"),
        ("都", "все", "dōu", "他们都很忙", "все они все очень заняты"),
        ("这", "это", "Zhè", "这是他弟弟吗？", "это его младший брат?"),
        ("是", "быть", "shì", "那是你爸爸吗？", "это твой папа?"),
        ("朋友", "друг", "Péngyǒu", "你朋友好吗？", "как дела у твоего друга?"),
        ("爸爸", "папа", "Bàba", "我爸爸很忙", "мой папа очень занят"),
        ("妈妈", "мама", "Māmā", "妈妈很好，你好吗？", "у мамы все хорошо, а как ты?"),
        ("你们", "вы", "Nǐmen", "你们忙吗？", "вы заняты?"),
        ("大夫", "доктор", "Dàfū", "爸爸的大夫", "доктор отца"),
        ("车", "машина", "Chē", "这不是弟弟的车，这是哥哥的车。",
         "Это не машина моего брата, это машина младшего брата."),
        ("那", "тот", "Nà", "那不是我的车", "то не моя машина"),
        ("书", "книга", "Shū", "大夫的书", "книга доктора"),
        ("是", "да, так,  правильно", "Shì", "是，这是我妈妈", "да, это моя мама"),
        ("报纸", "газета", "Bàozhǐ", "她朋友的报纸", "Газета ее приятеля"),
        ("尺", "линейка", "Chǐ", "他们哥哥的尺", "линейка их старшего брата"),
        ("笔", "карандаш", "Bǐ", "我们的笔", "наша ручка"),
        ("哪", "какой", "Nǎ", "他爸爸是哪国人？", "из какой страны его отец?"),
        ("国", "страна", "Guó", "回国", "вернуться в страну"),
        ("人", "человек", "Rén", "忙人", "занятой человек"),
        ("谁", "кто", "Shéi", "谁的报纸", "чья-то газета"),
        ("我们", "мы", "Wǒmen", "我们的报纸", "наша газета")]

    author = session.query(User).filter(User.teacher == 1).all()[-1].id
    for i in range(len(new_words)):
        new_word = Words(author=author,
                         hieroglyph=new_words[i][0],
                         translation=new_words[i][1],
                         transcription=new_words[i][2],
                         phrase_ch=new_words[i][3],
                         phrase_ru=new_words[i][4],
                         image="undefined_image.png",
                         front_side_audio="undefined_trans_audio.mp3",
                         left_side_audio="undefined_phrase_audio.mp3",
                         right_side_audio="undefined_trans_audio.mp3",
                         up_side_audio="undefined_phrase_audio.mp3",
                         down_side_audio="undefined_translation_audio.mp3",
                         creation_time=dt.datetime.now()
                         )
        cur_user = session.query(User).get(author)
        cur_user.words.append(new_word)
        for user in session.query(User).all():
            session.add(WordsToUsers(
                words=new_word.id,
                users=user.id,
                learn_state=0
            ))
        session.commit()
    # empty_word = Words()
    # cur_user = session.query(User).get(author)
    # cur_user.words.append(empty_word)
    session.commit()
    session.close()


def create_one_word():
    db_session.global_init("db/users.db")
    session = db_session.create_session()
    # print(session.query(User).filter(User.teacher == 1).all())
    author = session.query(User).filter(User.teacher == 1).all()[-1].id
    new_word = ("你", "ты", "Nǐ", "你好", "Здравствуйте")
    new_word = Words(author=author,
                     hieroglyph=new_word[0],
                     translation=new_word[1],
                     transcription=new_word[2],
                     phrase_ch=new_word[3],
                     phrase_ru=new_word[4],
                     image="undefined_image.png",
                     front_side_audio="undefined_trans_audio.mp3",
                     left_side_audio="undefined_phrase_audio.mp3",
                     right_side_audio="undefined_trans_audio.mp3",
                     up_side_audio="undefined_phrase_audio.mp3",
                     down_side_audio="undefined_translation_audio.mp3",
                     creation_time=dt.datetime.now())
    cur_user = session.query(User).get(author)
    cur_user.words.append(new_word)
    for user in session.query(User).all():
        session.add(WordsToUsers(
            words=new_word.id,
            users=user.id,
            learn_state=0
        ))
    session.commit()
    session.close()
    
    
if __name__ == '__main__':
    create_first_words()

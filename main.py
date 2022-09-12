
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import os
import speech_recognition as sr
import sys
import time
import pydub
import shutil
import json
from speech_recognition import UnknownValueError
import datetime
from vosk import KaldiRecognizer, Model
import wave

class Word:
    '''Класс для Vosk'''

    def __init__(self, dict):

        self.conf = dict["conf"]
        self.end = dict["end"]
        self.start = dict["start"]
        self.word = dict["word"]

    def to_string(self):
        ''' Returns a string describing this instance '''
        return "{:20} с {:.2f} секунд по {:.2f} секунд, чистота {:.2f}%".format(
            self.word, self.start, self.end, self.conf*100)


class AudioJson:
    """
    Данный класс создан для распознования текста из файлов .wav в recognized.json
    Включает в себя разные методы, которые являются приватными, но к использованию настоятельно рекомендуется использования метода main()
    """


    def __init__(
        self, 
        file_name: str,
        separate_count: int=3, 
        min_silence_len: int=1000, 
        silence_thresh: int=-30, 
        seek_step: int=100, 
        threshold: int=100
        ) -> None:

        self.file_name = file_name
        self.separate_count = int(separate_count)
        self.min_silence_len = min_silence_len
        self.silence_thresh = silence_thresh
        self.seek_step = seek_step
        self.threshold = threshold


    def __get_time(self) -> float:
        """
        Получает объект времени
        """
        return time.time()


    def __delete_and_create_temp(self) -> None:
        """
        Удаляет и создает папку temp
        """
        shutil.rmtree('temp', ignore_errors=True)
        os.mkdir('temp')


    def __mp3_convert_to_wav(self):
        """
        Конвертирует .mp3 файл в .wav файл
        """
        sound = AudioSegment.from_mp3(f'audio/{self.file_name}')
        file_wav_name = self.file_name.replace('.mp3', '.wav')
        sound.export(f'audio/file_wav_name', format="wav")


    def return_format_of_track(self) -> str:
        """
        Возвращает формат трека, который был передан как аргумент в консоли
        """
        return self.file_name.split('.')[-1]


    def _return_sound_object_of_track(self) -> object:
        """
        Возвращает звуковой объект обработки трека
        """
        return AudioSegment.from_file(f'audio/{self.file_name}')


    def _export_file_of_track(self, audio_file: object, count: int, from_: int, to_: int) -> None:
        """
        Экспортирует файл в папку temp
        """
        return audio_file.export(f'temp/{count}_{from_}_{to_}_{self.file_name}', format=self.return_format_of_track())


    def return_temp_dir(self) -> list:
        """
        Возвращает содержимое папки temp
        """
        return os.listdir('temp')


    def write_json(self, json_list: list) -> None:
        """
        Записывает в файл recognized.json итоги распознавания речи
        """
        with open('recognized.json', 'w', encoding='utf-8') as file:
            json.dump(json_list, fp=file, indent=4, ensure_ascii=False, sort_keys=True)


    def export_nonsilent_pieces_of_track(self) -> None:
        """
        Экспортирует те части трека, которые включают в себя какой-либо звук для более быстрого распознавания речи
        """
        sound = self._return_sound_object_of_track()
        pieces = detect_nonsilent(sound, min_silence_len=self.min_silence_len, silence_thresh=self.silence_thresh, seek_step=self.seek_step)
        count = 0
        for piece in pieces:
            print(piece)
            count += 1
            from_ = piece[0]//1000
            to_ = piece[1]//1000
            piece_sound_object = sound[piece[0]:piece[1]]
            self._export_file_of_track(audio_file=piece_sound_object, count=count, from_=from_, to_=to_)
        

    def delete_track(self, file_name) -> None:
        """
        Удаляет трек
        """
        os.remove(f'temp/{file_name}')


    def export_with_separator(self) -> None:
        """
        Разделяет имеющиеся треки на делитель 
        """
        files = self.return_temp_dir()
        for file in files:
            file_values_list = file.split('_')
            lenght_of_file = int(file_values_list[2]) - int(file_values_list[1])
            max_ = int(file_values_list[2])
            if self.separate_count < lenght_of_file:
                self.delete_track(file)
                from_ = int(file_values_list[1])
                to_ = int(file_values_list[1]) + self.separate_count
                while from_ < max_:
                    lenght_of_file_1 = from_
                    lenght_of_file_2 = to_
                    lenght_of_file_piece_1 = from_*1000
                    lenght_of_file_piece_2 = to_*1000
                    sound = self._return_sound_object_of_track()
                    piece_sound_object = sound[lenght_of_file_piece_1:lenght_of_file_piece_2]
                    self._export_file_of_track(audio_file=piece_sound_object, count=file_values_list[0], from_=lenght_of_file_1, to_=lenght_of_file_2)
                    from_ += self.separate_count
                    to_ += self.separate_count
        


    def __time_convert(self, seconds: int) -> str:
        """
        Преобразует секунды в нормальное время        
        """
        return str(datetime.timedelta(seconds=int(seconds)))


    def make_json_list(self) -> list:
        """
        Возвращает список для последующего преобразования в recognized.json
        """
        files = self.return_temp_dir()
        json_list = []
        recognizer = sr.Recognizer()
        recognizer.pause_threshold = 1
        for file in files:
            json_dict = {}
            with sr.AudioFile(f'temp/{file}') as source:
                recognizer.adjust_for_ambient_noise(source)
                audio_data = recognizer.record(source)
                try:
                    text = recognizer.recognize_google(audio_data=audio_data, language='ru-RU', show_all=True)
                except UnknownValueError:
                    text = '...'
                file_values_list = file.split('_')
                json_dict['value'] = file_values_list[0]
                json_dict['from'] = self.__time_convert(seconds=file_values_list[1])
                json_dict['to'] = self.__time_convert(seconds=file_values_list[2])
                json_dict['file'] = file_values_list[3]
                json_dict['text'] = text
                json_list.append(json_dict) 
        return json_list


    def make_json_vosk_list(self) -> list: 
        """
        Возвращает список для последующего преобразования в recognized.json
        """
        path_model = os.getcwd() + r'\vosk-model-small-ru-0.22'
        model = Model(path_model)
        files = self.return_temp_dir()
        for file in files:
            print(file)
            wf = wave.open(f'temp/{file}', "rb")
            rec = KaldiRecognizer(model, wf.getframerate())
            rec.SetWords(True)

            # get the list of JSON dictionaries
            results = []
            # recognize speech using vosk model
            while True:
                data = wf.readframes(16000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    part_result = json.loads(rec.Result())
                    results.append(part_result)
            part_result = json.loads(rec.FinalResult())
            results.append(part_result)

            # convert list of JSON dictionaries to list of 'Word' objects
            list_of_words = []
            for sentence in results:
                if len(sentence) == 1:
                    # sometimes there are bugs in recognition 
                    # and it returns an empty dictionary
                    # {'text': ''}
                    continue
                for obj in sentence['result']:
                    w = Word(obj)  # create custom Word object
                    list_of_words.append(w)  # and add it to list

            wf.close()  # close audiofile

            # output to the screen
            for word in list_of_words:
                print(word.to_string())
    

    def main(self) -> None:
        """
        Собирает все методы класса и создает файл recognized.json
        """
        time_before = self.__get_time()
        self.__mp3_convert_to_wav()
        self.export_nonsilent_pieces_of_track()
        # self.export_with_separator()
        self.make_json_vosk_list()
        self.make_json_list()
        self.write_json(self.make_json_list())
        self.__delete_and_create_temp()
        time_now = self.__get_time()
        return time_now-time_before

        

if __name__ == "__main__":
    pydub.AudioSegment.converter = r"C:\\ffmpeg\\bin\\ffprobe.exe"                 
    pydub.AudioSegment.ffmpeg = r"C:\\ffmpeg\\bin\\ffmpeg.exe"   
    file_name = sys.argv[1]
    audio_json_object = AudioJson(file_name=file_name)
    print(audio_json_object.main())
    
import nltk
import requests
import json
import random
import os
from os import path
from bs4 import BeautifulSoup
import time
from flask import Flask
from flask_cors import CORS, cross_origin
import configparser
import conf
import pickle

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

class Song:

    def __init__(self, title, author, genius_access_token):
        self.all_feature_dicts = {}
        self.final_tags = {}
        res = requests.get('http://api.genius.com/search?q=' + author + " " + title,
                           headers={'Authorization': 'BEARER ' + genius_access_token})
        data = json.loads(res.text)
        search_results = data['response']['hits']
        selected_song = search_results[0]
        self.genius_id = selected_song['result']['id']
        self.author = selected_song['result']['primary_artist']['name']
        self.title = selected_song['result']['title']
        self.url = 'http://www.genius.com' + selected_song['result']['path']

        song_res = requests.get('http://www.genius.com' + selected_song['result']['path'])
        song_html = BeautifulSoup(song_res.text, 'html.parser')
        [script.extract() for script in song_html('script')]

        lyrics = [result for result in song_html.find_all('div')]
        filtered_lyrics = filter(lambda x: 'class' in x.attrs.keys() and 'Lyrics' in x.attrs['class'][0], lyrics)
        lyrics = ' '.join([lyric.get_text() for lyric in filtered_lyrics])
        self.lyrics = nltk.word_tokenize(lyrics)
        self.generate_all_features()

    def generate_all_features(self):
        tags = ['profanity', 'drugs', 'violence', 'sexual references']
        [self.generate_feature_specific(tag) for tag in tags]

    def generate_feature_specific(self, tag: str):
        stemmer = nltk.stem.porter.PorterStemmer()
        stems = [stemmer.stem(word) for word in self.lyrics]
        curse_words_mild = ["hell", "damn", "ass"]
        curse_words_medium = ["shit", "bitch", "asshole"]
        curse_words_intense = ["fuck", "bastard", "cunt", "whore", "nigger", "nigga"]
        drug_list_mild = ["hit", "pop", "smoke", "pot", "pill", "puff", "withdrawal", "lace", "high"]
        drug_list_medium = ["weed", "marijuana", "cannabis", "mary jane", "snort", "haze", "powder", "blunt", "dealer"]
        drug_list_intense = ["drug", "cocaine", "coke", "heroine", "xan", "acid"]
        violence_list_mild = ["punch", "hit", "beat", "shot", "slap", "gang"]
        violence_list_medium = ["shoot", "rob", "stab", "gun", "glock", "knife", "bullet"]
        violence_list_intense = ["kill", "murder", "suicide", "homocide", "death", "die", "dead", "rape"]
        sexual_list_mild = ["nut", "balls", "hickey", "ride", "bite", "body", "ass"]
        sexual_list_medium = ["suck", "ho", "hoe", "thot", "fuck", "sex", "vibrator", "horny", "tits", "titties"]
        sexual_list_intense = ["pussy", "dick", "cock", "whore", "clit", "porn"]

        feature_dict = {}
        if tag == "profanity":
            curse_count = 0
            curse_values = []
            for word in curse_words_mild:
                count = max(self.lyrics.count(word), stems.count(word))
                curse_values.append(count * 0.2)
                curse_count += count
            for word in curse_words_medium:
                count = max(self.lyrics.count(word), stems.count(word))
                curse_values.append(count * 0.5)
                curse_count += count
            for word in curse_words_intense:
                count = max(self.lyrics.count(word), stems.count(word))
                curse_values.append(count * 1.0)
                curse_count += count
            curse_total = sum(curse_values)
            feature_dict["num_curse_words"] = curse_count
            feature_dict["weighted_curse_sum"] = curse_total
            feature_dict["absent(curse)"] = curse_total == 0
            feature_dict["few(curse)"] = 0 < curse_total < 5
            feature_dict["many(curse)"] = curse_total >= 5

        elif tag == "drugs":
            drug_count = 0
            drug_values = []
            for drug in drug_list_mild:
                count = max(self.lyrics.count(drug), stems.count(drug))
                drug_values.append(count * 0.2)
                drug_count += count
            for drug in drug_list_medium:
                count = max(self.lyrics.count(drug), stems.count(drug))
                drug_values.append(count * 0.5)
                drug_count += count
            for drug in drug_list_intense:
                count = max(self.lyrics.count(drug), stems.count(drug))
                drug_values.append(count * 1.0)
                drug_count += count
            drug_total = sum(drug_values)
            feature_dict["num_drug_words"] = drug_count
            feature_dict["weighted_drug_sum"] = drug_total
            feature_dict["absent(drugs)"] = drug_total == 0
            feature_dict["few(drugs)"] = 0 < drug_total < 3
            feature_dict["many(drugs)"] = drug_total >= 3

        elif tag == "violence":
            violence_count = 0
            violence_values = []
            for element in violence_list_mild:
                count = max(self.lyrics.count(element), stems.count(element))
                violence_values.append(count * 0.2)
                violence_count += count
            for element in violence_list_medium:
                count = max(self.lyrics.count(element), stems.count(element))
                violence_values.append(count * 0.5)
                violence_count += count
            for element in violence_list_intense:
                count = max(self.lyrics.count(element), stems.count(element))
                violence_values.append(count * 1.0)
                violence_count += count
            violence_total = sum(violence_values)
            feature_dict["num_violence_words"] = violence_count
            feature_dict["weighted_violence_sum"] = violence_total
            feature_dict["absent(violence)"] = violence_total == 0
            feature_dict["few(violence)"] = 0 < violence_total < 5
            feature_dict["many(violence)"] = violence_total >= 5

        elif tag == "sexual references":
            ref_count = 0
            ref_values = []
            for term in sexual_list_mild:
                count = max(self.lyrics.count(term), stems.count(term))
                ref_values.append(count * 0.2)
                ref_count += count
            for term in sexual_list_medium:
                count = max(self.lyrics.count(term), stems.count(term))
                ref_values.append(count * 0.5)
                ref_count += count
            for term in sexual_list_intense:
                count = max(self.lyrics.count(term), stems.count(term))
                ref_values.append(count * 1.0)
                ref_count += count
            ref_total = sum(ref_values)
            feature_dict["num_ref_words"] = ref_count
            feature_dict["weighted_ref_sum"] = ref_total
            feature_dict["absent(sexual references)"] = ref_total == 0
            feature_dict["few(sexual references)"] = 0 < ref_total < 2
            feature_dict["many(sexual references)"] = ref_total >= 2
        else:
            print("please input valid tag")

        self.all_feature_dicts[tag] = feature_dict

    def get_features(self, tag: str):
        return self.all_feature_dicts[tag]

    def assign(self, tag_type: str, severity: str):
        self.final_tags[tag_type] = severity

    def get_final_tags(self):
        return self.final_tags


class TagClassifier:
    def __init__(self, tag: str, intensity_tags: list):  # intensity is a list of tuples (song, intensity of chosen tag)
        self.target_tag = tag
        self.tagged_songs = intensity_tags
        self.training_set = [(song.get_features(self.target_tag), intensity) for (song, intensity) in self.tagged_songs]
        self.classifier = nltk.NaiveBayesClassifier.train(self.training_set)

    def predict(self, curr_song: Song) -> str:  # output is the intensity of the target tag within the lyrics
        result = self.classifier.classify(curr_song.get_features(self.target_tag))
        return result

    def assign(self, curr_song: Song):
        curr_song.assign(self.target_tag, self.predict(curr_song))

    def tag_type(self):
        return self.target_tag


def demo_trained_classifiers(api_key) -> []:
    # format for a song
    # {'title': '', 'artist': '',
    #  'tags': {'profanity': '', 'drugs': '', 'violence': '', 'sexual references': ''}}
    if (path.exists('pickle/classifiers.pkl')):
        pklfile = open('pickle/classifiers.pkl', 'rb')
        classifiers = pickle.load(pklfile)
        pklfile.close()
        return classifiers
    song_metadata_list = [
        {'title': "WAP", 'artist': "Cardi B",
         'tags': {'profanity': 'frequent', 'drugs': 'some', 'violence': 'none', 'sexual references': 'frequent'}},
        {'title': 'Lucy in the Sky with Diamonds', 'artist': 'The Beatles',
         'tags': {'profanity': 'none', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
        {'title': "God's Plan", 'artist': 'Drake',
         'tags': {'profanity': 'some', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'Marijuana', 'artist': 'Kid Cudi',
         'tags': {'profanity': 'some', 'drugs': 'frequent', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'I Know', 'artist': 'Jay Z',
         'tags': {'profanity': 'none', 'drugs': 'some', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'The Race', 'artist': 'Tay-K',
         'tags': {'profanity': 'frequent', 'drugs': 'none', 'violence': 'frequent', 'sexual references': 'some'}},
        {'title': 'I See the Light', 'artist': 'Mandy Moore & Zachary Levi',
         'tags': {'profanity': 'none', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'Stargazing', 'artist': 'Travis Scott',
         'tags': {'profanity': 'some', 'drugs': 'frequent', 'violence': 'none', 'sexual references': 'some'}},
        {'title': 'Headshot', 'artist': 'Lil Tjay',
         'tags': {'profanity': 'some', 'drugs': 'frequent', 'violence': 'some', 'sexual references': 'frequent'}},
        {'title': 'Next Right Thing', 'artist': 'Kristen Bell',
         'tags': {'profanity': 'none', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'Rapstar', 'artist': 'Polo G',
         'tags': {'profanity': 'frequent', 'drugs': 'none', 'violence': 'some', 'sexual references': 'frequent'}},
        {'title': 'Montero (Call Me By Your Name)', 'artist': 'Lil Nas X',
         'tags': {'profanity': 'frequent', 'drugs': 'some', 'violence': 'none', 'sexual references': 'some'}},
        {'title': 'Leave the Door Open', 'artist': 'Silk Sonic',
         'tags': {'profanity': 'none', 'drugs': 'some', 'violence': 'none', 'sexual references': 'some'}},
        {'title': 'Up', 'artist': 'Cardi B',
         'tags': {'profanity': 'frequent', 'drugs': 'some', 'violence': 'none', 'sexual references': 'frequent'}},
        {'title': 'Drivers License', 'artist': 'Olivia Rodrigo',
         'tags': {'profanity': 'some', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'Forever After All', 'artist': 'Luke Combs',
         'tags': {'profanity': 'none', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'The Good Ones', 'artist': 'Gabby Barrett',
         'tags': {'profanity': 'none', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'Titanium', 'artist': 'Dave',
         'tags': {'profanity': 'some', 'drugs': 'none', 'violence': 'some', 'sexual references': 'frequent'}},
        {'title': '34+35', 'artist': 'Ariana Grande',
         'tags': {'profanity': 'frequent', 'drugs': 'none', 'violence': 'none', 'sexual references': 'frequent'}},
        {'title': 'Therefore I Am', 'artist': 'Billie Eilish',
         'tags': {'profanity': 'some', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'Made for You', 'artist': 'Jake Owen',
         'tags': {'profanity': 'none', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'Streets', 'artist': 'Doja Cat',
         'tags': {'profanity': 'some', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'Street Runner', 'artist': 'Rod Wave',
         'tags': {'profanity': 'some', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'What’s Your Country Song', 'artist': 'Thomas Rhett',
         'tags': {'profanity': 'none', 'drugs': 'none', 'violence': 'some', 'sexual references': 'none'}},
        {'title': 'Hell of a View', 'artist': 'Eric Church',
         'tags': {'profanity': 'some', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'Somebody Like That', 'artist': 'Demi Pallas',
         'tags': {'profanity': 'none', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'Hold On', 'artist': 'Justin Bieber',
         'tags': {'profanity': 'none', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'Monsters', 'artist': 'All Time Low',
         'tags': {'profanity': 'frequent', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'Dancing With The Devil', 'artist': 'Demi Lovato',
         'tags': {'profanity': 'none', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'Gone', 'artist': 'Dierks Bentley',
         'tags': {'profanity': 'none', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'Suge', 'artist': 'DaBaby',
         'tags': {'profanity': 'frequent', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'MIDDLE CHILD', 'artist': 'J. Cole',
         'tags': {'profanity': 'frequent', 'drugs': 'some', 'violence': 'some', 'sexual references': 'some'}},
        {'title': 'Ransom', 'artist': 'Lil Tecca',
         'tags': {'profanity': 'frequent', 'drugs': 'none', 'violence': 'frequent', 'sexual references': 'none'}},
        {'title': 'Better Now', 'artist': 'Post Malone',
         'tags': {'profanity': 'some', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'Money', 'artist': 'Cardi B',
         'tags': {'profanity': 'frequent', 'drugs': 'none', 'violence': 'some', 'sexual references': 'frequent'}},
        {'title': 'Panini', 'artist': 'Lil Nas X',
         'tags': {'profanity': 'none', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'a lot', 'artist': '21 Savage',
         'tags': {'profanity': 'frequent', 'drugs': 'none', 'violence': 'some', 'sexual references': 'some'}},
        {'title': 'Lucid Dreams', 'artist': 'Juice WRLD',
         'tags': {'profanity': 'none', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'Mo Bamba', 'artist': 'Sheck Wes',
         'tags': {'profanity': 'frequent', 'drugs': 'none', 'violence': 'none', 'sexual references': 'frequent'}},
        {'title': 'Envy Me', 'artist': 'Calboy',
         'tags': {'profanity': 'frequent', 'drugs': 'some', 'violence': 'some', 'sexual references': 'none'}},
        {'title': 'Trampoline', 'artist': 'Shaed',
         'tags': {'profanity': 'none', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
        {'title': '3AM', 'artist': 'Russ',
         'tags': {'profanity': 'some', 'drugs': 'none', 'violence': 'none', 'sexual references': 'some'}},
        {'title': 'Life’s a Mess', 'artist': 'Juice WRLD & Halsey',
         'tags': {'profanity': 'some', 'drugs': 'some', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'Best Friend', 'artist': 'Rex Orange County',
         'tags': {'profanity': 'some', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'Watermelon Sugar', 'artist': 'Harry Styles',
         'tags': {'profanity': 'none', 'drugs': 'frequent', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'Say So', 'artist': 'Doja Cat',
         'tags': {'profanity': 'some', 'drugs': 'none', 'violence': 'some', 'sexual references': 'some'}},
        {'title': 'The Box', 'artist': 'Roddy Ricch',
         'tags': {'profanity': 'frequent', 'drugs': 'some', 'violence': 'none', 'sexual references': 'some'}},
        {'title': 'Lonely', 'artist': 'Joel Corry',
         'tags': {'profanity': 'none', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'Toosie Slide', 'artist': 'Drake',
         'tags': {'profanity': 'some', 'drugs': 'none', 'violence': 'some', 'sexual references': 'none'}},
        {'title': 'Savage', 'artist': 'Megan Thee Stallion',
         'tags': {'profanity': 'frequent', 'drugs': 'none', 'violence': 'none', 'sexual references': 'some'}},
        {'title': 'Ride It', 'artist': 'Regard',
         'tags': {'profanity': 'none', 'drugs': 'none', 'violence': 'none', 'sexual references': 'frequent'}},
        {'title': 'Physical', 'artist': 'Dua Lipa',
         'tags': {'profanity': 'none', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'SICKO MODE', 'artist': 'Travis Scott',
         'tags': {'profanity': 'frequent', 'drugs': 'some', 'violence': 'some', 'sexual references': 'none'}},
        {'title': 'Bodak Yellow', 'artist': 'Cardi B',
         'tags': {'profanity': 'frequent', 'drugs': 'none', 'violence': 'some', 'sexual references': 'frequent'}},
        {'title': 'Havana', 'artist': 'Camila Cabello',
         'tags': {'profanity': 'none', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'Stir Fry', 'artist': 'Migos',
         'tags': {'profanity': 'frequent', 'drugs': 'none', 'violence': 'none', 'sexual references': 'some'}},
        {'title': 'HUMBLE.', 'artist': 'Kendrick Lamar',
         'tags': {'profanity': 'frequent', 'drugs': 'none', 'violence': 'none', 'sexual references': 'some'}},
        {'title': 'Work', 'artist': 'Rihanna',
         'tags': {'profanity': 'none', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
        {'title': 'Panda', 'artist': 'Desiigner',
         'tags': {'profanity': 'frequent', 'drugs': 'none', 'violence': 'some', 'sexual references': 'none'}},
        {'title': 'Closer', 'artist': 'The Chainsmokers',
         'tags': {'profanity': 'none', 'drugs': 'none', 'violence': 'none', 'sexual references': 'none'}},
    ]
    songs = []
    tags = ['profanity', 'drugs', 'violence', 'sexual references']
    for song_metadata in song_metadata_list:
        song = Song(song_metadata['title'], song_metadata['artist'], api_key)
        [song.assign(tag, severity) for tag, severity in song_metadata['tags'].items()]
        songs.append(song)
        print(song_metadata['title'] + " trained")
    classifiers = [TagClassifier(tag, [(song, song.final_tags[tag]) for song in songs]) for tag in tags]
    filename = r'pickle/'
    if not os.path.exists(filename):
        os.makedirs(filename)
    output = open(os.path.join(filename, r'classifiers.pkl'), 'w+b')
    print('Pickling classifier data')
    pickle.dump(classifiers, output)
    output.close()
    print('Classifiers have been pickled')
    return classifiers

def is_valid_api(key):
    res = requests.get('http://api.genius.com/search?q=' + "travis scott" + " " + "stargazing",
        headers={'Authorization': 'BEARER ' + key})
    data = json.loads(res.text)
    if 'error' in data:
        return False
    else:
        return True
    


def create_app(test_config=None):
    nltk.download('punkt')
    print('punkt downloaded')
    config = configparser.ConfigParser()
    config.read('conf/dev.conf')
    genius_key = config.get('DEFAULT', 'genius_access_token')
    print("Training classifiers.")
    classifiers = demo_trained_classifiers(genius_key)
    print("Training complete.")
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/')
    def hello():
        return {'hi': 'hi'}

    @cross_origin(origin='localhost', headers=['Content- Type', 'Authorization'])

    @app.route('/songquery/<artist>/<title>/<apikey>')
    def get_classifications(artist, title, apikey):
        if not is_valid_api(apikey):
            obj = {}
            obj['meta'] = 401
            return obj
        tester = Song(title, artist, apikey)
        [classifier.assign(tester) for classifier in classifiers]
        obj = tester.get_final_tags()
        obj['artist'] = tester.author
        obj['title'] = tester.title
        obj['url'] = tester.url
        obj['meta'] = 200
        return obj

    return app

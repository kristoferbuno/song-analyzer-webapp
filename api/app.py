import nltk
import requests
import json
import random
from bs4 import BeautifulSoup
GENIUS_ACCESS_TOKEN = ''

class Song:

    def __init__(self, title, author, lyrics: str = ""):
        self.title = title
        self.author = author
        self.all_feature_dicts = {}
        self.final_tags = {}
        if len(lyrics) == 0:
            res = requests.get('http://api.genius.com/search?q=' + author + " " + title,
                               headers={'Authorization': 'BEARER ' + GENIUS_ACCESS_TOKEN})
            data = json.loads(res.text)
            search_results = data['response']['hits']
            selected_song = search_results[0]
            self.genius_id = selected_song['result']['id']

            song_res = requests.get('http://www.genius.com' + selected_song['result']['path'])
            song_html = BeautifulSoup(song_res.text, 'html.parser')
            [script.extract() for script in song_html('script')]
            lyrics = song_html.find('div', class_='lyrics').get_text()
            tokenized_lyrics = nltk.word_tokenize(lyrics)
            self.lyrics = tokenized_lyrics
        else:
            self.lyrics = lyrics
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

    def analyze(self):  # sets song's final tags to a list of tuples (tag, intensity)
        tag_intensities = []  # list of tuples to hold intensities of tags in the song

        profanity_trainers = []
        profanity_classifier = TagClassifier("profanity", profanity_trainers)
        p_prediction = profanity_classifier.predict(self)
        if p_prediction != "none":
            tag_intensities.append(("profanity", p_prediction))

        drug_trainers = []
        drug_classifier = TagClassifier("drugs", drug_trainers)
        d_prediction = drug_classifier.predict(self)
        if d_prediction != "none":
            tag_intensities.append(("drugs", d_prediction))

        violence_trainers = []
        violence_classifier = TagClassifier("violence", violence_trainers)
        v_prediction = violence_classifier.predict(self)
        if v_prediction != "none":
            tag_intensities.append(("violence", v_prediction))

        s_reference_trainers = []
        s_reference_classifier = TagClassifier("sexual references", s_reference_trainers)
        s_prediction = s_reference_classifier.predict(self)
        if s_prediction != "none":
            tag_intensities.append(("sexual references", s_prediction))

        self.final_tags = tag_intensities

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
        self.classifier.show_most_informative_features(5)

    def predict(self, curr_song: Song) -> str:  # output is the intensity of the target tag within the lyrics
        result = self.classifier.classify(curr_song.get_features(self.target_tag))
        return result

    def assign(self, curr_song: Song):
        curr_song.assign(self.target_tag, self.predict(curr_song))

    def tag_type(self):
        return self.target_tag


def demo_trained_classifiers() -> []:
    # format for a song
    # {'title': '', 'artist': '',
    #  'tags': {'profanity': '', 'drugs': '', 'violence': '', 'sexual references': ''}}
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
        song = Song(song_metadata['title'], song_metadata['artist'])
        [song.assign(tag, severity) for tag, severity in song_metadata['tags'].items()]
        songs.append(song)
    classifiers = [TagClassifier(tag, [(song, song.final_tags[tag]) for song in songs]) for tag in tags]
    return classifiers

def test_accuracy():
    # format for a song
    # {'title': '', 'artist': '',
    #  'tags': {'profanity': '', 'drugs': '', 'violence': '', 'sexual references': ''}}
    print("Training classifiers.")
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
    random.shuffle(song_metadata_list)
    training_songs = []
    tags = ['profanity', 'drugs', 'violence', 'sexual references']
    for song_metadata in song_metadata_list:
        song = Song(song_metadata['title'], song_metadata['artist'])
        [song.assign(tag, severity) for tag, severity in song_metadata['tags'].items()]
        training_songs.append(song)
    random.shuffle(training_songs)
    testing_songs = training_songs[:10]
    training_songs = training_songs[10:]
    classifiers = [TagClassifier(tag, [(song, song.final_tags[tag]) for song in training_songs]) for tag in tags]
    print("Training complete!")
    for classifier in classifiers:
        tag_testing_set = [(song.get_features(classifier.target_tag), song.final_tags[classifier.target_tag]) for song in testing_songs]
        print(f"Current testing tag is {classifier.target_tag}")
        print(f"Accuracy is {nltk.classify.accuracy(classifier.classifier, tag_testing_set):.2f}\n")


def training():
    print("Training classifiers.")
    classifiers = demo_trained_classifiers()
    print("Training complete!.")
    # lets test!
    print("\nTest Results")
    print("------------")
    ts_stargazing = Song('Stargazing', 'Travis Scott')
    [classifier.assign(ts_stargazing) for classifier in classifiers]
    print("Stargazing by Travis Scott tags:", ts_stargazing.final_tags, "\n")

    headshot = Song('Headshot', 'Lil Tjay')
    [classifier.assign(headshot) for classifier in classifiers]
    print("Headshot by lil Tjay tags:", headshot.final_tags, "\n")

    rockstar = Song('Rockstar', 'Post Malone')
    [classifier.assign(rockstar) for classifier in classifiers]
    print("Rockstar by Post Malone tags:", rockstar.final_tags, "\n")

    shoot = Song('Shoot', 'BlocBoy JB')
    [classifier.assign(shoot) for classifier in classifiers]
    print("Shoot by BlocBoy JB tags:", shoot.final_tags, "\n")

    disney_song = Song('Next Right Thing', 'Kristen Bell')
    [classifier.assign(disney_song) for classifier in classifiers]
    print("Next Right Thing (Frozen 2) tags:", disney_song.final_tags)

def console_interactive():
    print("Training classifiers.")
    classifiers = demo_trained_classifiers()
    print("Training complete.")
    operate = True
    while operate:
        title = input("Please input a song name.\n")
        artist = input("Please input the artist name.\n\n")
        tester = Song(title, artist)
        [classifier.assign(tester) for classifier in classifiers]
        print(f'{title} by {artist}', tester.final_tags, "\n")
        next = input("Would you like to try another song? [Y/N]\n")
        if next.upper() == 'Y':
            continue
        else:
            operate = False


def main():
    print("Input 1 for a simple demo of the program. Input 2 for an interactive demo. Input 3 for a randomized accuracy sample test.")
    intro_selection = input()
    while intro_selection != '1' and intro_selection != '2' and intro_selection != '3':
        intro_selection = input("Please enter a valid input.\n")
    if intro_selection == '1':
        training()
    if intro_selection == '2':
        console_interactive()
    if intro_selection == '3':
        test_accuracy()

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

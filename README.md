# song_tagger

song_tagger is a project which uses multiple naive-Bayesian classifiers (via nltk.NaiveBayesClassifier) to tag songs based off of profanity, drug references, sexual references, and violent language.

## Running the code
To run the code, run the main function.
Input 1 runs the *training* function; input 2 runs the *console_interactive* function.

For *training*,
the output comes in two major parts: the first part, which prints the most important features
for each classifier, and the second part, demarcated with the header "Test Results", which tests several
songs and prints the results in the format:
```python
# song_name by artist_name tags: {'profanity': w, 'drugs': x, 'violence': y, 'sexual references': z}
```

For *console_interactive*, the output simply asks for a title and artist, then prints the
results in the same format mentioned above.

## Usage

### Song
Container class to generate, handle, and process information relating to a song.

#### Member variables:
* title
* author
* all_feature_dicts
* final_tags

#### __init\_\_(self, title, author, lyrics: str = "")
Constructor for the Song class. Takes in a title, author, and an optional lyrics parameter.
```python
example_song = Song("Fireflies", "Owl City")
```
The constructor uses the title and author to call the Genius API to search for a song, and obtains the first search result's metadata.
It then retrieves the html for said first search result and uses bs4 to parse the lyrics found on the page.
After retrieving all of the information about the song, it calls *self.generate_all_features()*
to generate all four feature dictionaries for the song.

#### generate_feature_specific(self, tag: str)
Takes in a tag and generates a feature dictionary based on that tag. Valid tags include "profanity", "drugs",
"violence", and "sexual references". After the feature dictionary is generated,
it is assigned to the Song member variable *self.all_feature_dicts* as a dictionary entry.
```python
example_song.generate_feature_specific("profanity")
```

#### generate_all_features(self)
Defines a list of tags as ['profanity', 'drugs', 'violence', 'sexual references'], then
iterates through each tag, calling *self.generate_feature_specific(tag)* on each tag.


#### assign(self, tag_type: str, severity: str)
Sets the value of *self.final_tags[tag_type]* to *severity*, which should either be "none", "some", or "frequent".
This function is needed when pre-assigning values to songs in order
to use them as training data for the classifiers.

### TagClassifier
A container class for a Naive-Bayesian classifier specific towards one tag.

#### Member variables:
* target_tag: str
* tagged_songs: list
* training_set
* classifier

#### __init\_\_(self, tag: str, intensity_tags: list)
Assigns *tag* to *self.target_tag* and *intensity_tags* to *self.tagged_songs*; generates a training set
based on *self.tagged_songs*, and trains an *ntlk.NaiveBayesClassifier*, assigning the trained model to
*self.classifier*.

*intensity_tags* is intended to be passed in as a list of (Song, intensity: str) with respect
to the current target tag.

```python
tagged_songs = [(profane_song, 'frequent'), (clean_song, 'none')]
profanity_classifier = TagClassifier('profanity', tagged_songs)
```

#### predict(self, curr_song: Song) -> str
Uses *self.classifier* to classify *curr_song*'s intensity
with respect to the current tag by getting its
feature dictionary for the tag.

Returns the predicted intensity.
```python
r = profanity_classifer.predict(disney_song)
print(r) # 'none'
```

#### assign(self, curr_song: Song) -> str
Calls *curr_song.assign(self.target_tag, self.predict(curr_song))*,
thus assigning *curr_song* a value for the tag in its
*final_tags*.

```python
profanity_classifer.assign(profane_song)
print(profane_song.final_tags['profanity']) # 'frequent'
```

#### tag_type(self)
Returns the target tag for the TagClassifier.
```python
print(profanity_classifier.tag_type()) # 'profanity'
```

### Other functions
#### demo_trained_classifiers() -> []
Uses a list of preset songs as training data and returns a list
of four trained TagClassifiers for each corresponding category.

#### training()
Calls *demo_trained_classifiers()* to obtain the classifiers,
then tests several songs with the trained classifiers
to predict their tags.

#### console_interactive()
Calls *demo_trained_classifiers()* to obtain the classifiers, then
allows users to manually request songs with title and artist as inputs.
These songs are then tested by the trained classifiers for tag prediction.

## License
[MIT](https://choosealicense.com/licenses/mit/)
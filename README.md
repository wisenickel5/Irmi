# (Impressionable) Music Recommendation Inquiry system.

Someone’s favorite songs include basic information that can be derived from digital signals (i.e. tempo, timbre, loudness, etc.).
But these musical representations are rather simple and straightforward to calculate across various song genres and styles. It is
not so trivial to develop higher level interpretations (or notions that are more frequently seen by people), such as mood, danceability, and inspiration.
A decent music recommendation system should be able to decipher our own musical taste over a period of time and recommend music that
suits our mood at a given moment.

This application comes in the form of a command line application that analyzes a user’s Spotify listening history with sound & mood
classification models. A playlist will then be generated in the user’s Spotify account with songs that closely resemble the user’s listening preferences and given mood.

---

## Getting Started

By virtue of best practices, the virtual environment will not be commited to 
this project. An exact version of Python is not necessary, just ensure that a 
version >= 3.10.0 is being used. The Python community recommends setting up 
PyEnv to manage different versions of Python on your machine, see here: 
https://realpython.com/intro-to-pyenv/

Once the version is set, and the repository has been cloned locally, create a 
new directory called `venv` and `cd` into it. Then run the following command:

```
python -m venv .
```

This will create a new virtual environment. Next, activate it:

For windows (Powershell Session):

```
.\venv\Scripts\Activate.ps1
```

For Mac & Linux:

```
source venv/bin/activate
```

Once activated, use pip to install the project's dependencies:

```
pip install -r requirements.txt
```

---

## Related Technologies

- https://github.com/praveenraghuvanshi/sound-classification-mlnet

## Information Sources

- https://towardsdatascience.com/how-to-start-implementing-machine-learning-to-music-4bd2edccce1f

- https://tinuiti.com/blog/performance-display/spotify-algorithm/
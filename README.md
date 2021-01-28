# StudyBot

![StudyBot Logo](res/studybot.png)

StudyBot is a Discord bot which helps you get smarter!
It allows you to study from various question banks from all sorts of disciplines, and allows you to add your own too.
StudyBot is written mainly in Python using `discord.py`.
It uses MongoDB for persistence, and interfaces with Google Sheets API to read user-generated question banks.


# Adding/Updating Packages
If you are contributing, and would like to add a new library to the code, please make sure you add it to `requirements.in`. You will then need to update `requirements.txt`, following the below steps.

1. Ensure the `pip-tools` package is installed on your system. If not, install it with `pip install pip-tools`.
2. Update the `requirements.in` with the names of the new packages you want to add. (optional)
3. Run `pip-compile requirements.in > requirements.txt`, or run `pip-compile requirements.in` and copy the output to replace the contents of `requirements.txt`.

# Timeline
2021 January 27: Start
# homework_bot
This simple bot developed for Yandex Prkatikum students to deliver
up-to-time information about how's code review on your project is going.

It will check your homework status by Praktikum API and then update 
it every 10 minutes.

### To run the script:
On local machine, install all dependencies from requirements.txt using
pip3 (preferably in virtual env)
```bash
$ pip3 install -r requirements.txt
```
Then, add your tokens and chat id to .env file.
And then, run the script from project folder:
```bash
$ python3 homework.py
```

Made by Sinitsyn Artem, curated by Yandex Praktikum.
# tute
A flask app to play tute online

# Installation
Clone the repo to your preferred location.

Intall dependencies from requirements.txt

`pip install -r requirements.txt`

Update the password in config.py

Initialize database

`flask db init`

`flask db migrate -m "inititalization"`

`flask db upgrade`

If deployed in a web host such as [pythonanywhere](https://eu.pythonanywhere.com/), follow the instructions to create the wsgi file and you are pretty much done.

# Rules to play tute
[Rules](https://en.wikipedia.org/wiki/Tute)

Not all rules implemented yet!

# Cards
The files  for each card are based on the [whole deck](https://commons.wikimedia.org/wiki/File:Baraja_espa%C3%B1ola_completa.png) by [Basquetteur](https://commons.wikimedia.org/wiki/User:Basquetteur) so they are licensed under the Creative Commons Attribution-Share Alike 3.0 Unported license.	
You are free:

to share – to copy, distribute and transmit the work

to remix – to adapt the work

Under the following conditions:

attribution – You must give appropriate credit, provide a link to the license, and indicate if changes were made. You may do so in any reasonable manner, but not in any way that suggests the licensor endorses you or your use.

share alike – If you remix, transform, or build upon the material, you must distribute your contributions under the same or compatible license as the original.

# Acknowledgements
The structure of the Flask app is based on [Miguel Grinbergs Flask Mega Tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world) and [his book](https://www.oreilly.com/library/view/flask-web-development/9781491991725/)

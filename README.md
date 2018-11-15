# TagStat
Sample Falcon service to get most popular users from social networks recently posted with given hashtag

## Install

- Clone this repo.

- Install additional modules:
``pip3 install -r requirements.txt``

## Run
gunicorn --timeout 120 --graceful-timeout 120 tagstat:app

See [Gunicorn Deployment](https://gunicorn.org/#deployment) to deploy.

## TODO
- Using BeautifulSoup to parse pages.
- Using to Selenium to get more pages.
- Using asynchronous tasks for page requests and parsing.

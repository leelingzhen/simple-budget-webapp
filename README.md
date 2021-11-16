# Simple Daily Budget
### Description:
A simple implementation of a personal budget management in a dockerized flask webapp. This project was originally used as submission for CS50X's final project. Currently hosted on a personal server


### Getting Started
##### First, clone the repository and go into that directory

```
git clone https://github.com/leelingzhen/simple-budget-webapp.git
cd simple-budget-webapp
```

##### Secondly, pull latest image using docker && run

docker:

```
docker pull ghcr.io/leelingzhen/simple-budget-webapp:latest
docker run -d -p 5000:5000 budget
```

or using docker-compose,
Sample docker-compose.yml:

```
version: "3.7"
services:
  budget:
    image: ghcr.io/leelingzhen/simple-budget-webapp:latest
    ports: 
      - "5000:5000"
    volumes:
      - .:/simple-budget-webapp
```

##### Or, Secondly, buildi && run image from source:

docker:

```
docker build --tag simple-budget-webapp .
docker run -d -p 5000:5000 budget
```

buidling and running with docker-compose:
```
version: "3.7"
services:
  budget:
    image: simple-budget-webapp
	build: .
    ports: 
      - "5000:5000"
    volumes:
      - .:/simple-budget-webapp
```

##### Alternatively, if you wish to not use docker,  use uwsgi to host the app in production mode.  

First create a virtualenv
```
apt-get update && apt-get upgrade -y
apt-get install -y python3-pip python-dev
mkdir venv-flask
python3 -m venv venv-flask
```

activate venv-flask
```
source ./venv-flask/bin/activate
```

update pip and install requirements

```
python -m pip --upgrade install pip
pip install -r requirements.txt
```

start uwsgi server at port 5000
```
uwsgi --protocol=http -w application:app --socket 0.0.0.0:5000 
```

the webapp will be available at http://"your-ip-address":5000


#### Todo
- Add text colours to balances in summary page
	- green for positive balance
	- red for negative balance
- Add yearly summary trending line 

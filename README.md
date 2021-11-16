# Simple Daily Budget
#### Description:
A simple implementation of a personal budget management in a dockerized flask webapp. This project was originally used as submission for CS50X's final project.


#### Getting Started
First clone the repository and go into that directory

```
git clone https://github.com/leelingzhen/simple-budget-webapp.git
cd simple-budget-webapp
```

Build and run docker container 

Using docker:

```
docker build --tag budget .
docker run -d -p 5050:5050 budget
```

or using docker-compose,
Sample docker-compose.yml:

```
version: "3.7"
services:
  budget:
    container_name: budget
    build: .
    ports: 
      - "5050:5050"
    volumes:
      - .:/budget
```

Alternatively, if you wish to not use docker you can use uwsgi to host the app in production mode.  

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

start uwsgi server at port 5050
```
uwsgi --protocol=http -w application:app --socket 0.0.0.0:5050 
```

the webapp will be available at http://"your-ip-address":5050


#### Todo
- Add text colours to balances in summary page
	- green for positive balance
	- red for negative balance
- Add yearly summary trending line 

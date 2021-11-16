# Simple Daily Budget
#### Description:
A simple implementation of a personal budget management in a dockerized flask webapp. This project was originally used as submission for CS50X's final project.


#### Getting Started
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

#### Todo
- Add text colours to balances in summary page
	- green for positive balance
	- red for negative balance
- Add yearly summary trending line 

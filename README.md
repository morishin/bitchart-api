# bitchart-api
JPY/BTC realtime chart image API

Docker Repository https://hub.docker.com/r/morishin127/bitchart-api/

## Run
```
docker pull morishin127/bitchart-api
docker run -itd -p 80:8080 morishin127/bitchart-api
```
And open Docker host machine IP address in browser.

<img src="https://cloud.githubusercontent.com/assets/1413408/11913321/3e2b9ffc-a6a3-11e5-8651-be15435bd840.png" width="320"/>

## Develop
```
git clone git@github.com:morishin/bitchart-api.git
cd bitchart-api
pip install -r requirements.txt
python task.py
python chart.py
```
And open `http://localhost:8080/` in browser.

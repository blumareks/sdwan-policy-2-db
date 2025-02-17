# write sd wan policy to db
Writing sd wan policy to  to postgresql




## build it

* If you have a mac, then run commands :

```sh
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

for win OS in powershell run
```sh
.\.venv\bin\activate
```

### run it

  * in the terminal write `flask --app app run`
  * In a browser, load the url: http://127.0.0.1:5000/

### deploy it in a cloud as a microservice using RHOS

You need to setup the env variable in RHOS for the access to the postgresql:
```
URL=postgresql://ibm_cloud_ user:pass@the.address.databases.appdomain.cloud:port/ibmclouddb
RNA=url
```


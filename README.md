```
$ git clone https://github.com/Poor-Apes/contract_main.git
$ cd contract_main
$ cp .env.example .env
$ cp brownie-config.yaml.EXAMPLE brownie-config.yaml
$ virtualenv -p python3 .venv
$ source .venv/bin/activate
(.venv) $ pip install -r requirements.txt
(.venv) $ brownie test -m "not long"
...
```
1. Create Python virtual environment using [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/):

```sh
mkvirtualenv --python=/usr/bin/python3 ssc_podcast
pip install -r scripts/requirements.txt
```

2. Create file `scripts/aws_access.sh` with AWS key information:

```sh
#!/bin/sh
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
```

3. Add `scripts/cron_script.sh` to `crontab`:

```
15 * * * * run-one /path/to/cron_script.sh
```

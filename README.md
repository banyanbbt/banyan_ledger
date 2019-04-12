# **Banyan ledger**

#### simple ledger platform based on Python3.6 , Django2.3 and django-rest-framework

# **attractive function**

- built connection with HPB(High Performance Blockchain)

# **Requirements**

- Python(3.6)
- Django(2.3)
- django-rest-framework(3.9)a

# **Installation**
```python
pip install -r requirements.txt
```
# **Configuration**
We write all Configurations about celery tasks on the `celery_task/settings.py` file.
You need to change the configuration to your own.
`ledger/settings/dev` noted all configurations about django project.
You also need to modify the configuration abut your environment.For example `DATABASES`,`CACHES`...

# **Running**

#### Modify the database settings,As shown below:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': '127.0.0.1',
        'PORT': 3306,
        'USER': 'root',
        'PASSWORD': 'pwd',
        'NAME': 'gravity'
    }
}
```
#### Create DATABASE
```mysql
CREATE DATABASE gravity;

source ledger/blockcharin_leger.sql;
```
#### Execute command in the two terminals
```shell
# first terminal
cd ~/ledger
celery -A celery_tasks.main worker -l info --logfile hpb.log

# the other terminal
cd ~/ledger
celery -A celery_tasks.hpb.tasks beat - l info
```



 

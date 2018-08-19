# Description

Hardware API for storage fms cell

### Debug startup

Do it only for debug purpose:

```
cd .../fms_hardware/
source ./venv/bin/activate
uwsgi --socket 0.0.0.0:8000 --protocol=http -w storage.web_api.storage_web_api:app
```

For production:
[This guide](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-uwsgi-and-nginx-on-ubuntu-14-04)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'database-1.cxuu6midraas.us-east-1.rds.amazonaws.com',
        'PORT': '5432',
        'OPTIONS': {
            'options': '-c search_path=data'
        }
    }
}
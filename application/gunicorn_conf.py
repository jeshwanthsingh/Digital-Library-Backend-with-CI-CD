from multiprocessing import cpu_count
bind = '0.0.0.0:8000'  # Change from socket to network port
workers = cpu_count() + 1
worker_class = 'uvicorn.workers.UvicornWorker'
loglevel = 'debug'
accesslog = '/home/ubuntu/csc648-fa25-0104-team02/access_log'
errorlog = '/home/ubuntu/csc648-fa25-0104-team02/error_log'

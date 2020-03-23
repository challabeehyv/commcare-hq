"""
Simple WSGI server that exposes Prometheus metrics.

Environment variable `prometheus_multiproc_dir` must be set and match
the value used by Django.
"""
import os
from wsgiref.simple_server import make_server

from prometheus_client import CollectorRegistry, make_wsgi_app, multiprocess
from prometheus_client.exposition import _SilentHandler

multiproc_dir = os.environ.get("prometheus_multiproc_dir")
if not multiproc_dir:
    raise Exception("Environment variable 'prometheus_multiproc_dir' is not set")

print(f"Exposing metrics from '{multiproc_dir}'")

registry = CollectorRegistry()
multiprocess.MultiProcessCollector(registry)

app = make_wsgi_app(registry)
httpd = make_server('', 9011, app, handler_class=_SilentHandler)
httpd.serve_forever()

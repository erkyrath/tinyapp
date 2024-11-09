import sys
import argparse
import importlib.util
import importlib.machinery

import werkzeug.serving

parser = argparse.ArgumentParser()

parser.add_argument('filename')

args = parser.parse_args()


loader = importlib.machinery.SourceFileLoader('_wsgiapp', args.filename)
spec = importlib.util.spec_from_loader('_wsgiapp', loader=loader)
appmod = importlib.util.module_from_spec(spec)
sys.modules['_wsgiapp'] = appmod
spec.loader.exec_module(appmod)

werkzeug.serving.run_simple('localhost', 8001, appmod.application)


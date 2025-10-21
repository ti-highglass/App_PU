import PyInstaller.__main__
import os
import shutil

# Gerar executável do launcher
import shutil

PyInstaller.__main__.run([
    'launcher.py',
    '--onefile',
    '--console',
    '--name=Sistema_PU',
    '--add-data=templates;templates',
    '--add-data=static;static',
    '--add-data=.env;.',
    '--hidden-import=psycopg2',
    '--hidden-import=pandas',
    '--hidden-import=openpyxl',
    '--hidden-import=flask',
    '--hidden-import=werkzeug',
    '--hidden-import=jinja2',
    '--hidden-import=webbrowser',
    '--distpath=dist',
    '--workpath=build',
    '--clean'
])

# Copiar .env para pasta dist
if os.path.exists('.env'):
    shutil.copy2('.env', 'dist/.env')
    print("Arquivo .env copiado para dist/")
else:
    print("AVISO: Arquivo .env não encontrado para copiar")
import os

# Remove DATABASE_URL antes de qualquer importação para que os testes
# rodem sem banco de dados, usando apenas o data.json local.
os.environ.pop("DATABASE_URL", None)

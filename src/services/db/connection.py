import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import OperationalError, extras

def get_db_connection():
    # Cargar las variables de entorno desde el archivo .env
    load_dotenv()

    # Obtener las variables de conexión a la base de datos desde las variables de entorno
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    db_name = os.getenv('DB_NAME')
    db_sslmode = os.getenv('DB_SSLMODE', 'require')  # Default to 'require' if not set

    # Construir la URL de conexión a la base de datos
    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode={db_sslmode}"
    print(f"Conectando a la base de datos en: {db_url}")

    # Establecer la conexión a la base de datos
    try:
        connection = psycopg2.connect(
            db_url,
            sslmode='require',
            application_name="flask_email_app",
            cursor_factory=extras.RealDictCursor
        )
        print("Conexión a la base de datos establecida correctamente")
        return connection

    except OperationalError as error:
        print(f"Error de operación al conectar a la base de datos: {error}")
        return None
    except Exception as error:
        print(f"Error inesperado al conectar a la base de datos: {error}")
        return None
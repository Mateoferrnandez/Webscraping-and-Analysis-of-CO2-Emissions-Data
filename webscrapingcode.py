import requests
from bs4 import BeautifulSoup
import mysql.connector

# Definir constantes globales
YEAR_CHANGE = 3
#URBAN_POP = 10
SHARE_OF_WORLD = 11
MAX_RETRIES = 3  # Número máximo de reintentos para solicitudes HTTP

def clean_percentage(percentage):
    # Esta función limpia los porcentajes, quitando el símbolo '%' y convirtiendo a float
    if percentage.endswith('%'):
        return float(percentage.replace('%', '').strip()) / 100
    return None  # Devuelve None si el porcentaje no es válido

def process_row(celdas):
    row_data = []
    for i, td in enumerate(celdas):
        text = td.get_text(strip=True)
        if i in (YEAR_CHANGE, SHARE_OF_WORLD):
            # Limpia y convierte los porcentajes
            if text == "N.A." or text == "":
                text = None  # Maneja los casos donde no hay dato como 'N.A.' o vacío
            else:
                text = clean_percentage(text)
        elif i != 1:  # No procesar el país, que debe mantenerse como string
            # Limpia comas de los números y maneja valores no disponibles o vacíos
            if text == "N.A." or text == "":
                text = None
            else:
                text = text.replace(',', '').strip()
                # Intenta convertir a float si es un número
                try:
                    text = float(text)
                except ValueError:
                    pass  # Si falla la conversión, mantiene el texto original
        row_data.append(text)
    return row_data

def process_url(url, cursor, sql_insert, db):
    for _ in range(MAX_RETRIES):
        try:
            response = requests.get(url)
            if response.status_code != 200:
                print(f'Error al acceder a {url}: Código de estado {response.status_code}')
                continue
            soup = BeautifulSoup(response.text, 'html.parser')
            tabla = soup.find('table')  # Asumimos que siempre hay una tabla y es la correcta
            if tabla:
                for fila in tabla.find_all('tr')[1:]:  # Omitir el encabezado
                    celdas = fila.find_all('td')
                    if celdas and len(celdas) == 7:
                        row_data = process_row(celdas)
                        if len(row_data) == 7:
                            cursor.execute(sql_insert, row_data)
                            print(f'Datos insertados correctamente para la fila: {row_data}')
                        else:
                            print("Número incorrecto de elementos en row_data:", row_data)
                    else:
                        print("Número incorrecto de celdas en la fila:", celdas)
                db.commit()
                print(f'Datos de la tabla exportados correctamente a la base de datos MySQL')
            else:
                print("No se encontró tabla válida en la página.")
            break  # Si todo va bien, salir del bucle de reintentos
        except requests.RequestException as e:
            print(f'Error de solicitud para {url}: {str(e)}')
        except Exception as e:
            print(f'Error al procesar datos de {url}: {str(e)}')

def main():
    db_config = {
        "host": "bjvaq1vnnjtaf4neekcm-mysql.services.clever-cloud.com",
        "user": "uzkpsovh9wigmsgq",
        "password": "rs8yO0sICKU2nP8eCVp4",
        "database": "bjvaq1vnnjtaf4neekcm"
    }
    sql_insert = """
    INSERT INTO CO2 (`ranq`,`country`,`CO2 Emissions(tons)`,`yearlychange`,`population(2016)`,`percapita`,`worldshare`)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    urls = ['https://www.worldometers.info/co2-emissions/co2-emissions-by-country/']

    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()
        for url in urls:
            process_url(url, cursor, sql_insert, db)
    except mysql.connector.Error as e:
        print(f'Error de MySQL: {str(e)}')
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__": 
    main()

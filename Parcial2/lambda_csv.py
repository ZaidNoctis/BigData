import logging
import datetime
import boto3
from bs4 import BeautifulSoup
import csv
import io


# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


# Configuración de S3
S3_BUCKET_HTML = "landing-casas-parcial"  # Donde están los HTMLs
S3_BUCKET_CSV = "csv-bucket-parcial"  # Bucket donde se guardarán los CSVs
s3_client = boto3.client("s3")


def extract_property_data(soup):
    """Extrae la información de una propiedad desde su HTML."""
    try:
        barrio = soup.find("div", id="view-map__text")
        barrio = barrio.text.strip() if barrio else "Desconocido"

        valor = soup.find("div", class_="prices-and-fees__price")
        valor = valor.text.strip() if valor else "0"

        detalles = soup.find_all("div", class_="details-item-value")
        habitaciones = detalles[0].text.strip() if len(detalles) > 0 else "0"
        banos = detalles[1].text.strip() if len(detalles) > 1 else "0"
        mts2 = detalles[2].text.strip() if len(detalles) > 2 else "0"

        return [barrio, valor, habitaciones, banos, mts2]
    except Exception as e:
        logger.error(f"⚠️ Error extrayendo datos: {e}")
        return ["Desconocido", "0", "0", "0", "0"]


def process_html_files():
    """Descarga HTMLs de S3, extrae información y genera el CSV."""
    today = datetime.datetime.today().strftime("%Y-%m-%d")
    data = []

    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_HTML)
        objects = response.get("Contents", [])

        if not objects:
            logger.warning("❌ No se encontraron archivos HTML en S3.")
            return

        for obj in objects:
            file_key = obj["Key"]
            logger.info(f"📥 Procesando archivo: {file_key}")

            # Descargar HTML desde S3
            file_obj = s3_client.get_object(Bucket=S3_BUCKET_HTML, Key=file_key)
            html_content = file_obj["Body"].read().decode("utf-8")

            soup = BeautifulSoup(html_content, "html.parser")
            extracted_data = extract_property_data(soup)
            data.append([today] + extracted_data)

        if data:
            # Crear CSV en memoria
            csv_buffer = io.StringIO()
            csv_writer = csv.writer(csv_buffer)
            csv_writer.writerow([
                "FechaDescarga", "Barrio", "Valor", 
                "NumHabitaciones", "NumBanos", "mts2"
            ])
            csv_writer.writerows(data)

            # Guardar CSV en S3
            csv_file = f"{today}.csv"
            s3_client.put_object(
                Bucket=S3_BUCKET_CSV,
                Key=f"{today}/{csv_file}",
                Body=csv_buffer.getvalue().encode("utf-8"),
                ContentType="text/csv"
            )
            logger.info(f"✅ Guardado CSV en {S3_BUCKET_CSV}: {csv_file}")
        else:
            logger.warning("⚠️ No se extrajeron datos, no se generará el CSV.")

    except boto3.exceptions.Boto3Error as e:
        logger.error(f"❌ Error con S3: {e}")


def lambda_handler(event, context):
    """Manejador principal para AWS Lambda."""
    process_html_files()
    return {"statusCode": 200, "body": "Procesamiento de HTMLs completado y CSV generado"}


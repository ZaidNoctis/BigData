import boto3
import datetime
from bs4 import BeautifulSoup

# Configuración de S3
S3_BUCKET_HTML = "landing-casas-parcial"  # Donde están los HTMLs
S3_BUCKET_CSV = "csv-bucket-parcial"  # Bucket donde se guardarán los CSVs
s3_client = boto3.client("s3")

def extract_property_data(soup):
    """Extrae la información de una propiedad desde su HTML."""
    try:
        barrio = soup.find("div", id="view-map__text").text.strip() if soup.find("div", id="view-map__text") else "Desconocido"
        valor = soup.find("div", class_="prices-and-fees__price").text.strip() if soup.find("div", class_="prices-and-fees__price") else "0"

        detalles = soup.find_all("div", class_="details-item-value")
        habitaciones = detalles[0].text.strip() if len(detalles) > 0 else "0"
        banos = detalles[1].text.strip() if len(detalles) > 1 else "0"
        mts2 = detalles[2].text.strip() if len(detalles) > 2 else "0"

        return [barrio, valor, habitaciones, banos, mts2]
    except Exception as e:
        print(f"⚠️ Error extrayendo datos: {e}")
        return ["Desconocido", "0", "0", "0", "0"]

def process_html_files():
    """Descarga HTMLs de S3, extrae información y genera el CSV."""
    today = datetime.datetime.today().strftime("%Y-%m-%d")
    data = []

    # Obtener lista de archivos en el bucket de HTMLs
    response = s3_client.list_objects_v2(Bucket=S3_BUCKET_HTML)
    if "Contents" not in response:
        print("❌ No se encontraron archivos HTML en S3.")
        return

    for obj in response["Contents"]:
        file_key = obj["Key"]
        print(f"📥 Procesando archivo: {file_key}")

        # Descargar HTML desde S3
        file_obj = s3_client.get_object(Bucket=S3_BUCKET_HTML, Key=file_key)
        html_content = file_obj["Body"].read().decode("utf-8")

        soup = BeautifulSoup(html_content, "html.parser")
        extracted_data = extract_property_data(soup)
        data.append([today] + extracted_data)

    if data:
        # Guardar CSV en S3
        csv_file = f"{today}.csv"
        csv_body = "FechaDescarga,Barrio,Valor,NumHabitaciones,NumBanos,mts2\n"
        csv_body += "\n".join([",".join(row) for row in data])

        s3_client.put_object(
            Bucket=S3_BUCKET_CSV,
            Key=f"{today}/{csv_file}",
            Body=csv_body.encode("utf-8"),
            ContentType="text/csv"
        )
        print(f"✅ Guardado CSV en {S3_BUCKET_CSV}: {csv_file}")
    else:
        print("⚠️ No se extrajeron datos, no se generará el CSV.")

def lambda_handler(event, context):
    process_html_files()
    return {"statusCode": 200, "body": "Procesamiento de HTMLs completado y CSV generado"}


import datetime
import logging
import requests
import boto3
from bs4 import BeautifulSoup

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Configuración de S3
S3_BUCKET_HTML = "landing-casas-parcial"
s3_client = boto3.client("s3")

# URL de búsqueda de apartaestudios en Bogotá
BASE_URL = "https://casas.mitula.com.co/find"
PARAMS = {
    "operationType": "sell",
    "propertyType": "mitula_studio_apartment",
    "geoId": "mitula-CO-poblacion-0000014156",
    "text": "Bogotá, (Cundinamarca)",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

def get_property_links():
    """Extrae las 10 primeras URLs de los inmuebles desde la página de búsqueda."""
    try:
        response = requests.get(BASE_URL, params=PARAMS, headers=HEADERS)
        response.raise_for_status()  # Lanza error si hay un problema en la solicitud
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error al acceder a {BASE_URL}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    property_links = [
        f"https://casas.mitula.com.co{link['href']}"
        for link in soup.select("a[href^='/listing/']")[:10]
    ]

    logger.info(f"🔗 URLs extraídas: {property_links}")
    return property_links

def download_and_save_html():
    """Descarga los detalles de cada inmueble y guarda el HTML en S3."""
    today = datetime.datetime.today().strftime("%Y-%m-%d")
    property_links = get_property_links()
    
    if not property_links:
        logger.warning("❌ No se encontraron propiedades para descargar.")
        return

    for i, url in enumerate(property_links):
        try:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error al descargar {url}: {e}")
            continue

        file_name = f"{today}-property-{i+1}.html"

        # Guardar HTML en S3
        s3_client.put_object(
            Bucket=S3_BUCKET_HTML,
            Key=f"{today}/{file_name}",
            Body=response.text.encode("utf-8"),
            ContentType="text/html",
        )
        logger.info(f"✅ Guardado: {file_name}")

def lambda_handler(event, context):
    download_and_save_html()
    return {"statusCode": 200, "body": "Scraping y almacenamiento de HTML completado"}


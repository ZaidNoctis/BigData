import requests
import boto3
import datetime
from bs4 import BeautifulSoup

# Configuración de S3
S3_BUCKET_HTML = "landing-casas-parcial"
s3_client = boto3.client("s3")

# URL de búsqueda de apartaestudios en Bogotá
BASE_URL = "https://casas.mitula.com.co/find"
PARAMS = {
    "operationType": "sell",
    "propertyType": "mitula_studio_apartment",
    "geoId": "mitula-CO-poblacion-0000014156",
    "text": "Bogotá, (Cundinamarca)"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_property_links():
    """Extrae las 10 primeras URLs de los inmuebles desde la página de búsqueda."""
    response = requests.get(BASE_URL, params=PARAMS, headers=HEADERS)

    if response.status_code != 200:
        print(f"❌ Error al acceder a {BASE_URL}: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    property_links = []

    # Buscar enlaces que contengan "/listing/"
    for link in soup.select("a[href^='/listing/']")[:10]:  # Extraer solo los primeros 10
        relative_url = link["href"]
        full_url = "https://casas.mitula.com.co" + relative_url  # Convertir a URL completa
        property_links.append(full_url)

    print(f"🔗 URLs extraídas: {property_links}")  # Verificación de enlaces
    return property_links

def download_and_save_html():
    """Descarga los detalles de cada inmueble y guarda el HTML en S3."""
    today = datetime.datetime.today().strftime("%Y-%m-%d")
    property_links = get_property_links()
    
    if not property_links:
        print("❌ No se encontraron propiedades para descargar.")
        return

    for i, url in enumerate(property_links):
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code == 200:
            file_name = f"{today}-property-{i+1}.html"

            # Guardar HTML en S3
            s3_client.put_object(
                Bucket=S3_BUCKET_HTML,
                Key=f"{today}/{file_name}",
                Body=response.text.encode("utf-8"),
                ContentType="text/html"
            )
            print(f"✅ Guardado: {file_name}")
        else:
            print(f"❌ Error al descargar {url}: {response.status_code}")

def lambda_handler(event, context):
    download_and_save_html()
    return {"statusCode": 200, "body": "Scraping y almacenamiento de HTML completado"}


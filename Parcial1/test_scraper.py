import pytest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
from lambda_csv import extract_property_data
from lambda_function import get_property_links, download_and_save_html
import sys
import os

# Agregar el path de Parcial2 al sys.path para poder importar sus funciones
sys.path.insert(0, os.path.abspath("../Parcial2"))

# HTML simulado de la página de listado
HTML_LISTADO = (
    "<html><body>"
    '<a href="/listing/mitula-CO-9100034721910450243"></a>'
    '<a href="/listing/mitula-CO-9100034721910450244"></a>'
    '<a href="/listing/mitula-CO-9100034721910450245"></a>'
    '<a href="/listing/mitula-CO-9100034721910450246"></a>'
    "</body></html>"
)

# HTML simulado de una página de inmueble
HTML_PROPIEDAD = (
    "<html><body>"
    '<div id="view-map__text" class="view-map__text">Bogotá,Cundinamarca</div>'
    '<div class="prices-and-fees__price">$ 335.000.000</div>'
    '<div class="details-item-value">1 habitación</div>'
    "</body></html>"
)


@pytest.fixture
def mock_requests_get():
    """Mock para requests.get que simula las respuestas HTML de la web."""
    with patch("requests.get") as mock_get:
        def side_effect(url, *args, **kwargs):
            if "find" in url:
                return MagicMock(status_code=200, text=HTML_LISTADO)
            return MagicMock(status_code=200, text=HTML_PROPIEDAD)

        mock_get.side_effect = side_effect
        yield mock_get


def test_get_property_links(mock_requests_get):
    """Prueba que extrae correctamente los 10 enlaces de inmuebles."""
    links = get_property_links()
    assert len(links) == 10
    base_url = "https://casas.mitula.com.co/listing/"
    assert links[0] == f"{base_url}mitula-CO-9100034721910450243"


def test_extract_property_data():
    """Prueba que extrae correctamente los datos de un inmueble."""
    soup = BeautifulSoup(HTML_PROPIEDAD, "html.parser")
    data = extract_property_data(soup)
    assert data == ["Bogotá, Cundinamarca", "$ 335.000.000", "1 habitación"]


def test_download_and_process(mock_requests_get):
    """Prueba la función de descarga, verificando la subida a S3 con mock."""
    with patch("lambda_function.s3_client.put_object") as mock_put_object:
        download_and_save_html()
        # Verificar que se subieron los archivos HTML
        assert mock_put_object.call_count >= 10

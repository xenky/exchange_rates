import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import xml.etree.ElementTree as ET
import warnings

# Suprimir advertencias de certificados SSL
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

def get_bcv_rates():
    url = "https://www.bcv.org.ve/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    try:
        # Usar verify=False para ignorar problemas de certificado SSL
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extraer USD/VES
        usd_element = soup.find(id="dolar")
        if usd_element:
            usd_text = usd_element.find('strong').text.replace(',', '.').strip()
            usd_ves = float(usd_text)
        else:
            # Plan B: Buscar por texto
            dolar_div = soup.find('div', class_='dolar')
            if dolar_div:
                usd_text = dolar_div.find('strong').text.replace(',', '.').strip()
                usd_ves = float(usd_text)
            else:
                usd_ves = None
        
        # Extraer EUR/VES
        eur_element = soup.find(id="euro")
        if eur_element:
            eur_text = eur_element.find('strong').text.replace(',', '.').strip()
            eur_ves = float(eur_text)
        else:
            # Plan B: Buscar por texto
            euro_div = soup.find('div', class_='euro')
            if euro_div:
                eur_text = euro_div.find('strong').text.replace(',', '.').strip()
                eur_ves = float(eur_text)
            else:
                eur_ves = None
        
        return {'usdves': usd_ves, 'eurves': eur_ves}
    except Exception as e:
        print(f"Error obteniendo tasas BCV: {str(e)}")
        return {'usdves': None, 'eurves': None}

def get_banrep_rate():
    # Usar API de datos abiertos de Colombia (funcionó correctamente)
    try:
        url = "https://www.datos.gov.co/resource/32sa-8pi3.json?$limit=1&$order=vigenciahasta DESC"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data and isinstance(data, list) and len(data) > 0:
            return {'usdcop': float(data[0]['valor'])}
    except Exception as e:
        print(f"Intento 1 BanRep fallido: {str(e)}")
    
    # Método alternativo por si falla la API principal
    try:
        url = "https://www.banrep.gov.co/es"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        trm_div = soup.find('div', class_='trm-data')
        if trm_div:
            value = trm_div.find('div', class_='valor').text
            cleaned = value.replace('$', '').replace('.', '').replace(',', '').strip()
            return {'usdcop': float(cleaned)}
    except Exception as e:
        print(f"Intento 2 BanRep fallido: {str(e)}")
    
    return {'usdcop': None}

def get_bce_rate():
    url = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/xml'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        
        # Buscar tasa EUR/USD en el XML
        namespaces = {'ns': 'http://www.ecb.int/vocabulary/2002-08-01/eurofxref'}
        for cube in root.findall('.//ns:Cube[@currency="USD"]', namespaces):
            eurusd = float(cube.attrib['rate'])
            return {'eurusd': eurusd}
        
        raise Exception("Tasa EUR/USD no encontrada en XML")
    except Exception as e:
        print(f"Error obteniendo tasa BCE: {str(e)}")
        return {'eurusd': None}

def main():
    # Obtener fecha actual en formato dd/mm/YYYY
    current_date = datetime.now().strftime("%d/%m/%Y")
    
    print("Obteniendo tasas de cambio...")
    print(f"Fecha de consulta: {current_date}")
    
    # Obtener todas las tasas
    print("\nExtrayendo tasas BCV (USD/VES y EUR/VES)...")
    bcv_rates = get_bcv_rates()
    
    print("Extrayendo tasa BanRep (USD/COP)...")
    banrep_rate = get_banrep_rate()
    
    print("Extrayendo tasa BCE (EUR/USD)...")
    bce_rate = get_bce_rate()
    
    rates = {
        'date': current_date,
        'BCV': bcv_rates,
        'BanRep': banrep_rate,
        'BCE': bce_rate
    }
    
    # Guardar en archivo JSON
    with open('rates.json', 'w') as f:
        json.dump(rates, f, indent=4)
    
    print("\nDatos guardados exitosamente en rates.json")
    print("\nResumen de tasas obtenidas:")
    print(f"USD/VES: {bcv_rates['usdves']}")
    print(f"EUR/VES: {bcv_rates['eurves']}")
    print(f"USD/COP: {banrep_rate['usdcop']}")
    print(f"EUR/USD: {bce_rate['eurusd']}")
    
    print("\nEstructura completa del archivo JSON:")
    print(json.dumps(rates, indent=4))

if __name__ == "__main__":
    main()
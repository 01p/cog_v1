import requests
import xml.etree.ElementTree as ET

# URL und Coverage ID
base_url = "https://datacube.julius-kuehn.de/flf/ows"
coverage_id = "jki_phaseX201Xpermanentgreenland_annually"

# WCS DescribeCoverage Request
params = {
    "service": "WCS",
    "version": "2.0.1",
    "request": "DescribeCoverage",
    "coverageId": coverage_id
}

response = requests.get(base_url, params=params)
response.raise_for_status()

# XML-Antwort parsen
root = ET.fromstring(response.content)

# Namespace-Handling
ns = {
    "wcs": "http://www.opengis.net/wcs/2.0",
    "gml": "http://www.opengis.net/gml/3.2",
    "swe": "http://www.opengis.net/swe/2.0",
    "xlink": "http://www.w3.org/1999/xlink"
}

# Coverage-ID und Beschreibung
coverage_summary = root.find("wcs:CoverageDescription", ns)
if coverage_summary is not None:
    identifier_elem = coverage_summary.find("gml:identifier", ns)
    if identifier_elem is not None:
        coverage_id = identifier_elem.text
    else:
        coverage_id = None
    bounded_by = coverage_summary.find("gml:boundedBy/gml:Envelope", ns)

    print(f"Coverage ID: {coverage_id if coverage_id else 'N/A'}")
    print(f"CRS: {bounded_by.attrib.get('srsName') if bounded_by is not None else 'N/A'}")
    print(f"Extent:")
    print(f"  Lower Corner: {bounded_by.find('gml:lowerCorner', ns).text if bounded_by is not None and bounded_by.find('gml:lowerCorner', ns) is not None else 'N/A'}")
    print(f"  Upper Corner: {bounded_by.find('gml:upperCorner', ns).text if bounded_by is not None and bounded_by.find('gml:upperCorner', ns) is not None else 'N/A'}")

    # Dimensions und Formate auslesen
    range_type = coverage_summary.find("gml:rangeType/swe:DataRecord", ns)
    print("\nData Fields:")
    if range_type is not None:
        for field in range_type.findall("swe:field", ns):
            name = field.attrib.get("name")
            quantity = field.find("swe:Quantity", ns)
            uom = quantity.find("swe:uom", ns).attrib.get("code") if quantity is not None and quantity.find("swe:uom", ns) is not None else "N/A"
            print(f"  - {name} ({uom})")
    else:
        print("  No data fields found.")

    # Axes anzeigen
    print("\nAxes:")
    for axis in coverage_summary.findall("gml:domainSet/gml:RectifiedGrid/gml:axisLabels", ns):
        print("  ", axis.text)

    # Zeitachse extrahieren (optional)
    time_seq = coverage_summary.find(".//gml:timePosition", ns)
    if time_seq is not None:
        print("\nSample Time Position:", time_seq.text)
    if identifier_elem is not None:
        print("Coverage ID:", identifier_elem.text)
    else:
        print("⚠️ Kein <gml:identifier> gefunden.")
else:
    print("⚠️ Kein <wcs:CoverageDescription> gefunden.")

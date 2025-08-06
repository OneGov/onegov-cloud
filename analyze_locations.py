import xml.etree.ElementTree as ET

tree = ET.parse('wil_events.json')
root = tree.getroot()


# Find all locations within the <minasa> tag
locations = root.findall('.//locations/location')

# Extract and print location details
for location in locations:
    title = location.find('./address/title').text
    street = location.find('./address/street').text
    city = location.find('./address/city').text
    country = location.find('./address/country').text
    print(f"Title: {title}, Street: {street}, City: {city}, Country: {country}")

print('done')


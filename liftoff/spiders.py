from .americanAirline import americanAirlines
from .aeroplan import aeroplanselnium
from .virginatlantic import vigranAtlantic
from .deltaMiles import DeltaSkyMiles
from .united_mileage import UnitedMileagePlus
from .airFrance import airFrance

SCRAPERS_DICT = {
    "AA": [americanAirlines, "https://www.aa.com"], "AC": [aeroplanselnium, "https://www.aeroplan.com"],
    "VS": [vigranAtlantic, "https://www.virginatlantic.com"], "DL":[DeltaSkyMiles, "https://www.delta.com"],
    "UA": [UnitedMileagePlus, "https://www.united.com"], "AF": [airFrance, "https://www.airfrance.us/"]
}

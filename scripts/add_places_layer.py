"""Add the Overture `places` POI layer to dev and Android styles (idempotent)."""
import json, os

BICON = {
    "fashion_and_apparel_store": "clothing_store_11", "place_of_learning": "school_11",
    "restaurant": "restaurant_11", "bank_or_credit_union": "bank_11", "hotel": "lodging_11",
    "place": "marker_11", "financial_service": "bank_11", "electronics_store": "shop_11",
    "hospital": "hospital_11", "real_estate_service": "marker_11",
    "hardware_home_and_garden_store": "shop_11", "shopping": "shop_11", "education": "school_11",
    "hindu_place_of_worship": "place_of_worship_11", "professional_service": "marker_11",
    "college_university": "college_11", "personal_or_beauty_service": "shop_11",
    "travel_service": "suitcase_11", "historic_site": "monument_11",
    "event_or_party_service": "marker_11", "manufacturer": "shop_11", "automotive_service": "car_11",
    "gas_station": "fuel_11", "corporate_or_business_office": "marker_11",
    "food_and_beverage_store": "grocery_11", "diagnostics_imaging_or_lab_service": "hospital_11",
    "casual_eatery": "restaurant_11", "resort": "lodging_11", "auto_dealer": "car_11",
    "home_service": "marker_11", "gym": "pitch_11", "specialty_school": "school_11",
    "atm": "bank_11", "government_office": "town_hall_11", "lodging": "lodging_11",
    "technical_service": "marker_11", "dental_clinic": "dentist_11", "educational_service": "school_11",
    "fast_food_restaurant": "fast_food_11", "pharmacy_and_drug_store": "pharmacy_11",
    "cafe": "cafe_11", "high_school": "school_11", "b2b_service": "marker_11",
    "public_transit_facility_or_service": "bus_11", "health_care": "hospital_11",
    "religious_organization": "place_of_worship_11", "park": "park_11",
    "social_or_community_service": "marker_11", "building_or_construction_service": "marker_11",
    "vehicle_dealer": "car_11", "tutoring_service": "school_11", "shopping_mall": "shop_11",
    "wellness_service": "star_11", "shipping_or_delivery_service": "suitcase_11",
    "preschool": "school_11", "media_service": "marker_11", "attorney_or_law_firm": "marker_11",
    "specialized_health_care": "hospital_11", "supplier_or_distributor": "marker_11",
    "elementary_school": "school_11", "sport_or_fitness_facility": "pitch_11",
    "b2b_office_and_professional_service": "marker_11", "muslim_place_of_worship": "place_of_worship_11",
    "printing_service": "marker_11", "vehicle_parts_store": "car_11",
    "christian_place_of_worship": "place_of_worship_11", "geographic_entities": "mountain_11",
    "police_station": "police_11", "books_music_and_video_store": "shop_11",
    "community_and_government": "town_hall_11", "sporting_goods_store": "shop_11",
    "train_station": "railway_11", "agricultural_service": "marker_11", "farm": "marker_11",
    "coffee_shop": "cafe_11", "warehouse_club_store": "shop_11", "civic_organization": "town_hall_11",
    "flowers_and_gifts_store": "shop_11", "bakery": "bakery_11", "bar": "bar_11",
    "supermarket": "grocery_11", "grocery": "grocery_11", "convenience_store": "grocery_11",
    "museum": "museum_11", "library": "library_11", "cinema": "cinema_11", "theater": "theatre_11",
    "zoo": "zoo_11", "stadium": "stadium_11", "airport": "airport_11", "bus_station": "bus_11",
    "marina": "harbor_11", "campsite": "campsite_11", "toilet": "toilet_11", "laundry": "laundry_11",
    "veterinary": "veterinary_11", "dentist": "dentist_11", "doctor": "doctor_11",
    "clinic": "hospital_11", "pharmacy": "pharmacy_11", "parking": "marker_11",
    "car_repair": "car_11", "fire_station": "fire_station_11", "post_office": "post_11",
    "attraction": "attraction_11", "playground": "playground_11", "garden": "garden_11",
    "ice_cream": "ice_cream_11", "pub": "beer_11",
    "public_transit_facility_or_service": "bus_11", "train_station": "railway_11",
    "bus_station": "bus_11", "ferry_terminal": "ferry_terminal_11", "taxi": "car_11",
    "airport": "airport_11", "heliport": "heliport_11",
}


def icon_expr():
    e = ["match", ["get", "bcat"]]
    for k, v in BICON.items():
        e += [k, v]
    e.append("circle_11")
    return e


def patch(path, source_url):
    st = json.load(open(path, encoding="utf-8"))
    ref = next((l for l in st["layers"] if l["id"] == "place-town"), {})
    paint = ref.get("paint", {"text-color": "#333", "text-halo-color": "#fff", "text-halo-width": 1})

    st["sources"]["places"] = {"type": "vector", "url": source_url, "minzoom": 11, "maxzoom": 14}
    st["layers"] = [l for l in st["layers"] if l.get("id") not in ("poi", "places")]

    st["layers"].append({
        "id": "places", "type": "symbol", "source": "places", "source-layer": "place", "minzoom": 11,
        "layout": {
            "icon-image": icon_expr(),
            "icon-size": ["interpolate", ["linear"], ["zoom"], 11, 0.45, 16, 1.0],
            "text-field": ["to-string", ["get", "name"]],
            "text-font": ["Noto Sans Regular"], "text-size": 11,
            "text-anchor": "top", "text-offset": [0, 1.1], "text-padding": 2,
            "text-optional": True, "icon-allow-overlap": False,
        },
        "paint": paint,
    })
    json.dump(st, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("patched", os.path.basename(path))


for theme in ("light", "dark", "field"):
    patch(rf"G:\sketcyshitx2\data\style_{theme}.json", "places_local.json")
    ap = rf"G:\sketcyshitx2\android-assets\styles\style_{theme}.json"
    if os.path.exists(ap):
        patch(ap, "pmtiles://pakistan_places.pmtiles")
print("done")

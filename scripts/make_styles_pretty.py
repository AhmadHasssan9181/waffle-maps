"""Richer light/dark styles: landcover, landuse, roads by class with casings,
waterways, aeroways, rail, paths, water names, peaks, POI icons+names, 3D buildings."""
import json

LIGHT = dict(
    bg="#f4f1ec", wood="#cfe0c8", grass="#dfe8d8", farm="#eef0d5", scrub="#e2ead9",
    res="#e8e0d8", com="#f0e4e0", ind="#e6e2dc", cem="#e4e9e2", hosp="#f5e6e6", school="#f3efe0",
    park="#cfe3c8", water="#a5c8e1", wway="#9dc0dc",
    bld="#d9d0c9", bld_out="#b8aca3", bound="#b0a89e",
    mw="#f6a623", mw_c="#d9821f", tr="#f7c948", tr_c="#d9a92f",
    pr="#fde68a", pr_c="#d9b84a", sec="#ffffff", sec_c="#c9c2bb",
    ter="#ffffff", ter_c="#d5cfc8", mi="#ffffff", mi_c="#ddd6cf",
    path="#e8dccb", rail="#999999", text="#333333", halo="#ffffff", city="#111111",
)
DARK = dict(
    bg="#1a1c20", wood="#1c2a1e", grass="#202a22", farm="#26261e", scrub="#202820",
    res="#23262b", com="#2a2529", ind="#26282c", cem="#212a22", hosp="#2b2224", school="#262521",
    park="#1e2b21", water="#14243a", wway="#1b3350",
    bld="#2b2e34", bld_out="#3a3e45", bound="#3a3e45",
    mw="#c47a24", mw_c="#7a4a14", tr="#b8912f", tr_c="#6e5518",
    pr="#8f7a3a", pr_c="#5a4c22", sec="#4a4f57", sec_c="#33373d",
    ter="#3f444b", ter_c="#2c2f34", mi="#34383e", mi_c="#25282c",
    path="#2c2a26", rail="#555555", text="#e6e6e6", halo="#111111", city="#ffffff",
)

FIELD = dict(
    bg="#000000", wood="#001400", grass="#001400", farm="#0d0d00", scrub="#001400",
    res="#0d0d0d", com="#141414", ind="#101010", cem="#0a140a", hosp="#1a0000", school="#141400",
    park="#001400", water="#001a33", wway="#003366",
    bld="#1f1f1f", bld_out="#444444", bound="#555555",
    mw="#ffcc00", mw_c="#806600", tr="#ffaa00", tr_c="#805500",
    pr="#ff8800", pr_c="#804400", sec="#bbbbbb", sec_c="#555555",
    ter="#999999", ter_c="#444444", mi="#777777", mi_c="#333333",
    path="#996633", rail="#888888", text="#ffffff", halo="#000000", city="#ffffff",
)

ICON = {
    "hospital": "hospital_11", "clinic": "hospital_11", "doctors": "doctor_11",
    "dentist": "dentist_11", "pharmacy": "pharmacy_11", "police": "police_11",
    "fire_station": "fire_station_11", "fuel": "fuel_11", "school": "school_11",
    "college": "college_11", "university": "college_11", "bank": "bank_11",
    "atm": "bank_11", "restaurant": "restaurant_11", "fast_food": "fast_food_11",
    "cafe": "cafe_11", "bar": "bar_11", "pub": "beer_11",
    "drinking_water": "drinking_water_11", "park": "park_11", "garden": "garden_11",
    "playground": "playground_11", "pitch": "pitch_11", "stadium": "stadium_11",
    "place_of_worship": "place_of_worship_11", "cemetery": "cemetery_11",
    "attraction": "attraction_11", "museum": "museum_11", "zoo": "zoo_11",
    "theatre": "theatre_11", "cinema": "cinema_11", "lodging": "lodging_11",
    "bus": "bus_11", "railway": "railway_11", "airport": "airport_11",
    "grocery": "grocery_11", "clothing_store": "clothing_store_11", "shop": "shop_11",
    "laundry": "laundry_11", "library": "library_11", "town_hall": "town_hall_11",
    "post": "post_11", "information": "information_11", "toilet": "toilet_11",
    "swimming": "swimming_11", "golf": "golf_11", "monument": "monument_11",
    "picnic_site": "picnic_site_11", "veterinary": "veterinary_11",
}


def icon_expr():
    e = ["match", ["get", "class"]]
    for k, v in ICON.items():
        e += [k, v]
    e.append("circle_11")
    return e


def road(p, id_, classes, col, cas, z, w0, w1):
    filt = ["match", ["get", "class"]] + [c for cl in classes for c in (cl, True)] + [False]
    return [
        {"id": id_ + "-casing", "type": "line", "source": "v", "source-layer": "transportation",
         "minzoom": z, "filter": filt, "layout": {"line-cap": "round", "line-join": "round"},
         "paint": {"line-color": p[cas], "line-width": ["interpolate", ["linear"], ["zoom"], z, w0 + 1.4, 16, w1 + 3.2]}},
        {"id": id_, "type": "line", "source": "v", "source-layer": "transportation",
         "minzoom": z, "filter": filt, "layout": {"line-cap": "round", "line-join": "round"},
         "paint": {"line-color": p[col], "line-width": ["interpolate", ["linear"], ["zoom"], z, w0, 16, w1]}},
    ]


def make(p):
    layers = [
        {"id": "bg", "type": "background", "paint": {"background-color": p["bg"]}},
        {"id": "lc-wood", "type": "fill", "source": "v", "source-layer": "landcover",
         "filter": ["==", ["get", "class"], "wood"], "paint": {"fill-color": p["wood"], "fill-opacity": 0.85}},
        {"id": "lc-grass", "type": "fill", "source": "v", "source-layer": "landcover",
         "filter": ["match", ["get", "class"], "grass", True, "scrub", True, False],
         "paint": {"fill-color": p["grass"], "fill-opacity": 0.7}},
        {"id": "lc-farm", "type": "fill", "source": "v", "source-layer": "landcover",
         "filter": ["==", ["get", "class"], "farmland"], "paint": {"fill-color": p["farm"], "fill-opacity": 0.6}},
        {"id": "lu-res", "type": "fill", "source": "v", "source-layer": "landuse",
         "filter": ["==", ["get", "class"], "residential"], "paint": {"fill-color": p["res"], "fill-opacity": 0.6}},
        {"id": "lu-com", "type": "fill", "source": "v", "source-layer": "landuse",
         "filter": ["==", ["get", "class"], "commercial"], "paint": {"fill-color": p["com"], "fill-opacity": 0.7}},
        {"id": "lu-ind", "type": "fill", "source": "v", "source-layer": "landuse",
         "filter": ["==", ["get", "class"], "industrial"], "paint": {"fill-color": p["ind"], "fill-opacity": 0.7}},
        {"id": "lu-cem", "type": "fill", "source": "v", "source-layer": "landuse",
         "filter": ["==", ["get", "class"], "cemetery"], "paint": {"fill-color": p["cem"], "fill-opacity": 0.7}},
        {"id": "lu-hosp", "type": "fill", "source": "v", "source-layer": "landuse",
         "filter": ["==", ["get", "class"], "hospital"], "paint": {"fill-color": p["hosp"], "fill-opacity": 0.7}},
        {"id": "lu-school", "type": "fill", "source": "v", "source-layer": "landuse",
         "filter": ["==", ["get", "class"], "school"], "paint": {"fill-color": p["school"], "fill-opacity": 0.7}},
        {"id": "park", "type": "fill", "source": "v", "source-layer": "park",
         "paint": {"fill-color": p["park"], "fill-opacity": 0.85}},
        {"id": "water", "type": "fill", "source": "v", "source-layer": "water",
         "paint": {"fill-color": p["water"]}},
        {"id": "waterway", "type": "line", "source": "v", "source-layer": "waterway",
         "paint": {"line-color": p["wway"],
                   "line-width": ["match", ["get", "class"], "river", 2.2, "canal", 1.6, "stream", 1, 0.8]}},
        {"id": "aeroway", "type": "line", "source": "v", "source-layer": "aeroway", "minzoom": 10,
         "paint": {"line-color": p["bld_out"], "line-width": 2}},
        {"id": "building", "type": "fill", "source": "v", "source-layer": "building", "minzoom": 13,
         "paint": {"fill-color": p["bld"], "fill-outline-color": p["bld_out"]}},
        {"id": "building-3d", "type": "fill-extrusion", "source": "v", "source-layer": "building", "minzoom": 16,
         "paint": {"fill-extrusion-color": p["bld"], "fill-extrusion-opacity": 0.75,
                   "fill-extrusion-height": ["coalesce", ["get", "render_height"], 8],
                   "fill-extrusion-base": ["coalesce", ["get", "render_min_height"], 0]}},
        {"id": "boundary", "type": "line", "source": "v", "source-layer": "boundary",
         "paint": {"line-color": p["bound"], "line-width": 1}},
    ]
    layers += road(p, "rd-mw", ["motorway", "motorway_link"], "mw", "mw_c", 5, 2.2, 9.0)
    layers += road(p, "rd-tr", ["trunk", "trunk_link"], "tr", "tr_c", 6, 1.8, 7.0)
    layers += road(p, "rd-pr", ["primary", "primary_link"], "pr", "pr_c", 7, 1.4, 5.5)
    layers += road(p, "rd-sec", ["secondary", "secondary_link"], "sec", "sec_c", 9, 1.0, 4.0)
    layers += road(p, "rd-ter", ["tertiary", "tertiary_link"], "ter", "ter_c", 11, 0.7, 2.8)
    layers += road(p, "rd-mi", ["minor"], "mi", "mi_c", 13, 0.5, 1.8)
    layers += [
        {"id": "rd-svc", "type": "line", "source": "v", "source-layer": "transportation", "minzoom": 14,
         "filter": ["match", ["get", "class"], "service", True, "track", True, False],
         "paint": {"line-color": p["mi"], "line-width": 0.6}},
        {"id": "rd-path", "type": "line", "source": "v", "source-layer": "transportation", "minzoom": 14,
         "filter": ["==", ["get", "class"], "path"],
         "paint": {"line-color": p["path"], "line-width": 0.8, "line-dasharray": [2, 2]}},
        {"id": "rail", "type": "line", "source": "v", "source-layer": "transportation", "minzoom": 12,
         "filter": ["==", ["get", "class"], "rail"],
         "paint": {"line-color": p["rail"], "line-width": 1, "line-dasharray": [4, 3]}},
        {"id": "road-bridge", "type": "line", "source": "v", "source-layer": "transportation", "minzoom": 13,
         "filter": ["==", ["get", "brunnel"], "bridge"],
         "paint": {"line-color": p["mi"], "line-width": ["interpolate", ["linear"], ["zoom"], 13, 1.4, 16, 4.5]}},
        {"id": "road-tunnel", "type": "line", "source": "v", "source-layer": "transportation", "minzoom": 13,
         "filter": ["==", ["get", "brunnel"], "tunnel"],
         "paint": {"line-color": p["mi_c"], "line-width": ["interpolate", ["linear"], ["zoom"], 13, 1, 16, 3.5], "line-dasharray": [2, 2]}},
        {"id": "transit-line", "type": "line", "source": "v", "source-layer": "transportation", "minzoom": 12,
         "filter": ["==", ["get", "class"], "transit"],
         "paint": {"line-color": "#8B5CF6", "line-width": 1.5, "line-dasharray": [3, 2]}},
        {"id": "oneway", "type": "symbol", "source": "v", "source-layer": "transportation", "minzoom": 16,
         "filter": ["==", ["get", "oneway"], 1],
         "layout": {"icon-image": "oneway", "icon-size": 0.45, "symbol-placement": "line",
                    "icon-rotate": 90, "symbol-spacing": 70},
         "paint": {"icon-opacity": 0.55}},
        {"id": "road-label", "type": "symbol", "source": "v", "source-layer": "transportation_name", "minzoom": 11,
         "layout": {"text-field": ["to-string", ["coalesce", ["get", "name:en"], ["get", "name"], ""]],
                    "text-font": ["Noto Sans Regular"],
                    "text-size": ["interpolate", ["linear"], ["zoom"], 11, 9, 16, 12],
                    "symbol-placement": "line", "text-padding": 2, "text-letter-spacing": 0.02,
                    "symbol-sort-key": ["match", ["get", "class"],
                                        "motorway", 1, "trunk", 2, "primary", 3,
                                        "secondary", 4, "tertiary", 5, 6]},
         "paint": {"text-color": p["text"], "text-halo-color": p["halo"], "text-halo-width": 1.3}},
        {"id": "road-shield", "type": "symbol", "source": "v", "source-layer": "transportation_name", "minzoom": 11,
         "filter": ["has", "ref"],
         "layout": {"icon-image": ["match", ["length", ["get", "ref"]],
                                   1, "road_1", 2, "road_2", 3, "road_3", 4, "road_4", 5, "road_5", 6, "road_6", "road_6"],
                    "text-field": ["to-string", ["get", "ref"]],
                    "text-font": ["Noto Sans Regular"], "text-size": 9, "icon-size": 0.9,
                    "symbol-placement": "line", "icon-allow-overlap": False,
                    "icon-rotation-alignment": "viewport", "text-rotation-alignment": "viewport"},
         "paint": {"text-color": "#222222"}},
        {"id": "water-name", "type": "symbol", "source": "v", "source-layer": "water_name", "minzoom": 12,
         "layout": {"text-field": ["to-string", ["coalesce", ["get", "name:en"], ["get", "name"], ""]],
                    "text-font": ["Noto Sans Italic"], "text-size": 11, "symbol-placement": "line"},
         "paint": {"text-color": p["wway"], "text-halo-color": p["halo"], "text-halo-width": 1}},
        {"id": "aerodrome", "type": "symbol", "source": "v", "source-layer": "aerodrome_label", "minzoom": 10,
         "layout": {"text-field": ["to-string", ["coalesce", ["get", "name:en"], ["get", "name"], ""]],
                    "text-font": ["Noto Sans Regular"], "text-size": 11},
         "paint": {"text-color": p["text"], "text-halo-color": p["halo"], "text-halo-width": 1.2}},
        {"id": "peak", "type": "symbol", "source": "v", "source-layer": "mountain_peak", "minzoom": 11,
         "layout": {"text-field": ["to-string", ["coalesce", ["get", "name:en"], ["get", "name"], ""]],
                    "text-font": ["Noto Sans Italic"], "text-size": 10},
         "paint": {"text-color": p["text"], "text-halo-color": p["halo"], "text-halo-width": 1}},
        {"id": "place-village", "type": "symbol", "source": "v", "source-layer": "place", "minzoom": 11,
         "filter": ["match", ["get", "class"], "village", True, "hamlet", True, False],
         "layout": {"text-field": ["to-string", ["coalesce", ["get", "name:en"], ["get", "name"], ""]],
                    "text-font": ["Noto Sans Regular"],
                    "text-size": ["interpolate", ["linear"], ["zoom"], 11, 10, 14, 13]},
         "paint": {"text-color": p["text"], "text-halo-color": p["halo"], "text-halo-width": 1.2}},
        {"id": "place-town", "type": "symbol", "source": "v", "source-layer": "place", "minzoom": 9,
         "filter": ["==", ["get", "class"], "town"],
         "layout": {"text-field": ["to-string", ["coalesce", ["get", "name:en"], ["get", "name"], ""]],
                    "text-font": ["Noto Sans Regular"],
                    "text-size": ["interpolate", ["linear"], ["zoom"], 9, 11, 13, 16]},
         "paint": {"text-color": p["text"], "text-halo-color": p["halo"], "text-halo-width": 1.4}},
        {"id": "place-suburb", "type": "symbol", "source": "v", "source-layer": "place", "minzoom": 12,
         "filter": ["match", ["get", "class"],
                    "suburb", True, "neighbourhood", True, "quarter", True, "borough", True, False],
         "layout": {"text-field": ["to-string", ["coalesce", ["get", "name:en"], ["get", "name"], ""]],
                    "text-font": ["Noto Sans Regular"],
                    "text-size": ["interpolate", ["linear"], ["zoom"], 12, 10, 16, 12],
                    "text-letter-spacing": 0.08, "text-transform": "uppercase",
                    "text-max-width": 8},
         "paint": {"text-color": p["text"], "text-halo-color": p["halo"], "text-halo-width": 1.1,
                   "text-opacity": 0.9}},
        {"id": "place-city", "type": "symbol", "source": "v", "source-layer": "place",
         "filter": ["match", ["get", "class"], "city", True, "capital", True, False],
         "layout": {"text-field": ["to-string", ["coalesce", ["get", "name:en"], ["get", "name"], ""]],
                    "text-font": ["Noto Sans Medium"],
                    "text-size": ["interpolate", ["linear"], ["zoom"], 5, 11, 12, 18]},
         "paint": {"text-color": p["city"], "text-halo-color": p["halo"], "text-halo-width": 1.6}},
        {"id": "housenumber", "type": "symbol", "source": "v", "source-layer": "housenumber", "minzoom": 16,
         "layout": {"text-field": ["to-string", ["get", "housenumber"]],
                    "text-font": ["Noto Sans Regular"], "text-size": 9},
         "paint": {"text-color": p["text"], "text-halo-color": p["halo"],
                   "text-halo-width": 0.7, "text-opacity": 0.75}},
        {"id": "poi", "type": "symbol", "source": "v", "source-layer": "poi", "minzoom": 14,
         "filter": ["==", "$type", "Point"],
         "layout": {"icon-image": icon_expr(),
                    "icon-size": ["interpolate", ["linear"], ["zoom"], 14, 0.7, 16, 1.0],
                    "text-field": ["to-string", ["coalesce", ["get", "name:en"], ["get", "name"], ""]],
                    "text-font": ["Noto Sans Regular"], "text-size": 10, "text-anchor": "top",
                    "text-offset": [0, 1.1], "text-optional": True},
         "paint": {"text-color": p["text"], "text-halo-color": p["halo"], "text-halo-width": 1}},
    ]
    return {"version": 8, "sprite": "assets/sprite/sprite",
            "glyphs": "assets/fonts/{fontstack}/{range}.pbf",
            "sources": {"v": {"type": "vector", "url": "tiles_local.json"}},
            "layers": layers}


for name, pal in (("light", LIGHT), ("dark", DARK), ("field", FIELD)):
    st = make(pal)
    out = rf"G:\sketcyshitx2\data\style_{name}.json"
    json.dump(st, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("wrote", out, "layers", len(st["layers"]))

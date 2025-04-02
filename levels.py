LEVELS = {
    "Poziom 1": [  # Startowy poziom — uczysz się
        {"x": 150, "y": 300, "color": "green", "type": "circle", "units": 10, "max_connections": 2},
        {"x": 800, "y": 300, "color": "red", "type": "circle", "units": 5, "max_connections": 1},
    ],

    "Poziom 2": [  # Więcej typów i szersze pole walki
        {"x": 100, "y": 600, "color": "green", "type": "circle", "units": 12, "max_connections": 2},
        {"x": 200, "y": 200, "color": "green", "type": "plus", "units": 8, "max_connections": 3},
        {"x": 700, "y": 150, "color": "red", "type": "triangle", "units": 10, "max_connections": 2},
        {"x": 850, "y": 500, "color": "red", "type": "circle", "units": 8, "max_connections": 2},
    ],

    "Poziom 3": [  # Równe szanse, więcej kierunków
        {"x": 100, "y": 100, "color": "green", "type": "plus", "units": 10, "max_connections": 3},
        {"x": 300, "y": 600, "color": "green", "type": "circle", "units": 8, "max_connections": 2},
        {"x": 700, "y": 100, "color": "red", "type": "plus", "units": 10, "max_connections": 3},
        {"x": 900, "y": 600, "color": "red", "type": "triangle", "units": 8, "max_connections": 2},
    ],

    "Poziom 4": [  # Wróg ma przewagę — musisz atakować z rozmysłem
        {"x": 100, "y": 350, "color": "green", "type": "triangle", "units": 10, "max_connections": 2},
        {"x": 400, "y": 600, "color": "green", "type": "circle", "units": 6, "max_connections": 2},

        {"x": 650, "y": 100, "color": "red", "type": "plus", "units": 14, "max_connections": 3},
        {"x": 800, "y": 300, "color": "red", "type": "circle", "units": 10, "max_connections": 2},
        {"x": 900, "y": 600, "color": "red", "type": "triangle", "units": 8, "max_connections": 2},
    ],

    "Poziom 5": [  # Pełna plansza — trudna walka
        {"x": 150, "y": 400, "color": "green", "type": "plus", "units": 10, "max_connections": 3},
        {"x": 300, "y": 150, "color": "green", "type": "triangle", "units": 6, "max_connections": 1},

        {"x": 500, "y": 500, "color": "red", "type": "plus", "units": 14, "max_connections": 3},
        {"x": 650, "y": 100, "color": "red", "type": "circle", "units": 10, "max_connections": 2},
        {"x": 800, "y": 300, "color": "red", "type": "triangle", "units": 12, "max_connections": 2},
        {"x": 900, "y": 600, "color": "red", "type": "plus", "units": 8, "max_connections": 3},
    ]
}

import math

def haversine(lat1, lon1, lat2, lon2):
    """
    Calcula a distância entre dois pontos geográficos usando a fórmula de Haversine.
    Retorna a distância em quilômetros.
    """
    R = 6371  # raio da Terra em km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c

def calcular_proximidade(user_coords, unidades_coords):
    """
    Recebe coordenadas do usuário e um dicionário de unidades com suas coordenadas.
    Retorna um dicionário {nome_unidade: status_proximidade}.
    """
    lat_user, lon_user = user_coords
    resultado = {}

    for nome, (lat, lon) in unidades_coords.items():
        distancia = haversine(lat_user, lon_user, lat, lon)
        
        # Converte distância em status
        if distancia < 2:
            status = f"Muito perto ({distancia:.1f} km)"
        elif distancia < 10:
            status = f"Perto ({distancia:.1f} km)"
        else:
            status = f"Longe ({distancia:.1f} km)"
        
        resultado[nome] = status
    
    return resultado

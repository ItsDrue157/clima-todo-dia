def uv_index(uv_index):
    if uv_index >= 0 and uv_index <= 2:
        return f'{uv_index}: UV BAIXO'
    elif uv_index >= 3 and uv_index <= 5:
        return f'{uv_index}:UV MODERADO, recomenda-se um protetor fator 30'
    elif uv_index >=6 and uv_index<=7:
        return f'{uv_index}: UV ALTO, recomenda-se um oculos de sol'
    elif uv_index >= 8 and uv_index<=10:
        return f'{uv_index}: UV MUITO ALTO, risco alto de queimadura'
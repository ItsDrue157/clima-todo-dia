def calcularDirecaoDoVento(direcaoDoVento):
    
    if direcaoDoVento >= 337.5 or direcaoDoVento <= 22.5:
        return(f'Norte')

    #Nordeste
    elif direcaoDoVento >= 22.5 and direcaoDoVento <67.5:
        return(f'Nordeste')

    #Leste
    elif direcaoDoVento >= 67.5 and direcaoDoVento < 112.5:
        return(f'Leste')

    #Sudeste
    elif direcaoDoVento >= 112.5 and direcaoDoVento <157.5:
        return(f'Sudeste')

    #Sul
    elif direcaoDoVento >= 157.5 and direcaoDoVento < 202.5:
        return(f'Sul')

    #Sudoeste
    elif direcaoDoVento >= 202.5 and direcaoDoVento < 247.5:
        return(f'Sudoeste')

    #Oeste
    elif direcaoDoVento >= 247.5 and direcaoDoVento < 292.5:
        return(f'Oeste')

    #Noroeste
    elif direcaoDoVento >= 292.5 and direcaoDoVento < 337.5:
        return(f'Noroeste')
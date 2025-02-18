import copy
import math

X = "X"
O = "O"
EMPTY = None

def estado_inicial():
    """
    Retorna o estado inicial do tabuleiro.
    """
    return [
        [EMPTY, EMPTY, EMPTY],
        [EMPTY, EMPTY, EMPTY],
        [EMPTY, EMPTY, EMPTY]
    ]


def jogador(tabuleiro):
    """
    Retorna qual jogador (X ou O) fará a próxima jogada no tabuleiro.
    Se o número de X for maior que o número de O, então é a vez de O.
    Caso contrário, é a vez de X.
    """
    x_count = 0
    o_count = 0

    for linha in tabuleiro:
        for casa in linha:
            if casa == X:
                x_count += 1
            elif casa == O:
                o_count += 1

    if x_count > o_count:
        return O
    else:
        return X


def acoes(tabuleiro):
    """
    Retorna um conjunto de todas as ações possíveis (i, j) disponíveis no tabuleiro.
    Cada ação é uma tupla (linha, coluna) onde ainda não há uma jogada.
    """
    movimentos_possiveis = set()
    for i in range(len(tabuleiro)):
        for j in range(len(tabuleiro[0])):
            if tabuleiro[i][j] == EMPTY:
                movimentos_possiveis.add((i, j))
    return movimentos_possiveis


def resultado(tabuleiro, acao):
    """
    Retorna o tabuleiro resultante ao aplicar a ação (i, j) no tabuleiro.
    """
    if acao not in acoes(tabuleiro):
        raise Exception("Movimento inválido!")

    i, j = acao
    copia_tabuleiro = copy.deepcopy(tabuleiro)
    copia_tabuleiro[i][j] = jogador(tabuleiro)
    return copia_tabuleiro


def checa_linha(tabuleiro, simbolo):
    """
    Verifica se existe alguma linha completa para o jogador 'simbolo' (X ou O).
    Retorna True se existir, caso contrário False.
    """
    for i in range(len(tabuleiro)):
        if (tabuleiro[i][0] == simbolo and
            tabuleiro[i][1] == simbolo and
            tabuleiro[i][2] == simbolo):
            return True
    return False


def checa_coluna(tabuleiro, simbolo):
    """
    Verifica se existe alguma coluna completa para o jogador 'simbolo'.
    Retorna True se existir, caso contrário False.
    """
    for j in range(len(tabuleiro[0])):
        if (tabuleiro[0][j] == simbolo and
            tabuleiro[1][j] == simbolo and
            tabuleiro[2][j] == simbolo):
            return True
    return False


def checa_diagonal_principal(tabuleiro, simbolo):
    """
    Verifica se a diagonal principal (canto superior esquerdo para canto inferior direito)
    está completa para o jogador 'simbolo'.
    """
    for i in range(len(tabuleiro)):
        if tabuleiro[i][i] != simbolo:
            return False
    return True


def checa_diagonal_secundaria(tabuleiro, simbolo):
    """
    Verifica se a diagonal secundária (canto superior direito para canto inferior esquerdo)
    está completa para o jogador 'simbolo'.
    """
    tamanho = len(tabuleiro)
    for i in range(tamanho):
        if tabuleiro[i][tamanho - 1 - i] != simbolo:
            return False
    return True


def vencedor(tabuleiro):
    """
    Retorna o vencedor do jogo (X ou O) caso exista, senão retorna None.
    """
    # Verifica se X ganhou
    if (checa_linha(tabuleiro, X) or
        checa_coluna(tabuleiro, X) or
        checa_diagonal_principal(tabuleiro, X) or
        checa_diagonal_secundaria(tabuleiro, X)):
        return X

    # Verifica se O ganhou
    if (checa_linha(tabuleiro, O) or
        checa_coluna(tabuleiro, O) or
        checa_diagonal_principal(tabuleiro, O) or
        checa_diagonal_secundaria(tabuleiro, O)):
        return O

    # Caso contrário, não há vencedor
    return None


def terminal(tabuleiro):
    """
    Retorna True se o jogo acabou (alguém venceu ou não há mais espaços vazios),
    caso contrário False.
    """
    if vencedor(tabuleiro) is not None:
        return True

    for linha in tabuleiro:
        for casa in linha:
            if casa == EMPTY:
                return False
    return True


def utilidade(tabuleiro):
    """
    Retorna 1 se X venceu, -1 se O venceu e 0 caso contrário.
    """
    ganhador = vencedor(tabuleiro)
    if ganhador == X:
        return 1
    elif ganhador == O:
        return -1
    else:
        return 0


def max_valor(tabuleiro):
    """
    Função auxiliar para o algoritmo minimax.
    Retorna o valor máximo que pode ser obtido a partir do estado 'tabuleiro'.
    """
    if terminal(tabuleiro):
        return utilidade(tabuleiro)

    v = -math.inf
    for acao in acoes(tabuleiro):
        v = max(v, min_valor(resultado(tabuleiro, acao)))
    return v


def min_valor(tabuleiro):
    """
    Função auxiliar para o algoritmo minimax.
    Retorna o valor mínimo que pode ser obtido a partir do estado 'tabuleiro'.
    """
    if terminal(tabuleiro):
        return utilidade(tabuleiro)

    v = math.inf
    for acao in acoes(tabuleiro):
        v = min(v, max_valor(resultado(tabuleiro, acao)))
    return v


def minimax(tabuleiro):
    """
    Retorna a ação ótima (linha, coluna) para o jogador atual no tabuleiro,
    de acordo com o algoritmo minimax.
    Se o jogo já estiver em estado terminal, retorna None.
    """
    if terminal(tabuleiro):
        return None

    turno = jogador(tabuleiro)

    if turno == X:
        # Jogador Max (X)
        melhor_valor = -math.inf
        melhor_acao = None
        for acao in acoes(tabuleiro):
            valor = min_valor(resultado(tabuleiro, acao))
            if valor > melhor_valor:
                melhor_valor = valor
                melhor_acao = acao
        return melhor_acao
    else:
        # Jogador Min (O)
        melhor_valor = math.inf
        melhor_acao = None
        for acao in acoes(tabuleiro):
            valor = max_valor(resultado(tabuleiro, acao))
            if valor < melhor_valor:
                melhor_valor = valor
                melhor_acao = acao
        return melhor_acao

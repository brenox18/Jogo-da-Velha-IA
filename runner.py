import pygame
import sys
import random
import math

import tictactoe as ttt 

pygame.init()

# Configurações de tela
tamanho = largura, altura = 800, 600
tela = pygame.display.set_mode(tamanho)
pygame.display.set_caption("Jogo da Velha")
clock = pygame.time.Clock()

# Cores
preto = (0, 0, 0)
branco = (255, 255, 255)
cinza = (50, 50, 50)
vermelho = (255, 50, 50)         # Para overlay de derrota
hover_color = (255, 255, 255, 50)  # Branco semi-transparente para efeito de hover

# Cores para o gradiente de fundo
gradient_top = (20, 20, 30)
gradient_bottom = (50, 50, 80)

# Carrega fontes
try:
    fonteMedia = pygame.font.Font("Nunito-Regular.ttf", 28)
    fonteGrande = pygame.font.Font("Nunito-Regular.ttf", 40)
    fonteMovimento = pygame.font.Font("Nunito-Regular.ttf", 60)
except Exception as e:
    print("Fonte Nunito não encontrada, utilizando Comic Sans MS.", e)
    fonteMedia = pygame.font.SysFont("comicsansms", 28)
    fonteGrande = pygame.font.SysFont("comicsansms", 40)
    fonteMovimento = pygame.font.SysFont("comicsansms", 60)

# Carrega sons
try:
    fake_load_sound = pygame.mixer.Sound("assets/fake_load.mp3")
    loser_sound = pygame.mixer.Sound("assets/loser.mp3")
    
    # Som das explosões (usado na jogada da máquina)
    maquina_click_sound = pygame.mixer.Sound("assets/maquina_click.mp3")
    # Reduz o volume para 30%
    maquina_click_sound.set_volume(0.2)

    player_click_sound = pygame.mixer.Sound("assets/player_click.mp3")
    player_click_sound.set_volume(0.2)

    trilha_sonora_sound = pygame.mixer.Sound("assets/trilha_sonora.mp3")
except Exception as e:
    print("Erro ao carregar efeitos sonoros:", e)
    fake_load_sound = None
    loser_sound = None
    maquina_click_sound = None
    player_click_sound = None
    trilha_sonora_sound = None

# Função para desenhar um gradiente no fundo
def draw_gradient(surface, color_top, color_bottom):
    for y in range(surface.get_height()):
        ratio = y / surface.get_height()
        r = int(color_top[0] * (1 - ratio) + color_bottom[0] * ratio)
        g = int(color_top[1] * (1 - ratio) + color_bottom[1] * ratio)
        b = int(color_top[2] * (1 - ratio) + color_bottom[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (surface.get_width(), y))

# --- Efeito de Explosão ---
class ExplosionParticle:
    def __init__(self, pos, color):
        self.x, self.y = pos
        self.color = color
        self.radius = random.randint(3, 6)
        self.lifetime = random.randint(20, 40)
        self.max_lifetime = self.lifetime
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1

    def draw(self, surface):
        if self.lifetime > 0:
            alpha = int(255 * (self.lifetime / self.max_lifetime))
            surf = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, self.color + (alpha,), (self.radius, self.radius), self.radius)
            surface.blit(surf, (self.x - self.radius, self.y - self.radius))

class Explosion:
    def __init__(self, pos, color, particle_count=20):
        self.particles = [ExplosionParticle(pos, color) for _ in range(particle_count)]
        self.done = False

    def update(self):
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.lifetime > 0]
        if not self.particles:
            self.done = True

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

# Lista para armazenar os efeitos de explosão ativos
explosion_effects = []

# --- Efeito de Fade (overlay vermelho na derrota) ---
fade_duration = 60  # duração em frames para o fade
fade_time = 0
fade_overlay_alpha = 0

# Classe para botões (usada na tela de seleção e no resultado)
class Button:
    def __init__(self, rect, text, font, base_color, hover_color, text_color):
        self.base_rect = pygame.Rect(rect)
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.base_color = base_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.current_color = base_color
        self.scale = 1.0

    def draw(self, surface):
        shadow_offset = 4
        shadow_rect = self.rect.copy()
        shadow_rect.x += shadow_offset
        shadow_rect.y += shadow_offset
        pygame.draw.rect(surface, (0, 0, 0), shadow_rect, border_radius=8)
        pygame.draw.rect(surface, self.current_color, self.rect, border_radius=8)
        text_shadow = self.font.render(self.text, True, cinza)
        text_shadow_rect = text_shadow.get_rect(center=(self.rect.centerx + 2, self.rect.centery + 2))
        surface.blit(text_shadow, text_shadow_rect)
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def update(self, pos):
        if self.base_rect.collidepoint(pos):
            self.current_color = self.hover_color
            self.scale = min(1.1, self.scale + 0.05)
        else:
            self.current_color = self.base_color
            self.scale = max(1.0, self.scale - 0.05)
        center = self.base_rect.center
        self.rect.width = int(self.base_rect.width * self.scale)
        self.rect.height = int(self.base_rect.height * self.scale)
        self.rect.center = center

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

# Parâmetros do tabuleiro (grade 3x3 tradicional)
tamanho_casa = 100
origem = (largura / 2 - 1.5 * tamanho_casa, altura / 2 - 1.5 * tamanho_casa)
tabuleiro_area = pygame.Rect(origem[0], origem[1], 3 * tamanho_casa, 3 * tamanho_casa)

# Variáveis de estado
usuario = None               # Se None, estamos na tela de seleção
tabuleiro = ttt.estado_inicial()
resultado = None             # Guarda o resultado da rodada (None, empate ou o símbolo do vencedor)
# Flag para garantir que a trilha sonora seja interrompida somente uma vez quando o jogador perde
trilha_interrompida = False

# Controle da jogada do computador via timer
computer_move_scheduled = False
COMPUTER_MOVE_EVENT = pygame.USEREVENT + 1

# Botões
botaoX = Button((largura / 8, altura / 2, largura / 4, 60), "Jogar como X", fonteMedia, branco, (200, 200, 200), preto)
botaoO = Button((5 * largura / 8, altura / 2, largura / 4, 60), "Jogar como O", fonteMedia, branco, (200, 200, 200), preto)
botaoNovamente = Button((largura / 3, altura - 100, largura / 3, 60), "Jogar Novamente", fonteMedia, branco, (200, 200, 200), preto)

# Prepara o fundo com gradiente
fundo = pygame.Surface(tela.get_size())
draw_gradient(fundo, gradient_top, gradient_bottom)

# Função de easing (easeOutQuad) para o fade de derrota
def easeOutQuad(t, b, c, d):
    t /= d
    return -c * t * (t - 2) + b

# Controle do "fake load" na tela de seleção
fake_loading = False
fake_load_start = 0
FAKE_LOAD_DURATION = 2000  # 2 segundos

running = True
while running:
    clock.tick(60)
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Evento para a jogada do computador (apenas na partida ativa)
        if event.type == COMPUTER_MOVE_EVENT:
            if usuario is not None and not ttt.terminal(tabuleiro):
                # Se for a vez do computador
                if usuario != ttt.jogador(tabuleiro):
                    melhor_jogada = ttt.minimax(tabuleiro)
                    tabuleiro = ttt.resultado(tabuleiro, melhor_jogada)
                    i, j = melhor_jogada
                    cell_center = (origem[0] + j * tamanho_casa + tamanho_casa / 2,
                                   origem[1] + i * tamanho_casa + tamanho_casa / 2)
                    explosion_effects.append(Explosion(cell_center, (0, 200, 255)))
                    if maquina_click_sound:
                        maquina_click_sound.play()
            pygame.time.set_timer(COMPUTER_MOVE_EVENT, 0)
            computer_move_scheduled = False

        # Eventos de clique
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Se estivermos na tela de seleção (usuário não escolheu ainda)
            if usuario is None:
                if botaoX.is_clicked(event.pos):
                    if player_click_sound:
                        player_click_sound.play()
                    usuario = ttt.X
                    # Chama o efeito sonoro do fake load
                    if fake_load_sound:
                        fake_load_sound.play()
                    fake_loading = True
                    fake_load_start = pygame.time.get_ticks()
                elif botaoO.is_clicked(event.pos):
                    if player_click_sound:
                        player_click_sound.play()
                    usuario = ttt.O
                    # Chama o efeito sonoro do fake load
                    if fake_load_sound:
                        fake_load_sound.play()
                    fake_loading = True
                    fake_load_start = pygame.time.get_ticks()
                else:
                    # Clique fora dos botões de seleção
                    explosion_effects.append(Explosion(event.pos, (255, 255, 255)))
                    if player_click_sound:
                        player_click_sound.play()
            else:
                # Se o jogo terminou, aguardando clique no botão "Jogar Novamente"
                if ttt.terminal(tabuleiro):
                    if botaoNovamente.is_clicked(event.pos):
                        if player_click_sound:
                            player_click_sound.play()
                        # Retorna à tela de seleção
                        usuario = None
                        tabuleiro = ttt.estado_inicial()
                        resultado = None
                        fade_time = 0
                        fade_overlay_alpha = 0
                        trilha_interrompida = False
                else:
                    # Durante a partida, se o clique ocorrer na área do tabuleiro:
                    if tabuleiro_area.collidepoint(event.pos):
                        col = int((event.pos[0] - origem[0]) // tamanho_casa)
                        row = int((event.pos[1] - origem[1]) // tamanho_casa)
                        if tabuleiro[row][col] == ttt.EMPTY:
                            if player_click_sound:
                                player_click_sound.play()
                            tabuleiro = ttt.resultado(tabuleiro, (row, col))
                            cell_center = (origem[0] + col * tamanho_casa + tamanho_casa / 2,
                                           origem[1] + row * tamanho_casa + tamanho_casa / 2)
                            explosion_effects.append(Explosion(cell_center, (255, 200, 0)))
                    else:
                        explosion_effects.append(Explosion(event.pos, (255, 255, 255)))
                        if player_click_sound:
                            player_click_sound.play()

    # Se estivermos no fake load, exibe a tela de carregamento
    if fake_loading:
        tela.blit(fundo, (0, 0))
        loading_text = fonteGrande.render("Carregando...", True, branco)
        loading_rect = loading_text.get_rect(center=(largura / 2, altura / 2))
        tela.blit(loading_text, loading_rect)
        pygame.display.flip()
        if pygame.time.get_ticks() - fake_load_start >= FAKE_LOAD_DURATION:
            fake_loading = False
            # Inicia a trilha sonora se ela não estiver tocando (por exemplo, após derrota)
            if trilha_sonora_sound and not trilha_sonora_sound.get_num_channels():
                trilha_sonora_sound.play(-1)
        continue

    # Se estivermos na partida e o jogo terminou, registra o resultado
    if usuario is not None and ttt.terminal(tabuleiro):
        resultado = ttt.vencedor(tabuleiro)  # Pode ser None (empate) ou 'X'/'O'
        # Se o jogador perdeu, interrompe a trilha sonora (se ainda não foi interrompida)
        if resultado is not None and resultado != usuario and not trilha_interrompida:
            if trilha_sonora_sound:
                trilha_sonora_sound.stop()
            if loser_sound:
                loser_sound.play()
            trilha_interrompida = True

    # Agenda a jogada do computador se for a vez e a partida estiver ativa
    if usuario is not None and not ttt.terminal(tabuleiro) and usuario != ttt.jogador(tabuleiro) and not computer_move_scheduled:
        pygame.time.set_timer(COMPUTER_MOVE_EVENT, 1000)  # 1 segundo de "pensamento"
        computer_move_scheduled = True

    # Desenha o fundo
    tela.blit(fundo, (0, 0))

    # Se estivermos na tela de seleção
    if usuario is None:
        titulo_shadow = fonteGrande.render("Jogo da Velha", True, cinza)
        titulo_shadow_rect = titulo_shadow.get_rect(center=(largura / 2 + 2, 60 + 2))
        tela.blit(titulo_shadow, titulo_shadow_rect)
        titulo = fonteGrande.render("Jogo da Velha", True, branco)
        titulo_rect = titulo.get_rect(center=(largura / 2, 60))
        tela.blit(titulo, titulo_rect)
        botaoX.update(mouse_pos)
        botaoO.update(mouse_pos)
        botaoX.draw(tela)
        botaoO.draw(tela)
    else:
        # Desenha o tabuleiro tradicional (grade 3x3)
        pygame.draw.rect(tela, branco, tabuleiro_area, 4)
        # Linhas verticais
        pygame.draw.line(tela, branco,
                         (origem[0] + tamanho_casa, origem[1]),
                         (origem[0] + tamanho_casa, origem[1] + 3 * tamanho_casa), 4)
        pygame.draw.line(tela, branco,
                         (origem[0] + 2 * tamanho_casa, origem[1]),
                         (origem[0] + 2 * tamanho_casa, origem[1] + 3 * tamanho_casa), 4)
        # Linhas horizontais
        pygame.draw.line(tela, branco,
                         (origem[0], origem[1] + tamanho_casa),
                         (origem[0] + 3 * tamanho_casa, origem[1] + tamanho_casa), 4)
        pygame.draw.line(tela, branco,
                         (origem[0], origem[1] + 2 * tamanho_casa),
                         (origem[0] + 3 * tamanho_casa, origem[1] + 2 * tamanho_casa), 4)

        # Efeito de hover: se o mouse estiver sobre uma casa vazia, destaca-a
        if tabuleiro_area.collidepoint(mouse_pos):
            col = int((mouse_pos[0] - origem[0]) // tamanho_casa)
            row = int((mouse_pos[1] - origem[1]) // tamanho_casa)
            if tabuleiro[row][col] == ttt.EMPTY:
                hover_rect = pygame.Rect(origem[0] + col * tamanho_casa,
                                         origem[1] + row * tamanho_casa,
                                         tamanho_casa, tamanho_casa)
                hover_surface = pygame.Surface((tamanho_casa, tamanho_casa), pygame.SRCALPHA)
                hover_surface.fill(hover_color)
                tela.blit(hover_surface, hover_rect.topleft)

        # Desenha os movimentos (X e O) com sombra
        for i in range(3):
            for j in range(3):
                if tabuleiro[i][j] != ttt.EMPTY:
                    simbolo = fonteMovimento.render(tabuleiro[i][j], True, branco)
                    pos = (origem[0] + j * tamanho_casa + tamanho_casa / 2,
                           origem[1] + i * tamanho_casa + tamanho_casa / 2)
                    simbolo_rect = simbolo.get_rect(center=pos)
                    sombra = fonteMovimento.render(tabuleiro[i][j], True, cinza)
                    sombra_rect = sombra.get_rect(center=(pos[0] + 3, pos[1] + 3))
                    tela.blit(sombra, sombra_rect)
                    tela.blit(simbolo, simbolo_rect)

        # Se a partida não terminou, exibe mensagem de turno; caso contrário, exibe resultado e botão
        if not ttt.terminal(tabuleiro):
            if usuario == ttt.jogador(tabuleiro):
                texto_titulo = f"Sua vez ({usuario})"
            else:
                texto_titulo = "Computador pensando..."
            titulo_shadow = fonteGrande.render(texto_titulo, True, cinza)
            titulo_shadow_rect = titulo_shadow.get_rect(center=(largura / 2 + 2, 60 + 2))
            tela.blit(titulo_shadow, titulo_shadow_rect)
            titulo_text = fonteGrande.render(texto_titulo, True, branco)
            titulo_text_rect = titulo_text.get_rect(center=(largura / 2, 60))
            tela.blit(titulo_text, titulo_text_rect)
        else:
            if resultado is None:
                msg = "Fim de jogo: Empate."
            else:
                msg = f"Fim de jogo: {resultado} venceu!"
            msg_shadow = fonteGrande.render(msg, True, cinza)
            msg_shadow_rect = msg_shadow.get_rect(center=(largura / 2 + 2, 60 + 2))
            tela.blit(msg_shadow, msg_shadow_rect)
            msg_text = fonteGrande.render(msg, True, branco)
            msg_text_rect = msg_text.get_rect(center=(largura / 2, 60))
            tela.blit(msg_text, msg_text_rect)
            botaoNovamente.update(mouse_pos)
            botaoNovamente.draw(tela)

            # Se o jogador perdeu, exibe também um efeito de fade vermelho (opcional)
            if resultado is not None and resultado != usuario:
                if fade_time < fade_duration:
                    fade_overlay_alpha = easeOutQuad(fade_time, 0, 200, fade_duration)
                    fade_time += 1
                fade_surface = pygame.Surface((largura, altura))
                fade_surface.set_alpha(int(fade_overlay_alpha))
                fade_surface.fill(vermelho)
                tela.blit(fade_surface, (0, 0))

    # Atualiza e desenha os efeitos de explosão
    for explosion in explosion_effects:
        explosion.update()
        explosion.draw(tela)
    explosion_effects = [exp for exp in explosion_effects if not exp.done]

    pygame.display.flip()

pygame.quit()
sys.exit()

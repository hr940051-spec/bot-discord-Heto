# Bot de Discord recriado a partir do Bot 0.9.py
# Batalhas PvP 4x4, gacha, personagens, perfis, economia e menus.
# Instale: pip install -U discord.py flask
# Configure a variável de ambiente TOKEN com o token do bot.

from __future__ import annotations
import os
import getpass
import json
import random
import copy
import difflib
import unicodedata
import asyncio
import threading
from datetime import date, datetime, timezone
from pathlib import Path

import discord
from discord.ext import commands
from flask import Flask

# -------------------- CONFIGURAÇÃO --------------------
PREFIXO = "!"
TOKEN = os.getenv("TOKEN")
# ID do único canal onde os comandos do jogo serão aceitos. Configure GAME_CHANNEL_ID.
GAME_CHANNEL_ID = int(os.getenv("GAME_CHANNEL_ID", "1564835650581168229") or "1564835650581168229")
ARQUIVO_DADOS = Path(os.getenv("DATA_FILE", "jogadores_data.json"))
CUSTO_GACHA = 50
REEMBOLSO_DUPLICADO = 25
LIMITE_PITY = 50
RECOMPENSA_DIARIA = 100
MOEDAS_INICIAIS = 150
NIVEL_MAXIMO = 50
CUSTO_LIVRO_EXP = 100
CUSTO_CHAVE_FENDA = 100
XP_LIVRO_EXP = 100
# Evento de Halloween 2026: começa no Dia das Bruxas e dura um mês, até 30/11, inclusive.
HALLOWEEN_INICIO = date(2026, 10, 31)
HALLOWEEN_FIM = date(2026, 11, 30)

# Servidor HTTP simples para serviços de hospedagem que exigem uma porta aberta.
app = Flask(__name__)
@app.get("/")
def home():
    return "Bot online!"

def iniciar_servidor_web():
    porta = int(os.getenv("PORT", "10000"))
    threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=porta, use_reloader=False),
        daemon=True,
    ).start()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIXO, intents=intents, help_command=None)

@bot.check
async def limitar_ao_canal_oficial(ctx):
    """Impede que os comandos do jogo sejam usados fora do canal configurado."""
    if ctx.guild is None:
        raise commands.CheckFailure("O jogo só pode ser usado dentro do servidor oficial.")
    if GAME_CHANNEL_ID <= 0:
        raise commands.CheckFailure("O canal do jogo ainda não foi configurado pelo administrador.")
    if ctx.channel.id != GAME_CHANNEL_ID:
        raise commands.CheckFailure(f"O jogo só funciona no canal <#{GAME_CHANNEL_ID}>.")
    return True

# -------------------- PERSONAGENS ORIGINAIS --------------------
PERSONAGENS = {'Tohka Yatogami': {'anime': 'Date A Live', 'classe': 'Saber', 'raridade': 'Rara', 'emoji': '👑', 'hp': 110, 'mana': 40, 'gif': 'https://cdn.imgchest.com/files/5e6e71b85a53.gif', 'ataque_normal': {'nome': 'Corte Espada Astral', 'dano': 16, 'descricao': 'Tohka desfere um golpe veloz com sua espada espiritual.', 'gif': 'https://cdn.imgchest.com/files/63bd7b6baf58.gif'}, 'especial': {'nome': '⚔️ Sandalphon (Corte Final)', 'dano': 32, 'custo_mana': 20, 'descricao': 'Invoca o trono e desfere um golpe devastador.', 'gif': 'https://cdn.imgchest.com/files/17ed046e4e42.gif'}, 'defesa_normal': {'nome': 'Barreira Astral', 'reducao_dano': 0.5, 'descricao': 'Tohka ergue uma barreira de mana.', 'gif': 'https://cdn.imgchest.com/files/a044451a35a3.gif'}}, 'Ken Kaneki': {'anime': 'Tokyo Ghoul', 'classe': 'Berserker', 'raridade': 'Rara', 'emoji': '☕', 'hp': 95, 'mana': 50, 'gif': 'https://cdn.imgchest.com/files/832312a9603b.gif', 'ataque_normal': {'nome': 'Investida de Ghoul', 'dano': 18, 'descricao': 'Kaneki avança rapidamente com as garras.', 'gif': 'https://cdn.imgchest.com/files/74638a34bf9e.gif'}, 'especial': {'nome': '🐙 Liberação de Kagune', 'dano': 28, 'custo_mana': 25, 'descricao': 'Libera seus tentáculos kagune com força total.', 'gif': 'https://cdn.imgchest.com/files/e3b092a368d9.gif'}, 'defesa_normal': {'nome': 'Reflexo Ghoul', 'reducao_dano': 0.5, 'descricao': 'Usa sua agilidade para amortecer o golpe.', 'gif': 'https://cdn.imgchest.com/files/19d84e56d333.gif'}}, 'FIREFLY / SAM': {'anime': 'Honkai: Star Rail', 'classe': 'Rider', 'raridade': 'Epica', 'emoji': '🔥', 'forma': 'normal', 'hp': 120, 'hp_max': 120, 'mana': 45, 'gif': 'https://cdn.imgchest.com/files/ae04c3cc283d.gif', 'ataque_normal': {'nome': 'Ordem Estelar (Ataque)', 'dano': 15, 'descricao': 'Firefly desfere um golpe ágil com a lâmina de energia.', 'gif': 'https://cdn.imgchest.com/files/fd6fe2ef8713.gif'}, 'especial': {'nome': 'Incandescência Completa (Transformação)', 'dano': 25, 'custo_mana': 20, 'efeito': 'transformar_sam', 'descricao': 'Firefly liberta o seu verdadeiro poder, vestindo a armadura SAM!', 'gif': 'https://cdn.imgchest.com/files/a65144462508.gif'}, 'defesa_normal': {'nome': 'Evasão Tática', 'reducao_dano': 0.5, 'descricao': 'Firefly recua rapidamente da investida inimiga.', 'gif': 'https://cdn.imgchest.com/files/f41d858423eb.gif'}, 'ataque_sam': {'nome': 'Bombardeio Férreo (Ataque SAM)', 'dano': 35, 'descricao': 'SAM despenca dos céus envolto em chamas verdes esmagadoras.', 'gif': 'https://cdn.imgchest.com/files/a07562dec10a.gif'}, 'especial_sam': {'nome': 'Desativar Combustão', 'dano': 0, 'custo_mana': 10, 'efeito': 'transformar_normal', 'descricao': 'SAM descarrega um feixe massivo de chamas antes de voltar à base.', 'gif': 'https://cdn.imgchest.com/files/5125e6e1b780.gif'}, 'defesa_sam': {'nome': 'Campo de Força / Barreira Kael', 'reducao_dano': 0.7, 'descricao': 'SAM projeta um escudo de energia térmica frontal.', 'gif': 'https://cdn.imgchest.com/files/57e44b73bbbe.gif'}}, 'Sasuke Uchiha': {'classe': 'Archer', 'raridade': 'Rara', 'emoji': '⚡', 'anime': 'Naruto', 'hp': 100, 'mana': 50, 'gif': 'https://cdn.imgchest.com/files/daec3a69715a.gif', 'ataque_normal': {'nome': 'Estilo Fogo: Jutsu Bola de Fogo', 'dano': 18, 'descricao': 'Sasuke lança uma esfera de fogo devastadora contra o oponente.', 'gif': 'https://cdn.imgchest.com/files/ed473b565a65.gif'}, 'especial': {'nome': ' Chidori (Mil Pássaros)', 'dano': 32, 'custo_mana': 25, 'descricao': 'Concentra chakra de raio na mão e avança em alta velocidade.', 'gif': 'https://cdn.imgchest.com/files/0943da111e8e.gif'}, 'defesa_normal': {'nome': 'Previsão do Sharingan', 'reducao_dano': 0.5, 'descricao': 'Usa o Sharingan para prever os movimentos e esquivar do impacto.', 'gif': 'https://cdn.imgchest.com/files/e82c844b2168.gif'}}, 'White Queen': {'anime': 'Date A Bullet', 'classe': 'Caster', 'raridade': 'Epica', 'emoji': '♟️', 'hp': 140, 'mana': 50, 'gif': 'https://cdn.imgchest.com/files/a09a20995cf4.gif', 'ataque_normal': {'nome': 'Corte de Lugh 🗡️', 'dano': 17, 'descricao': 'White Queen desfere um golpe veloz e gélido com a sua espada.', 'gif': 'https://cdn.imgchest.com/files/c421a3755412.gif'}, 'especial': {'nome': '👑 Xeque-Mate (Decreto Absoluto)', 'dano': 38, 'custo_mana': 20, 'descricao': 'Invoca o poder do tabuleiro para aplicar um golpe devastador que esmaga o inimigo.', 'gif': 'https://cdn.imgchest.com/files/0d255a84ea3a.gif'}, 'defesa_normal': {'nome': 'Barreira do Tabuleiro', 'reducao_dano': 0.5, 'descricao': 'White Queen se protege com o poder de suas peças.', 'gif': 'https://cdn.imgchest.com/files/b628f2923d42.gif'}, 'mecanica_unica': 'xeque_mate'}, 'Kirara': {'anime': 'Jujutsu Kaisen', 'classe': 'Estrategista', 'raridade': 'Epica', 'emoji': '⭐', 'hp': 120, 'mana': 50, 'gif': 'https://cdn.imgchest.com/files/88b405a50359.gif', 'ataque_normal': {'nome': 'Chuva de Moedas', 'dano': 20, 'descricao': 'Kirara atira moedas como balas contra o oponente.', 'gif': 'https://cdn.imgchest.com/files/93aa2b06313e.mp4'}, 'especial': {'nome': 'Repulsão Estelar', 'dano': 45, 'custo_mana': 20, 'descricao': 'Repeli tudo em cima do oponente.', 'gif': 'https://cdn.imgchest.com/files/0f672887d950.mp43'}, 'defesa_normal': {'nome': 'Alinhamento das 5 Estrelas', 'reducao_dano': 0.6, 'descricao': 'Junta as 5 estrelas para criar uma defesa absoluta.', 'gif': 'https://cdn.imgchest.com/files/3e0ad0d472cc.gif'}}, 'Maomao': {'anime': 'The Apothecary Diaries', 'classe': 'Caster', 'raridade': 'Lendaria', 'emoji': '🧪', 'hp': 130, 'mana': 60, 'gif': 'https://cdn.imgchest.com/files/fb9f99ad5dda.gif', 'ataque_normal': {'nome': 'Ofensa Ácida', 'dano': 15, 'descricao': 'Maomao ofende o oponente com duras verdades, causando pouco dano direto, mas reduzindo a defesa dele.', 'gif': 'https://cdn.imgchest.com/files/f858bd5d68fa.mp4'}, 'especial': {'nome': 'Envenenamento', 'dano': 35, 'custo_mana': 25, 'descricao': 'Usa venenos potentes: causa dano a si mesma, mas anula totalmente a defesa do inimigo por 1 a 2 rounds.', 'gif': 'https://cdn.imgchest.com/files/45606d6bbd42.gif'}, 'defesa_normal': {'nome': 'Experimento Medicinal', 'reducao_dano': 0.7, 'descricao': 'Testa venenos em si mesma: 50% de chance de mitigar 70% do dano (com auto-envenenamento), 30% de falha e 20% de imunidade total por 2 turnos.', 'gif_sucesso': 'https://cdn.imgchest.com/files/a56c92b9b3de.gif', 'gif_falha': 'https://cdn.imgchest.com/files/601987286d86.mp4'}, 'mecanica_unica': 'envenenamento_maomao'}}


# -------------------- NOVOS PERSONAGENS --------------------
def ficha(anime, classe, raridade, emoji, hp, mana, gif, ataque, especial, defesa, mecanica=None, passiva=None):
    d={"anime":anime,"classe":classe,"raridade":raridade,"emoji":emoji,"hp":hp,"mana":mana,"gif":gif,
       "ataque_normal":ataque,"especial":especial,"defesa_normal":defesa}
    if mecanica: d["mecanica_unica"]=mecanica
    if passiva: d["passiva"]=passiva
    return d

PERSONAGENS.update({
"Medusa": ficha("Fate","Rider","Lendaria","🐍",110,50,"https://tenor.com/bpjJ2.gif",
 {"nome":"Olhar da Górgona","dano":17,"descricao":"Dano médio; 10% de chance de sangrar por 2 turnos.","gif":"https://tenor.com/bpjJ2.gif"},
 {"nome":"Petrificação","dano":32,"custo_mana":22,"efeito":"petrificacao_medusa","descricao":"Ganha 2 pontos; com 5 pontos pode paralisar por 2 turnos.","gif":"https://tenor.com/bJzmE.gif"},
 {"nome":"Esquiva da Górgona","reducao_dano":0.15,"descricao":"25% de esquiva; com 5 pontos, 50% de esquiva e 15% de redução.","gif":"https://tenor.com/bq2GE.gif"},"petrificacao_medusa"),
"Osamu Dazai": ficha("Bungou Stray Dogs","Controlador","Lendaria","🩹",105,60,"https://klipy.com/gifs/dazai-wow",
 {"nome":"Convite ao Duplo Suicídio","dano":5,"descricao":"Causa 5 de dano por desconforto.","gif":"https://klipy.com/gifs/dazai-osamu-dance"},
 {"nome":"Não Mais Humano","dano":0,"custo_mana":25,"efeito":"dazai_bloqueio","descricao":"Zera a mana de até 2 inimigos e bloqueia seus especiais por 3 turnos.","gif":"https://klipy.com/gifs/dazai-wow"},
 {"nome":"Não Mais Humano","reducao_dano":0,"descricao":"Anula efeitos especiais e alterações de status; ataques comuns ainda causam dano.","gif":"https://klipy.com/gifs/dazai-wow"},"nulificacao_dazai"),
"Saber": ficha("Fate","Saber","Lendaria","⚔️",125,55,"https://tenor.com/20I5OcAeBE.gif",
 {"nome":"Espada Invisível","dano":17,"descricao":"Dano aleatório de 12, 17 ou 21; após 3 ataques, passa a causar 27.","gif":"https://tenor.com/bWKZNll93Lx.gif"},
 {"nome":"EXCALIBUR","dano":42,"custo_mana":30,"efeito":"excalibur_saber","descricao":"Disponível após revelar a espada; golpe muito alto e reinicia o modo oculto.","gif":"https://tenor.com/kCZDUXhuaP8.gif"},
 {"nome":"Guarda de Saber","reducao_dano":0.35,"descricao":"Reduz o dano recebido.","gif":"https://tenor.com/h5iuDlC4q4m.gif"},"espada_revelada_saber"),
"Barou": ficha("Blue Lock","Atacante","Epica","👑",115,45,"https://tenor.com/rc296WIxa6n.gif",
 {"nome":"Instinto de Predador","dano":5,"efeito":"barou_percentual","descricao":"Causa cerca de 5% da vida atual do alvo.","gif":"https://tenor.com/rc296WIxa6n.gif"},
 {"nome":"Devour","dano":23,"custo_mana":18,"efeito":"devour_barou","descricao":"23 de dano; se derrotar o alvo, rouba 20% do ataque dele para fortalecer futuros especiais nesta batalha.","gif":"https://tenor.com/kCZDUXhuaP8.gif"},
 {"nome":"Postura do Rei","reducao_dano":0.3,"descricao":"Reduz o dano recebido.","gif":"https://tenor.com/h5iuDlC4q4m.gif"},"devorador_barou"),
"Anya (Mouthwashing)": ficha("Mouthwashing","Suporte","Rara","🩺",100,65,"https://klipy.com/gifs/anya-mouthwashing-18",
 {"nome":"Diagnóstico de Depressão","dano":1,"efeito":"anya_atordoamento","descricao":"A tristeza faz o alvo perder a próxima ação.","gif":"https://klipy.com/gifs/mouthwashing-game-mouthwashing-wrong-organ"},
 {"nome":"Protocolo de Emergência","dano":0,"custo_mana":25,"efeito":"anya_salvamento","descricao":"Uma vez por batalha impede a morte de um aliado (fica com 50% da vida máxima) e cura 20% da vida máxima de um aliado com 25% de vida ou menos.","gif":"https://klipy.com/gifs/mouthwashing-anya-anya-mouthwashing"},
 {"nome":"Analgésico e Porta Trancada","reducao_dano":1.0,"descricao":"Recupera 50% da própria vida e garante proteção nesta rodada.","gif":"https://klipy.com/gifs/anya-shocked-anya-hand-over-mouth"},"suporte_anya"),
"Bayonetta": ficha("Bayonetta","DPS","Lendaria","🔫",115,50,"https://klipy.com/gifs/bayonetta-7",
 {"nome":"Ebony & Ivory","dano":18,"descricao":"Dispara com suas duas pistolas.","gif":"https://klipy.com/gifs/bayonetta-bayonetta2-11"},
 {"nome":"Forma Final","dano":25,"custo_mana":25,"efeito":"bayonetta_percentual","descricao":"Causa 25% da vida atual do alvo; 10% de chance de causar 50%.","gif":"https://klipy.com/gifs/bayonetta3-bayonetta"},
 {"nome":"Cabelos Demoníacos","reducao_dano":0.2,"descricao":"Reduz o dano recebido em 20%.","gif":"https://klipy.com/gifs/bayonetta-bayonetta2-10"},"witch_bayonetta"),
"Robin": ficha("Honkai: Star Rail","Suporte","Lendaria","🎤",105,70,"https://tenor.com/nMLCqHUsW6R.gif",
 {"nome":"Nota Harmoniosa","dano":14,"descricao":"Ataque musical simples.","gif":"https://tenor.com/iUND6KND8CL.gif"},
 {"nome":"Concerto de Robin","dano":0,"custo_mana":30,"efeito":"robin_buff","descricao":"Por 5 turnos, aliados recuperam 5 HP por turno; Robin e aliados recuperam 3 de mana por turno. Não renova enquanto ativo.","gif":"https://tenor.com/eUkUM989V5G.gif"},
 {"nome":"Passo de Dança","reducao_dano":0.3,"descricao":"Evita parte do impacto.","gif":"https://tenor.com/dkqw7qWlmtv.gif"},"concerto_robin"),
"Cyrene": ficha("Honkai: Star Rail","Suporte","Epica","🌸",110,60,"https://tenor.com/l0y3Sm1XYBc.gif",
 {"nome":"Lâmina de Memórias","dano":16,"descricao":"Ataque básico equilibrado.","gif":"https://tenor.com/dhErIqEVhtO.gif"},
 {"nome":"Crescendo de Poder","dano":0,"custo_mana":20,"efeito":"cyrene_bonus","descricao":"Cada uso aumenta o próprio dano em 2%, até +15%.","gif":"https://tenor.com/qeZ7qUEu6tk.gif"},
 {"nome":"Véu Protetor","reducao_dano":0.25,"descricao":"Reduz o dano recebido.","gif":"https://tenor.com/tEEfrGmnVK6.gif"},"lideranca_cyrene","Ao iniciar: aliados causam +30% de dano até 2 turnos depois de Cyrene sair do campo; inimigos causam 5% menos dano durante a batalha."),
"Jolyne Cujoh": ficha("JoJo's Bizarre Adventure","DPS","Epica","🕸️",115,45,"https://klipy.com/gifs/jolyne-jolyne-cujoh-1",
 {"nome":"Chutão","dano":22,"efeito":"jolyne_chance","descricao":"60% de chance de acertar; 40% de chance de o inimigo desviar.","gif":"https://klipy.com/gifs/jolyne-cujoh-cmoon"},
 {"nome":"Stone Free: ORA ORA ORA!","dano":42,"custo_mana":25,"descricao":"Sequência de socos repetidos com dano alto.","gif":"https://klipy.com/gifs/jojos-bizarre-adventure-jolyne"},
 {"nome":"Guarda Stone Free","reducao_dano":0.35,"descricao":"Usa o Stand para reduzir o dano recebido.","gif":"https://c.tenor.com/MXPxvBLD_h8AAAAC/tenor.gif"},"stone_free_jolyne"),
"Dante": ficha("Devil May Cry","DPS versátil","Lendaria","🔴",130,60,"https://klipy.com/gifs/dante-dante-devil-may-cry5",
 {"nome":"Quatro Estilos","dano":24,"efeito":"dante_estilos","descricao":"Escolhe aleatoriamente Swordmaster (28 de dano), Gunslinger (15 em todos os inimigos), Trickster (reduz a defesa inimiga em 30% e esquiva do próximo ataque recebido) ou Royal Guard (armazena o dano recebido para contra-atacar); pode repetir.","gif":"https://klipy.com/gifs/stinger-dante"},
 {"nome":"Sin Devil Trigger","dano":36,"custo_mana":30,"efeito":"sin_devil_trigger","descricao":"A partir da segunda ação de Dante na batalha, tem 40% de chance de dobrar o dano deste especial e atingir todos os inimigos vivos. Se falhar, não causa dano.","gif":"https://klipy.com/gifs/dante-dante-devil-may-cry5"},
 {"nome":"Esquiva Demoníaca","reducao_dano":0.3,"descricao":"Reduz o dano recebido com agilidade.","gif":"https://klipy.com/gifs/dmc5-royal-guard"},"quatro_estilos_dante"),
"Itachi Uchiha": ficha("Naruto Shippuden","Controlador","Lendaria","🔥",115,60,"https://klipy.com/gifs/uchiha-itachi-anime-mdk",
 {"nome":"Amaterasu: Chamas Negras","dano":16,"efeito":"amaterasu_itachi","descricao":"80% de chance de acertar; remove bônus e queima por 10% da vida máxima durante 1 turno.","gif":"https://klipy.com/gifs/uchiha-itachi-anime-mdk"},
 {"nome":"Susanoo: Espelho Yata e Espada Totsuka","dano":0,"custo_mana":25,"efeito":"susanoo_itachi","descricao":"Arma o Espelho Yata para sobreviver ao primeiro golpe fatal e a Espada Totsuka para selar um inimigo se for derrotado depois.","gif":"https://klipy.com/gifs/itachi-susano"},
 {"nome":"Espelho Yata","reducao_dano":0.4,"descricao":"Reduz o dano recebido; a ativação do Susanoo dissipa status negativos.","gif":"https://klipy.com/gifs/itachi-susano"},"amaterasu_susanoo_itachi")
})

# Personagens adicionados para a próxima rodada de testes.
PERSONAGENS.update({
"Columbina": ficha("Genshin Impact", "Suporte Lunar", "Lendaria", "🌙", 110, 70,
 "https://tenor.com/search/columbina-genshin-impact-gifs",
 {"nome":"Toque da Lua","dano":16,"descricao":"Um golpe lunar que marca o alvo para o próximo aliado causar dano adicional.","efeito":"columbina_marca","gif":"https://tenor.com/search/columbina-genshin-impact-gifs"},
 {"nome":"Domínio Lunar","dano":0,"custo_mana":30,"efeito":"columbina_dominio","descricao":"Por 2 turnos, aliados vivos causam 20% a mais de dano.","gif":"https://tenor.com/search/columbina-genshin-impact-gifs"},
 {"nome":"Véu da Lua","reducao_dano":0.4,"descricao":"Reduz 40% do dano recebido.","gif":"https://tenor.com/search/columbina-genshin-impact-gifs"},
 "columbina_lunar","Uma vez por batalha, quando um aliado sofreria um golpe fatal, a Lua o revive com 30% da vida máxima."),
"Kafka": ficha("Honkai: Star Rail", "DPS / Dano contínuo", "Lendaria", "⚡", 115, 65,
 "https://tenor.com/search/kafka-honkai-star-rail-gifs",
 {"nome":"Sussurro da Meia-Noite","dano":18,"efeito":"kafka_choque","descricao":"Causa dano elétrico e tem 50% de chance de aplicar Choque por 2 turnos.","gif":"https://tenor.com/search/kafka-honkai-star-rail-gifs"},
 {"nome":"Carícia da Lua Caída","dano":27,"custo_mana":25,"efeito":"kafka_detonacao","descricao":"Atinge o alvo e todos os inimigos vivos; detona imediatamente o dano contínuo já aplicado aos alvos.","gif":"https://tenor.com/search/kafka-honkai-star-rail-gifs"},
 {"nome":"Passo Silencioso","reducao_dano":0.35,"descricao":"Reduz 35% do dano recebido.","gif":"https://tenor.com/search/kafka-honkai-star-rail-gifs"},
 "kafka_dano_continuo","Uma vez por batalha, quando um aliado causa dano, Kafka tem 20% de chance de executar um ataque de acompanhamento." )
})

# Ajustes de versões e personagens já existentes, sem alterar dados persistidos.
PERSONAGENS["Tohka Yatogami"].update({
 "mecanica_unica":"tohka_normal_evolucao_futura",
 "ataque_normal":{"nome":"Corte de Sandalphon","dano":20,"descricao":"Tohka normal ataca com sua espada; Inverse Tohka fica reservada para uma evolução futura.","gif":"https://cdn.imgchest.com/files/63bd7b6baf58.gif"},
 "especial":{"nome":"Halvanhelev: Espada Final","dano":30,"dano_chefe":45,"custo_mana":30,"descricao":"Corte de energia que atinge todos os inimigos.","gif":"https://cdn.imgchest.com/files/17ed046e4e42.gif"},
 "defesa_normal":{"nome":"Vestido Astral","reducao_dano":0.4,"descricao":"Reduz 40% do dano recebido.","gif":"https://cdn.imgchest.com/files/a044451a35a3.gif"}})
PERSONAGENS["Ken Kaneki"].update({"mecanica_unica":"kaneki_inicio_historia","passiva":"Abaixo de 40% da vida, ataques básicos causam +20% e curam parte do dano causado."})
PERSONAGENS["Sasuke Uchiha"].update({
 "anime":"Naruto Shippuden","mecanica_unica":"sharingan_sasuke","passiva":"Sharingan: 15% de chance de esquivar; seus especiais marcam o alvo para receber +10% do próximo ataque aliado.",
 "ataque_normal":{"nome":"Chidori","dano":20,"descricao":"Investida elétrica; 25% de chance de atordoar por 1 turno.","gif":"https://cdn.imgchest.com/files/0943da111e8e.gif"},
 "especial":{"nome":"Amaterasu: Chamas Negras","dano":18,"custo_mana":25,"efeito":"amaterasu_sasuke","descricao":"Causa dano e queimadura por 2 turnos, reduzindo a defesa em 20%.","gif":"https://cdn.imgchest.com/files/ed473b565a65.gif"},
 "defesa_normal":{"nome":"Susanoo","reducao_dano":0.45,"descricao":"Reduz 45% do dano recebido.","gif":"https://cdn.imgchest.com/files/e82c844b2168.gif"}})
PERSONAGENS["FIREFLY / SAM"].update({"mecanica_unica":"transformacao_firefly","passiva":"No modo SAM, ataques ficam mais fortes e a personagem sofre queimadura progressiva ao fim dos próprios turnos."})
PERSONAGENS["Kirara"].update({"mecanica_unica":"cinco_estrelas_kirara","passiva":"Após duas defesas, a próxima defesa garante zero dano durante a rodada; depois o contador reinicia."})
PERSONAGENS["Maomao"].update({"passiva":"Foco defensivo: enfraquece ataque e defesa inimigos; sua defesa tem 50% de proteção, 30% de falha e 20% de imunidade temporária."})
PERSONAGENS["Tohka Yatogami"].update({"passiva":"Ao derrotar um inimigo, recupera 10% da vida máxima."})
PERSONAGENS["White Queen"].update({"passiva":"Seu especial atinge todos os inimigos vivos."})
PERSONAGENS["Medusa"].update({"passiva":"Acumula pontos de petrificação; ataques e defesas podem esquivar e fortalecer a próxima ação."})
PERSONAGENS["Osamu Dazai"].update({"passiva":"Anula efeitos de status quando é atingido; seus especiais bloqueiam a energia dos inimigos."})
PERSONAGENS["Saber"].update({"passiva":"Após três ataques básicos, revela a espada e fortalece os ataques até usar EXCALIBUR."})
PERSONAGENS["Barou"].update({"passiva":"Seu ataque básico escala com a vida atual do alvo; ao derrotar alguém, fortalece os próximos especiais."})
PERSONAGENS["Anya (Mouthwashing)"].update({"passiva":"Seu especial pode impedir uma derrota fatal uma vez por batalha e curar um aliado muito ferido."})
PERSONAGENS["Bayonetta"].update({"passiva":"Seu especial causa dano percentual à vida atual do alvo, com chance de dano aumentado."})
PERSONAGENS["Robin"].update({"passiva":"O Concerto cura aliados e recupera mana por 5 turnos."})
PERSONAGENS["Cyrene"].update({"passiva":"A equipe começa com bônus ofensivo e redução do dano causado pelos inimigos; ela também acumula poder próprio."})
PERSONAGENS["Jolyne Cujoh"].update({"passiva":"Seu ataque básico tem 60% de chance de acertar; caso contrário, o alvo desvia."})
PERSONAGENS["Dante"].update({"passiva":"Alterna estilos de combate aleatórios e pode preparar contra-ataques ou esquivas."})
PERSONAGENS["Itachi Uchiha"].update({"passiva":"O Susanoo pode bloquear um golpe fatal e selar o inimigo que o derrotar."})

# -------------------- DADOS PERSISTENTES --------------------
def carregar_dados():
    try:
        if ARQUIVO_DADOS.exists():
            with ARQUIVO_DADOS.open("r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
                return dados if isinstance(dados, dict) else {}
    except (OSError, json.JSONDecodeError) as erro:
        print(f"Não foi possível carregar {ARQUIVO_DADOS}: {erro}")
    return {}

JOGADORES = carregar_dados()


def salvar_dados():
    temporario = ARQUIVO_DADOS.with_suffix(ARQUIVO_DADOS.suffix + ".tmp")
    try:
        with temporario.open("w", encoding="utf-8") as arquivo:
            json.dump(JOGADORES, arquivo, ensure_ascii=False, indent=2)
        temporario.replace(ARQUIVO_DADOS)
    except OSError as erro:
        print(f"Não foi possível salvar os dados: {erro}")


def obter_perfil(user_id):
    uid = str(user_id)
    if uid not in JOGADORES:
        JOGADORES[uid] = {
            "moedas": MOEDAS_INICIAIS,
            "inventario": [nome for nome in ["Tohka Yatogami", "Ken Kaneki", "Anya (Mouthwashing)", "Sasuke Uchiha"] if nome in PERSONAGENS],
            "personagem_selecionado": "Tohka Yatogami",
            "pity": 0,
            "ultimo_diario": "",
            "personagens_dados": {},
            "vitorias": 0,
            "derrotas": 0,
        }
        salvar_dados()
    perfil = JOGADORES[uid]
    perfil.setdefault("moedas", MOEDAS_INICIAIS)
    perfil.setdefault("inventario", [])
    perfil.setdefault("personagem_selecionado", perfil["inventario"][0] if perfil["inventario"] else None)
    perfil.setdefault("pity", 0)
    perfil.setdefault("ultimo_diario", "")
    perfil.setdefault("personagens_dados", {})
    perfil.setdefault("itens", {})
    perfil.setdefault("vitorias", 0)
    perfil.setdefault("derrotas", 0)
    # Campos adicionados sem apagar perfis antigos.
    perfil.setdefault("fase_desbloqueada", 1)
    perfil.setdefault("chaves_fenda", 0)
    perfil.setdefault("fases_concluidas", [])
    perfil.setdefault("doces_halloween", 0)
    perfil.setdefault("ultimo_halloween", "")
    return perfil


def obter_dados_progressao(perfil, nome):
    """Retorna o progresso individual sem substituir dados já existentes."""
    progresso = perfil.setdefault("personagens_dados", {}).setdefault(nome, {})
    progresso.setdefault("nivel", 1)
    progresso.setdefault("xp", 0)
    progresso["nivel"] = max(1, min(NIVEL_MAXIMO, int(progresso.get("nivel", 1))))
    progresso["xp"] = max(0, int(progresso.get("xp", 0)))
    if progresso["nivel"] >= NIVEL_MAXIMO:
        progresso["xp"] = 0
    return progresso


def xp_necessario(nivel):
    return 100 * max(1, int(nivel))


def conceder_xp(perfil, nome, quantidade):
    progresso = obter_dados_progressao(perfil, nome)
    if progresso["nivel"] >= NIVEL_MAXIMO:
        return 0, progresso["nivel"]
    progresso["xp"] += max(0, int(quantidade))
    subiu = 0
    while progresso["nivel"] < NIVEL_MAXIMO and progresso["xp"] >= xp_necessario(progresso["nivel"]):
        progresso["xp"] -= xp_necessario(progresso["nivel"])
        progresso["nivel"] += 1
        subiu += 1
    if progresso["nivel"] >= NIVEL_MAXIMO:
        progresso["xp"] = 0
    return subiu, progresso["nivel"]


def dados_personagem(nome):
    return PERSONAGENS.get(nome, {})


def raridade_gacha(nome):
    """Converte a raridade cadastrada em uma categoria distinta do gacha."""
    raridade = str(dados_personagem(nome).get("raridade", "Comum")).strip().casefold()
    normalizada = raridade.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    if normalizada in ("lendaria", "5 estrelas", "5_estrelas", "lendario"):
        return "5_estrelas"
    if normalizada in ("epica", "4 estrelas", "4_estrelas"):
        return "4_estrelas"
    if normalizada in ("rara", "3 estrelas", "3_estrelas"):
        return "3_estrelas"
    if normalizada in ("mitica", "mitico", "mythic"):
        return "mitico"  # Categoria exclusiva do portal; não entra no gacha normal.
    return "2_estrelas"  # Comum ou raridade ausente/desconhecida


def emoji_raridade(categoria):
    return {
        "5_estrelas": "⭐⭐⭐⭐⭐ LENDÁRIA",
        "4_estrelas": "⭐⭐⭐⭐ ÉPICA",
        "3_estrelas": "⭐⭐⭐ RARA",
        "2_estrelas": "⭐⭐ COMUM",
    }.get(categoria, "⭐")


def sortear_personagem(perfil):
    pool = {"5_estrelas": [], "4_estrelas": [], "3_estrelas": [], "2_estrelas": []}
    for nome in PERSONAGENS:
        categoria_personagem = raridade_gacha(nome)
        # Míticos são exclusivos do portal e nunca podem sair no gacha normal.
        if categoria_personagem in pool:
            pool[categoria_personagem].append(nome)
    perfil["pity"] = int(perfil.get("pity", 0)) + 1
    if perfil["pity"] >= LIMITE_PITY and pool["5_estrelas"]:
        categoria = "5_estrelas"
        perfil["pity"] = 0
        motivo = "Pity ativado! Garantia de personagem lendário."
    else:
        # Pesos-base: Comum 50%, Rara 30%, Épica 15%, Lendária 5%.
        categorias = ["2_estrelas", "3_estrelas", "4_estrelas", "5_estrelas"]
        pesos = [50, 30, 15, 5]
        validas = [(cat, peso) for cat, peso in zip(categorias, pesos) if pool[cat]]
        categoria = random.choices([x[0] for x in validas], weights=[x[1] for x in validas], k=1)[0]
        motivo = f"Pity: {perfil['pity']}/{LIMITE_PITY}"
        if categoria == "5_estrelas":
            perfil["pity"] = 0
            motivo = "Personagem lendário obtido! Pity reiniciado."
    return random.choice(pool[categoria]), categoria, motivo

# Falas originais de apresentação para os perfis. Não são citações oficiais das obras.
FALAS_PERSONAGENS = {
    'Tohka Yatogami': '“Enquanto eu puder proteger quem amo, continuarei lutando.”',
    'Ken Kaneki': '“Mesmo quebrado, ainda posso escolher quem quero ser.”',
    'FIREFLY / SAM': '“Meu tempo é limitado; por isso, cada batalha precisa valer a pena.”',
    'Sasuke Uchiha': '“Não vou parar até alcançar o objetivo que escolhi.”',
    'White Queen': '“No meu tabuleiro, cada movimento tem um preço.”',
    'Kirara': '“Siga as estrelas com cuidado: nem todo caminho leva ao destino esperado.”',
    'Maomao': '“Antes de tirar conclusões, prefiro descobrir qual é o veneno.”',
    'Medusa': '“Não confunda meu silêncio com fraqueza; ainda sei como encerrar esta luta.”',
    'Osamu Dazai': '“Até o plano mais absurdo pode funcionar quando ninguém prevê o próximo passo.”',
    'Saber': '“Minha espada não vacilará enquanto houver alguém para proteger.”',
    'Barou': '“O campo é meu reino; quem quiser vencer terá de me superar.”',
    'Anya (Mouthwashing)': '“Às vezes, sobreviver já é a decisão mais difícil.”',
    'Bayonetta': '“Se a noite quer espetáculo, então que comece a dança.”',
    'Robin': '“Cada nota guarda uma lembrança; juntas, elas podem mudar o destino.”',
    'Cyrene': '“Toda memória deixa um eco — e todo eco pode se tornar força.”',
    'Jolyne Cujoh': '“Não vou deixar que decidam meu destino por mim.”',
    'Dante': '“O que me move não é o destino… é a minha própria vontade.”',
    'Itachi Uchiha': '“A verdadeira força também está no que escolhemos carregar em silêncio.”',
 }
for _nome_personagem, _fala_personagem in FALAS_PERSONAGENS.items():
    if _nome_personagem in PERSONAGENS:
        PERSONAGENS[_nome_personagem]["fala"] = _fala_personagem

# -------------------- FERRAMENTAS DE EMBED --------------------
def embed_personagem(nome):
    dados = dados_personagem(nome)
    raridade = dados.get("raridade", "Comum")
    categoria = raridade_gacha(nome)
    estrelas = {"5_estrelas": "⭐⭐⭐⭐⭐", "4_estrelas": "⭐⭐⭐⭐", "3_estrelas": "⭐⭐⭐", "2_estrelas": "⭐⭐", "mitico": "🌌 MÍTICO"}.get(categoria, "⭐")
    descricao = f"**Anime:** {dados.get('anime', 'Desconhecido')}\n**Classe:** {dados.get('classe', 'Guerreiro')}\n**Raridade:** {estrelas} {raridade}"
    exclusivo_portal = categoria == "mitico" or bool(dados.get("exclusivo_portal"))
    if exclusivo_portal:
        descricao += "\n**Obtenção:** 🔒 Exclusivo do Portal — não aparece no gacha normal."
    embed = discord.Embed(
        title=f"{dados.get('emoji', '🎭')} {nome}",
        description=descricao,
        color={"5_estrelas": discord.Color.gold(), "4_estrelas": discord.Color.purple(), "3_estrelas": discord.Color.blue(), "2_estrelas": discord.Color.light_grey(), "mitico": discord.Color.dark_purple()}.get(categoria, discord.Color.blurple()),
    )
    fala = dados.get("fala")
    if fala:
        embed.add_field(name="💬 Fala do personagem", value=f"*{fala}*", inline=False)
    embed.add_field(name="❤️ HP", value=str(dados.get("hp", 100)))
    embed.add_field(name="💧 Mana", value=str(dados.get("mana", 50)))
    ataque = dados.get("ataque_normal", {})
    especial = dados.get("especial", {})
    defesa = dados.get("defesa_normal", {})
    embed.add_field(name=f"⚔️ {ataque.get('nome', 'Ataque normal')}", value=f"Dano: {ataque.get('dano', 10)}\n{ataque.get('descricao', '')}", inline=False)
    embed.add_field(name=f"✨ {especial.get('nome', 'Especial')}", value=f"Dano: {especial.get('dano', 20)} | Custo: {especial.get('custo_mana', 20)} mana\n{especial.get('descricao', '')}", inline=False)
    embed.add_field(name=f"🛡️ {defesa.get('nome', 'Defesa')}", value=defesa.get("descricao", "Reduz o dano recebido no próximo ataque."), inline=False)
    if dados.get("passiva"):
        embed.add_field(name="🌟 Passiva", value=dados["passiva"], inline=False)
    imagem = dados.get("imagem_padrao") or dados.get("gif")
    if imagem and str(imagem).startswith("http"):
        embed.set_image(url=imagem)
    return embed

# -------------------- COMBATE 4x4 --------------------
class PersonagemCombate:
    def __init__(self, nome, nivel=1):
        self.nome_chave = nome
        self.dados = copy.deepcopy(PERSONAGENS[nome])
        self.nome = nome
        self.nivel = max(1, min(NIVEL_MAXIMO, int(nivel)))
        bonus_hp = (self.nivel - 1) * 2
        bonus_dano = (self.nivel - 1) // 5
        self.hp_max = int(self.dados.get("hp_max", self.dados.get("hp", 100))) + bonus_hp
        self.hp = self.hp_max
        self.mana_max = int(self.dados.get("mana", 50)) + ((self.nivel - 1) // 5)
        self.mana = self.mana_max
        # Bônus de dano gradual: +1 a cada 5 níveis, aplicado às ações com dano fixo.
        if bonus_dano:
            for chave in ("ataque_normal", "especial", "ataque_sam", "especial_sam"):
                acao = self.dados.get(chave)
                if isinstance(acao, dict) and isinstance(acao.get("dano"), (int, float)) and acao.get("dano", 0) > 0:
                    acao["dano"] = int(acao["dano"]) + bonus_dano
        self.defendendo = False
        self.forma = self.dados.get("forma", "normal")
        self.bloqueio_especial = False
        self.status = {}
        self.status_turnos = {}
        self.pontos_petrificacao = 0
        self.ataques_saber = 0
        self.espada_revelada = False
        self.bonus_especial_barou = 0
        self.defesas_kirara = 0
        self.bonus_dano_proprio = 0
        self.yata_disponivel = False
        self.totsuka_ativa = False
        self.imunidade_turnos = 0
        self.anya_salvamento_usado = False
        self.royal_guard = False
        self.royal_guard_dano = 0
        self.esquiva_total = False
        self.acoes_realizadas = 0
        self.defesa_forcada = None
        self.kafka_acionou_rodada = False

    def vivo(self):
        return self.hp > 0

    def ataque(self):
        if self.nome_chave == "FIREFLY / SAM" and self.forma == "sam":
            return self.dados.get("ataque_sam", self.dados.get("ataque_normal", {}))
        return self.dados.get("ataque_normal", {})

    def especial(self):
        if self.nome_chave == "FIREFLY / SAM" and self.forma == "sam":
            return self.dados.get("especial_sam", self.dados.get("especial", {}))
        return self.dados.get("especial", {})

    def defesa(self):
        if self.nome_chave == "FIREFLY / SAM" and self.forma == "sam":
            return self.dados.get("defesa_sam", self.dados.get("defesa_normal", {}))
        return self.dados.get("defesa_normal", {})


class Lutador:
    def __init__(self, usuario, nomes):
        self.usuario = usuario
        self.nome_user = usuario.display_name
        perfil = obter_perfil(usuario.id)
        self.time = [PersonagemCombate(nome, obter_dados_progressao(perfil, nome)["nivel"]) for nome in nomes]
        self.indice_ativo = 0
        self.turnos_tomados = 0
        self.anya_salvamento_ativo = False
        self.anya_salvamento_usado = False
        self.columbina_revive_usado = False
        self.kafka_acompanhamento_usado = False
        self.columbina_dominio_turnos = 0
        self.robin_turnos = 0
        self.cyrene_turnos = 0
        self.cyrene_buff_ativo = any(p.nome_chave == "Cyrene" for p in self.time)
        self.cyrene_reducao = self.cyrene_buff_ativo

    @property
    def ativo(self):
        return self.time[self.indice_ativo]

    def tem_vivos(self):
        return any(p.vivo() for p in self.time)

    def trocar_para_proximo_vivo(self):
        for i, p in enumerate(self.time):
            if p.vivo():
                self.indice_ativo = i
                return True
        return False


class SelecaoTime(discord.ui.View):
    def __init__(self, ctx, oponente, dono_selecao):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.oponente = oponente
        self.dono_selecao = dono_selecao
        perfil = obter_perfil(dono_selecao.id)
        nomes = [n for n in perfil["inventario"] if n in PERSONAGENS]
        opcoes = [discord.SelectOption(
            label=nome[:100],
            description=f"{PERSONAGENS[nome].get('anime', 'Outro')} | {PERSONAGENS[nome].get('classe', 'Guerreiro')}"[:100],
            emoji=PERSONAGENS[nome].get("emoji", "⚔️"),
            value=nome,
        ) for nome in nomes[:25]]
        self.select = discord.ui.Select(
            placeholder=f"Escolha 4 personagens para {dono_selecao.display_name}",
            min_values=4, max_values=4,
            options=opcoes,
            disabled=len(opcoes) < 4,
        )
        self.select.callback = self.selecionar
        self.add_item(self.select)

    async def selecionar(self, interaction):
        if interaction.user.id != self.dono_selecao.id:
            await interaction.response.send_message("Essa seleção pertence ao outro jogador.", ephemeral=True)
            return
        nomes = self.select.values
        if len(nomes) != 4 or len(set(nomes)) != 4:
            await interaction.response.send_message("Escolha exatamente 4 personagens diferentes.", ephemeral=True)
            return
        if self.dono_selecao.id == self.ctx.author.id:
            self.ctx.bot._duelos_pendentes[str(self.ctx.author.id)] = nomes
            view = SelecaoTime(self.ctx, self.oponente, self.oponente)
            embed = discord.Embed(title="⚔️ Duelo PvP 4x4", description=f"{self.ctx.author.mention} escolheu a equipe. Agora é a vez de {self.oponente.mention} escolher 4 personagens.", color=discord.Color.blurple())
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            nomes_p1 = self.ctx.bot._duelos_pendentes.pop(str(self.ctx.author.id), None)
            if not nomes_p1:
                await interaction.response.send_message("Não encontrei a primeira equipe. Inicie o duelo novamente com !duelo @jogador.", ephemeral=True)
                return
            p1 = Lutador(self.ctx.author, nomes_p1)
            p2 = Lutador(self.oponente, nomes)
            batalha = BatalhaView(p1, p2)
            embed = batalha.criar_embed("A batalha 4x4 começou! É a vez do primeiro jogador.")
            await interaction.response.edit_message(embed=embed, view=batalha)
            batalha.message = interaction.message
        self.stop()


class BatalhaView(discord.ui.View):
    def __init__(self, p1, p2):
        super().__init__(timeout=900)
        self.p1 = p1
        self.p2 = p2
        self.turno_atual = p1
        self.encerrada = False

    def oponente(self, lutador):
        return self.p2 if lutador is self.p1 else self.p1

    def criar_embed(self, log):
        embed = discord.Embed(title="⚔️ Batalha PvP 4x4", description=log, color=discord.Color.dark_red())
        for lutador in (self.p1, self.p2):
            linhas = []
            for i, p in enumerate(lutador.time):
                marcador = "▶️ " if i == lutador.indice_ativo else "　"
                status = f"❤️ {p.hp}/{p.hp_max} · 💧 {p.mana}/{p.mana_max}" if p.vivo() else "💀 Derrotado"
                forma = " (SAM)" if p.nome_chave == "FIREFLY / SAM" and p.forma == "sam" else ""
                linhas.append(f"{marcador}**{p.dados.get('emoji', '⚔️')} {p.nome}{forma}** — {status}")
            embed.add_field(name=f"Equipe: {lutador.nome_user}", value="\n".join(linhas), inline=True)
        embed.set_footer(text=f"Turno de {self.turno_atual.nome_user} | Personagem ativo: {self.turno_atual.ativo.nome}")
        imagem = self.turno_atual.ativo.dados.get("gif")
        if imagem and str(imagem).startswith("http"):
            embed.set_thumbnail(url=imagem)
        return embed

    async def validar_turno(self, interaction):
        if self.encerrada:
            await interaction.response.send_message("Esta batalha já terminou.", ephemeral=True)
            return False
        if interaction.user.id not in (self.p1.usuario.id, self.p2.usuario.id):
            await interaction.response.send_message("Você não participa deste duelo.", ephemeral=True)
            return False
        if interaction.user.id != self.turno_atual.usuario.id:
            await interaction.response.send_message("Ainda não é o seu turno.", ephemeral=True)
            return False
        p = self.turno_atual.ativo
        if not getattr(p, "_inicio_turno_processado", False):
            p._inicio_turno_processado = True
            for st in ("queimadura", "sangramento", "choque_kafka"):
                turnos = int(p.status.get(st, 0))
                if turnos > 0 and p.vivo():
                    dano_status = int(p.status.get(st + "_dano", max(1, round(p.hp_max * .05)))) if st in ("queimadura", "choque_kafka") else max(1, round(p.hp_max * .05))
                    p.hp = max(0, p.hp - dano_status)
                    p.status[st] = turnos - 1
                    if p.status[st] <= 0: p.status.pop(st, None); p.status.pop(st + "_dano", None)
                    if p.hp <= 0:
                        self.turno_atual = self.oponente(self.turno_atual)
                        await interaction.response.send_message(f"🔥 {p.nome} foi derrotado por um efeito de status.", ephemeral=True)
                        try: await interaction.message.edit(embed=self.criar_embed("☠️ Um efeito de status derrotou o personagem."), view=self)
                        except discord.HTTPException: pass
                        return False
            # Efeitos de controle são verificados antes de expirar; os demais duram até o fim da ação do alvo.
        bloqueio = next((st for st in ("paralisado", "selado", "atordoado") if p.status.get(st, 0) > 0), None)
        if bloqueio:
            p.status[bloqueio] -= 1
            if p.status[bloqueio] <= 0: p.status.pop(bloqueio, None)
            self.turno_atual = self.oponente(self.turno_atual)
            self.turno_atual.ativo._inicio_turno_processado = False
            await interaction.response.send_message(f"⛓️ {p.nome} está {bloqueio} e perde a ação.", ephemeral=True)
            try: await interaction.message.edit(embed=self.criar_embed(f"⛓️ {p.nome} perdeu a ação."), view=self)
            except discord.HTTPException: pass
            return False
        return True

    async def finalizar_acao(self, interaction, log, imagem=None):
        quem_agiu = self.turno_atual
        p_agiu = quem_agiu.ativo
        for st in ("especial_bloqueado", "dano_reduzido", "defesa_reduzida", "defesa_anulada", "buffs_bloqueados", "marcado", "choque_kafka"):
            if p_agiu.status.get(st, 0) > 0:
                p_agiu.status[st] -= 1
                if p_agiu.status[st] <= 0:
                    p_agiu.status.pop(st, None)
                    if st == "defesa_reduzida": p_agiu.status.pop("defesa_reducao_pct", None)
        if quem_agiu.columbina_dominio_turnos > 0:
            quem_agiu.columbina_dominio_turnos -= 1
            if quem_agiu.columbina_dominio_turnos <= 0:
                log += "\n🌙 O Domínio Lunar terminou."
        if quem_agiu.cyrene_turnos > 0 and p_agiu.nome_chave != "Cyrene":
            quem_agiu.cyrene_turnos -= 1
            if quem_agiu.cyrene_turnos <= 0:
                quem_agiu.cyrene_buff_ativo = False
                log += "\n🌸 O bônus de dano de Cyrene terminou."
        if p_agiu.nome_chave == "FIREFLY / SAM" and p_agiu.forma == "sam" and p_agiu.vivo():
            queimadura = max(1, round(p_agiu.hp_max * .05))
            p_agiu.hp = max(1, p_agiu.hp - queimadura)
            log += f"\n🔥 SAM sofre {queimadura} de queimadura de sobrecarga."
        if quem_agiu.robin_turnos > 0:
            for aliado in quem_agiu.time:
                if aliado.vivo() and aliado.nome_chave != "Osamu Dazai":
                    aliado.hp = min(aliado.hp_max, aliado.hp + 5)
                    aliado.mana = min(aliado.mana_max, aliado.mana + 3)
            quem_agiu.robin_turnos -= 1
            log += "\n🎶 Robin recuperou 5 HP e 3 de mana para a equipe."
        alvo = self.oponente(self.turno_atual)
        if not alvo.tem_vivos():
            self.encerrada = True
            vencedor = self.turno_atual
            pv = obter_perfil(vencedor.usuario.id)
            pp = obter_perfil(alvo.usuario.id)
            pv["vitorias"] = int(pv.get("vitorias", 0)) + 1
            pp["derrotas"] = int(pp.get("derrotas", 0)) + 1
            pv["moedas"] = int(pv.get("moedas", 0)) + 100
            salvar_dados()
            log += f"\n\n🏆 **{vencedor.nome_user} venceu o duelo e recebeu 100 moedas!**"
            for item in self.children:
                item.disabled = True
            await interaction.message.edit(embed=self.criar_embed(log), view=self)
            self.stop()
            return
        if not alvo.ativo.vivo():
            alvo.trocar_para_proximo_vivo()
            log += f"\n🔁 {alvo.nome_user} colocou **{alvo.ativo.nome}** em campo automaticamente."
        # A defesa dura até o próximo golpe recebido.
        quem_agiu.turnos_tomados += 1
        p_agiu.acoes_realizadas += 1
        p_agiu.mana = min(p_agiu.mana_max, p_agiu.mana + 5)
        self.turno_atual = alvo
        self.turno_atual.ativo._inicio_turno_processado = False
        embed = self.criar_embed(log)
        if imagem and str(imagem).startswith("http"):
            embed.set_image(url=imagem)
        await interaction.message.edit(embed=embed, view=self)

    @discord.ui.button(label="Atacar", style=discord.ButtonStyle.danger, emoji="⚔️")
    async def atacar(self, interaction, button):
        if not await self.validar_turno(interaction): return
        atacante = self.turno_atual.ativo
        equipe = self.turno_atual
        equipe_inimiga = self.oponente(equipe)
        inimigos = [p for p in equipe_inimiga.time if p.vivo()]
        if not inimigos: return
        defensor = equipe_inimiga.ativo
        acao = atacante.ataque()
        nome = acao.get("nome", "Ataque normal")
        dano = int(acao.get("dano", 15)) + random.randint(-2, 2)
        if atacante.nome_chave == "Osamu Dazai": dano = 5
        imagem = acao.get("gif")
        log = ""
        alvos = [defensor]

        if atacante.nome_chave == "Columbina":
            defensor.status["marcado"] = 1
            log = "🌙 O alvo foi marcado pela Lua; o próximo ataque aliado causa 10% a mais de dano."
        elif atacante.nome_chave == "Kafka":
            if random.random() < .50:
                defensor.status["choque_kafka"] = 2
                defensor.status["choque_kafka_dano"] = max(1, round(defensor.hp_max * .06))
                log = "⚡ Kafka aplicou Choque por 2 turnos."
        elif atacante.nome_chave == "Medusa":
            if atacante.pontos_petrificacao >= 5:
                dano = 26
                defensor.status["dano_reduzido"] = 1
                atacante.pontos_petrificacao = 0
                log = "🐍 Ataque fortalecido! O dano do alvo foi reduzido em 10%."
            else:
                atacante.pontos_petrificacao += 1
                if random.random() < .10:
                    defensor.status["sangramento"] = 2
                    log = "🩸 O alvo sangrará por 2 turnos."
        elif atacante.nome_chave == "Saber":
            if atacante.espada_revelada:
                dano = 27
            else:
                dano = random.choice([12,17,21])
                atacante.ataques_saber += 1
                if atacante.ataques_saber >= 3:
                    atacante.espada_revelada = True
                    log = "✨ A espada de Saber foi revelada; EXCALIBUR está disponível!"
        elif atacante.nome_chave == "Barou":
            dano = max(1, round(defensor.hp * .05))
        elif atacante.nome_chave == "Maomao":
            defensor.status["dano_reduzido"] = 1
            defensor.status["defesa_reduzida"] = 1
            defensor.status["defesa_reducao_pct"] = 10
            log = "🧪 Maomao ofendeu o inimigo: ele causa 10% menos dano e fica com a defesa enfraquecida."
        elif atacante.nome_chave == "Anya (Mouthwashing)":
            dano = 1
            if defensor.nome_chave != "Osamu Dazai": defensor.status["paralisado"] = 1
            log = "🩺 A provocação de Anya fará o alvo perder a próxima ação."
        elif atacante.nome_chave == "Jolyne Cujoh" and random.random() >= .60:
            dano = 0
            log = "🕸️ O inimigo desviou do chutão de Jolyne!"
        elif atacante.nome_chave == "Dante":
            estilo = random.choice(["Swordmaster", "Gunslinger", "Trickster", "Royal Guard"])
            nome = estilo
            if estilo == "Swordmaster":
                dano = 28; imagem = "https://klipy.com/gifs/stinger-dante"; log = "⚔️ Swordmaster: investida poderosa da Rebellion."
            elif estilo == "Gunslinger":
                dano = 15; alvos = inimigos; imagem = "https://klipy.com/gifs/gun-spin-gunpoint"; log = "🔫 Gunslinger: Ebony & Ivory atingem todos os inimigos."
            elif estilo == "Trickster":
                dano = 0; atacante.esquiva_total = True; imagem = "https://cdn.discordapp.com/attachments/1325666447954808844/1564300968454000680/Smooth_attacks_and_even_smoother_dodges360P_1.gif"
                for inimigo in inimigos: inimigo.status["defesa_reduzida"] = 1; inimigo.status["defesa_reducao_pct"] = 30
                log = "💨 Trickster: inimigos perdem 30% de defesa e Dante esquivará do próximo ataque recebido."
            else:
                dano = 0; atacante.royal_guard = True; atacante.royal_guard_dano = 0; atacante.defendendo = True; imagem = "https://klipy.com/gifs/dmc5-royal-guard"
                log = "🛡️ Royal Guard: Dante preparou sua defesa perfeita e contra-ataque."
        elif atacante.nome_chave == "Itachi Uchiha":
            if random.random() < .80:
                defensor.status.pop("buff_positivo", None)
                defensor.status.pop("buff_dano", None)
                defensor.status.pop("buff_defesa", None)
                defensor.status["queimadura"] = 1
                defensor.status["queimadura_dano"] = max(1, round(defensor.hp_max * .10))
                defensor.status["buffs_bloqueados"] = 1
                log = "🔥 Amaterasu removeu os bônus positivos e aplicou queimadura de 10% da vida máxima."
            else:
                dano = 0; log = "🔥 Amaterasu errou (80% de chance de acerto)."

        if atacante.nome_chave == "Cyrene":
            dano = round(dano * (1 + atacante.bonus_dano_proprio))
        if atacante.nome_chave == "Ken Kaneki" and atacante.hp <= atacante.hp_max * .40:
            dano = round(dano * 1.2)
        if equipe.cyrene_buff_ativo and atacante.nome_chave != "Osamu Dazai":
            dano = round(dano * 1.30)
        if equipe.columbina_dominio_turnos > 0:
            dano = round(dano * 1.20)
        dano_total = 0
        extras=[]
        for alvo in alvos:
            d=max(0,dano)
            if atacante.status.get("dano_reduzido",0) and atacante.nome_chave != "Osamu Dazai": d=round(d*.90)
            if alvo.status.get("defesa_reduzida",0): d=round(d*(1 + alvo.status.get("defesa_reducao_pct",10)/100))
            if alvo.status.get("marcado",0):
                d=round(d*1.10)
                alvo.status.pop("marcado", None)
            if alvo.imunidade_turnos > 0:
                d=0; alvo.imunidade_turnos -= 1
            if alvo.status.get("defesa_anulada",0): alvo.defendendo=False
            if equipe_inimiga.cyrene_reducao: d=round(d*.95)
            if alvo.nome_chave == "Dazai" and alvo.defendendo: pass
            if alvo.esquiva_total:
                d=0; alvo.esquiva_total=False
            if alvo.defendendo:
                if alvo.defesa_forcada == "imune": d=0
                elif alvo.royal_guard:
                    alvo.royal_guard_dano += d; d=0
                else:
                    red=float(alvo.defesa_forcada if isinstance(alvo.defesa_forcada,(float,int)) else alvo.defesa().get("reducao_dano",.5))
                    if alvo.nome_chave == "Medusa" and random.random() < (.50 if alvo.pontos_petrificacao>=5 else .25): d=0
                    else: d=max(0,round(d*(1-red)))
                alvo.defendendo=False; alvo.defesa_forcada=None
            if d >= alvo.hp and equipe_inimiga.anya_salvamento_ativo and not equipe_inimiga.anya_salvamento_usado:
                alvo.hp=max(1,round(alvo.hp_max*.50)); equipe_inimiga.anya_salvamento_usado=True; equipe_inimiga.anya_salvamento_ativo=False
                extras.append("Anya impediu a morte de um aliado!"); aplicado=0
            elif d >= alvo.hp and alvo.nome_chave == "Itachi Uchiha" and alvo.yata_disponivel:
                alvo.hp=1; alvo.yata_disponivel=False; alvo.status.clear(); aplicado=0; extras.append("Espelho Yata bloqueou o golpe fatal!")
            else:
                antes=alvo.hp; alvo.hp=max(0,alvo.hp-d); aplicado=antes-alvo.hp
            dano_total += aplicado
            if alvo.hp <= 0 and atacante.nome_chave == "Tohka Yatogami":
                cura=max(1,round(atacante.hp_max*.10)); atacante.hp=min(atacante.hp_max,atacante.hp+cura); extras.append(f"👑 Tohka recuperou {cura} HP ao finalizar um inimigo.")
            if alvo.nome_chave == "Osamu Dazai" and atacante.nome_chave != "Osamu Dazai":
                alvo.status.clear()
            if alvo.royal_guard and alvo.royal_guard_dano > 0:
                contra = alvo.royal_guard_dano
                atacante.hp = max(0, atacante.hp - contra)
                extras.append(f"🛡️ Royal Guard devolveu {contra} de dano!")
                alvo.royal_guard_dano = 0; alvo.royal_guard = False; alvo.defendendo = False
            if alvo.hp <= 0 and alvo.nome_chave == "Itachi Uchiha" and alvo.totsuka_ativa:
                atacante.status["selado"] = 2; alvo.totsuka_ativa=False; extras.append("A Espada Totsuka selou o atacante por 2 turnos!")
        if atacante.nome_chave == "Sasuke Uchiha" and defensor.vivo() and random.random() < .25:
            defensor.status["atordoado"] = 1
            log += " ⚡ Chidori atordoou o alvo!"
        # Passiva de Kafka: um único ataque de acompanhamento por batalha, com 20% de chance
        # quando um aliado causa dano. Kafka precisa estar viva e não pode ser quem iniciou o ataque.
        kafka_aliada = next((p for p in equipe.time if p.nome_chave == "Kafka" and p.vivo()), None)
        if dano_total > 0 and atacante.nome_chave != "Kafka" and kafka_aliada and not equipe.kafka_acompanhamento_usado and random.random() < .20:
            alvo_follow = next((p for p in alvos if p.vivo()), None)
            if alvo_follow is not None:
                dano_follow = max(1, round(kafka_aliada.ataque().get("dano", 18) * .50))
                dano_follow = min(dano_follow, max(0, alvo_follow.hp - 1))
                alvo_follow.hp -= dano_follow
                equipe.kafka_acompanhamento_usado = True
                extras.append(f"⚡ Kafka ativou seu ataque de acompanhamento e causou {dano_follow} de dano!")
        if atacante.nome_chave == "Ken Kaneki" and dano_total > 0:
            fracao = .30 if atacante.hp <= atacante.hp_max * .40 else .20
            cura = max(1, round(dano_total * fracao))
            atacante.hp = min(atacante.hp_max, atacante.hp + cura)
            log += f" 🩸 Kaneki regenerou {cura} HP."
        if atacante.nome_chave == "Medusa" and not log: log=f"🐍 Petrificação: {atacante.pontos_petrificacao}/5 pontos."
        if not log: log=f"⚔️ **{atacante.nome}** usou *{nome}* e causou **{dano_total}** de dano."
        else: log += f"\nDano total: **{dano_total}**."
        if extras: log += "\n" + "\n".join(extras)
        atacante.mana=min(atacante.mana_max,atacante.mana+8)
        await interaction.response.defer()
        await self.finalizar_acao(interaction,log,imagem)

    @discord.ui.button(label="Especial", style=discord.ButtonStyle.success, emoji="✨")
    async def especial(self, interaction, button):
        if not await self.validar_turno(interaction): return
        atacante=self.turno_atual.ativo; equipe=self.turno_atual; equipe_inimiga=self.oponente(equipe)
        inimigos=[p for p in equipe_inimiga.time if p.vivo()]
        if not inimigos: return
        defensor=equipe_inimiga.ativo; acao=atacante.especial(); custo=int(acao.get("custo_mana",20)); efeito=acao.get("efeito")
        if atacante.nome_chave == "Saber" and not atacante.espada_revelada:
            await interaction.response.send_message("Ataque 3 vezes para revelar a espada e liberar EXCALIBUR.",ephemeral=True); return
        if atacante.nome_chave == "Dante" and atacante.acoes_realizadas < 1:
            await interaction.response.send_message("Sin Devil Trigger fica disponível a partir da 2ª rodada.",ephemeral=True); return
        if atacante.status.get("especial_bloqueado",0)>0 and atacante.nome_chave!="Osamu Dazai":
            await interaction.response.send_message("Seus especiais estão bloqueados por status.",ephemeral=True); return
        if atacante.mana<custo:
            await interaction.response.send_message(f"Mana insuficiente. Você precisa de {custo} e tem {atacante.mana}.",ephemeral=True); return
        if atacante.nome_chave == "Robin" and equipe.robin_turnos>0:
            await interaction.response.send_message("O concerto já está ativo e não pode ser renovado.",ephemeral=True); return
        atacante.mana-=custo; dano=int(acao.get("dano",20)); log=""; imagem=acao.get("gif"); alvos=[defensor]
        if atacante.nome_chave == "Columbina":
            equipe.columbina_dominio_turnos = 2
            dano = 0
            log = "🌙 Domínio Lunar ativo por 2 turnos: aliados causam 20% a mais de dano."
        elif atacante.nome_chave == "Kafka":
            alvos = inimigos[:]
            log = "⚡ Kafka atingiu todos os inimigos; Choque e outros danos contínuos foram detonados."
        elif atacante.nome_chave == "Medusa":
            if atacante.pontos_petrificacao>=5:
                defensor.status["paralisado"]=2; atacante.pontos_petrificacao=0; dano=0; log="🐍 Petrificação! O inimigo foi paralisado por 2 turnos."
            else:
                atacante.pontos_petrificacao=min(5,atacante.pontos_petrificacao+2); defensor.status["dano_reduzido"]=1; log=f"🐍 Medusa acumulou {atacante.pontos_petrificacao}/5 pontos e reduziu o próximo dano do inimigo em 15%."
        elif atacante.nome_chave == "Osamu Dazai":
            alvos=inimigos[:2]
            for alvo in alvos: alvo.mana=0; alvo.status["especial_bloqueado"]=3
            dano=0; log="🩹 Dazai zerou a mana de até dois inimigos e bloqueou seus especiais por 3 turnos."
        elif atacante.nome_chave == "Bayonetta":
            pct=.50 if random.random()<.10 else .25; dano=max(1,round(defensor.hp*pct)); log=f"🔫 Bayonetta causou {int(pct*100)}% da vida atual do alvo."
        elif atacante.nome_chave == "Robin":
            equipe.robin_turnos=5; dano=0; log="🎶 Concerto ativo por 5 turnos: aliados recebem +5 HP e +3 mana por turno."
        elif atacante.nome_chave == "Cyrene":
            atacante.bonus_dano_proprio=min(.15,atacante.bonus_dano_proprio+.02); dano=0; log=f"🌸 Cyrene ganhou +{int(atacante.bonus_dano_proprio*100)}% de dano (máximo 15%)."
        elif atacante.nome_chave == "Anya (Mouthwashing)":
            equipe.anya_salvamento_ativo=not equipe.anya_salvamento_usado; dano=0
            feridos=[p for p in equipe.time if p.vivo() and p.nome_chave != "Osamu Dazai" and p.hp<=p.hp_max*.25]
            if feridos:
                aliado=min(feridos,key=lambda p:p.hp); cura=max(1,round(aliado.hp_max*.20)); aliado.hp=min(aliado.hp_max,aliado.hp+cura)
                log=f"🩺 Anya armou a prevenção de morte e curou {aliado.nome} em {cura} HP."
            else: log="🩺 Anya armou a prevenção de morte: o próximo aliado fatalmente atingido fica com 50% da vida máxima."
        elif atacante.nome_chave == "Itachi Uchiha":
            atacante.yata_disponivel=True; atacante.totsuka_ativa=True; atacante.status.clear(); dano=0
            log="🔥 Susanoo ativado: Espelho Yata protege do primeiro golpe fatal; Totsuka sela um inimigo se Itachi for derrotado depois."
        elif atacante.nome_chave == "Dante":
            if random.random()<.40:
                dano*=2; alvos=inimigos; log="😈 Sin Devil Trigger! O dano deste especial foi dobrado e atingiu todos os inimigos vivos."
            else: dano=0; log="😈 Sin Devil Trigger falhou (40% de chance de ativação); nenhum dano foi causado."
        elif atacante.nome_chave == "Saber":
            atacante.espada_revelada=False; atacante.ataques_saber=0; log="⚔️ EXCALIBUR! Saber liberou um golpe devastador e a espada voltou a ficar oculta."
        elif atacante.nome_chave == "FIREFLY / SAM":
            if atacante.forma=="sam": atacante.forma="normal"; dano=0; log="🔥 Firefly saiu do modo em chamas e voltou à forma base."
            else: atacante.forma="sam"; dano=0; log="🔥 Firefly entrou no modo SAM: +50% de dano e defesa reforçada, mas sofre 5% da vida máxima em queimadura ao fim dos próprios turnos."
        elif atacante.nome_chave == "Tohka Yatogami":
            alvos=inimigos; log="👑 Tohka liberou Halvanhelev e atingiu todos os inimigos."
        elif atacante.nome_chave == "Barou":
            dano += atacante.bonus_especial_barou; log=f"👑 Devour causou {dano} de dano (bônus acumulado: {atacante.bonus_especial_barou})."
        elif atacante.nome_chave == "Maomao":
            defensor.status["defesa_anulada"] = 2
            log = "🧪 O veneno de Maomao causou dano alto e anulou totalmente a defesa do alvo por 2 turnos."
        elif atacante.nome_chave == "Sasuke Uchiha":
            defensor.status["queimadura"]=2; defensor.status["queimadura_dano"]=max(1,round(defensor.hp_max*.08)); defensor.status["defesa_reduzida"]=2; defensor.status["defesa_reducao_pct"]=20; defensor.status["marcado"] = 1
            log="🔥 Amaterasu aplicou queimadura por 2 turnos, reduziu a defesa em 20% e marcou o alvo para o próximo ataque aliado."
        dano_total=0; extras=[]
        for alvo in alvos:
            d=dano
            if atacante.nome_chave=="Cyrene": d=round(d*(1+atacante.bonus_dano_proprio))
            if equipe.cyrene_buff_ativo and atacante.nome_chave != "Osamu Dazai": d=round(d*1.30)
            if equipe.columbina_dominio_turnos > 0 and atacante.nome_chave != "Columbina": d=round(d*1.20)
            if atacante.nome_chave == "Kafka" and alvo.status.get("choque_kafka", 0) > 0:
                detonacao = int(alvo.status.get("choque_kafka_dano", max(1, round(alvo.hp_max * .06)))) * int(alvo.status.get("choque_kafka", 0))
                d += detonacao
                extras.append(f"⚡ Detonação de Choque em {alvo.nome}: +{detonacao} de dano.")
                alvo.status.pop("choque_kafka", None)
                alvo.status.pop("choque_kafka_dano", None)
            if equipe_inimiga.cyrene_reducao: d=round(d*.95)
            if atacante.status.get("dano_reduzido",0) and atacante.nome_chave != "Osamu Dazai": d=round(d*.90)
            if alvo.status.get("defesa_reduzida",0): d=round(d*(1 + alvo.status.get("defesa_reducao_pct",10)/100))
            if alvo.status.get("marcado",0):
                d=round(d*1.10)
                alvo.status.pop("marcado", None)
            if alvo.imunidade_turnos > 0:
                d=0; alvo.imunidade_turnos -= 1
            if alvo.status.get("defesa_anulada",0): alvo.defendendo=False
            if alvo.nome_chave == "Sasuke Uchiha" and random.random() < .15:
                d=0
            if alvo.defendendo:
                if alvo.defesa_forcada=="imune": d=0
                elif alvo.royal_guard: alvo.royal_guard_dano += d; d=0
                else: d=max(0,round(d*(1-float(alvo.defesa_forcada if isinstance(alvo.defesa_forcada,(int,float)) else alvo.defesa().get("reducao_dano",.5)))))
                alvo.defendendo=False; alvo.defesa_forcada=None
            if d>=alvo.hp and not equipe_inimiga.columbina_revive_usado and any(a.nome_chave == "Columbina" and a.vivo() for a in equipe_inimiga.time) and alvo.nome_chave != "Osamu Dazai":
                alvo.hp=max(1,round(alvo.hp_max*.30)); equipe_inimiga.columbina_revive_usado=True; extras.append("🌙 Columbina reviveu um aliado com 30% da vida máxima!"); aplicado=0
            elif d>=alvo.hp and equipe_inimiga.anya_salvamento_ativo and not equipe_inimiga.anya_salvamento_usado and alvo.nome_chave != "Osamu Dazai":
                alvo.hp=max(1,round(alvo.hp_max*.50)); equipe_inimiga.anya_salvamento_usado=True; equipe_inimiga.anya_salvamento_ativo=False; extras.append("Anya impediu a morte de um aliado!"); aplicado=0
            elif d>=alvo.hp and alvo.nome_chave=="Itachi Uchiha" and alvo.yata_disponivel:
                alvo.hp=1; alvo.yata_disponivel=False; alvo.status.clear(); extras.append("Espelho Yata bloqueou o golpe fatal!"); aplicado=0
            else:
                antes=alvo.hp; alvo.hp=max(0,alvo.hp-max(0,d)); aplicado=antes-alvo.hp
            dano_total+=aplicado
            if alvo.nome_chave == "Osamu Dazai" and atacante.nome_chave != "Osamu Dazai":
                alvo.status.clear()
            if alvo.royal_guard and alvo.royal_guard_dano > 0:
                contra=alvo.royal_guard_dano; atacante.hp=max(0,atacante.hp-contra); extras.append(f"🛡️ Royal Guard devolveu {contra} de dano!"); alvo.royal_guard_dano=0; alvo.royal_guard=False; alvo.defendendo=False
            if alvo.hp<=0 and atacante.nome_chave=="Barou":
                roubado=round(int(alvo.dados.get("ataque_normal",{}).get("dano",15))*.20); atacante.bonus_especial_barou+=roubado; extras.append(f"Barou roubou {roubado} de ataque para os próximos especiais.")
            if alvo.hp<=0 and alvo.nome_chave=="Itachi Uchiha" and alvo.totsuka_ativa:
                atacante.status["selado"]=2; alvo.totsuka_ativa=False; extras.append("Espada Totsuka selou o atacante por 2 turnos!")
        # Passiva de Kafka: um único ataque de acompanhamento por batalha, com 20% de chance
        # quando um aliado causa dano. Kafka precisa estar viva e não pode ser quem iniciou o ataque.
        kafka_aliada = next((p for p in equipe.time if p.nome_chave == "Kafka" and p.vivo()), None)
        if dano_total > 0 and atacante.nome_chave != "Kafka" and kafka_aliada and not equipe.kafka_acompanhamento_usado and random.random() < .20:
            alvo_follow = next((p for p in alvos if p.vivo()), None)
            if alvo_follow is not None:
                dano_follow = max(1, round(kafka_aliada.ataque().get("dano", 18) * .50))
                dano_follow = min(dano_follow, max(0, alvo_follow.hp - 1))
                alvo_follow.hp -= dano_follow
                equipe.kafka_acompanhamento_usado = True
                extras.append(f"⚡ Kafka ativou seu ataque de acompanhamento e causou {dano_follow} de dano!")
        if atacante.nome_chave == "Ken Kaneki" and dano_total > 0:
            cura=max(1,round(dano_total*.25)); atacante.hp=min(atacante.hp_max,atacante.hp+cura); log += f" 🩸 Kaneki regenerou {cura} HP."
        if dano_total and not log: log=f"✨ **{atacante.nome}** usou **{acao.get('nome','Especial')}** e causou **{dano_total}** de dano."
        elif dano_total: log+=f"\nDano total: **{dano_total}**."
        if extras: log+="\n"+"\n".join(extras)
        await interaction.response.defer()
        await self.finalizar_acao(interaction,log or f"✨ {atacante.nome} usou {acao.get('nome','Especial')}.",imagem)

    @discord.ui.button(label="Defender", style=discord.ButtonStyle.primary, emoji="🛡️")
    async def defender(self, interaction, button):
        if not await self.validar_turno(interaction): return
        p=self.turno_atual.ativo; p.defendendo=True; p.defesa_forcada=None; d=p.defesa(); nome=d.get("nome","Defesa"); imagem=d.get("gif") or d.get("gif_sucesso")
        log=f"🛡️ **{p.nome}** usou *{nome}*."
        if p.nome_chave=="Medusa":
            if p.pontos_petrificacao>=5:
                p.defesa_forcada=.15; p.esquiva_total=random.random()<.50; p.pontos_petrificacao=0; log+=" Esquiva de 50% e redução de 15%; pontos reiniciados."
            else:
                p.pontos_petrificacao+=1; p.esquiva_total=random.random()<.25; log+=f" Chance de esquiva de 25%; petrificação {p.pontos_petrificacao}/5."
        elif p.nome_chave=="Kirara":
            p.defesas_kirara+=1
            if p.defesas_kirara>=3: p.defesa_forcada="imune"; p.defesas_kirara=0; log+=" ⭐ Defesa absoluta ativada: zero dano nesta rodada!"
            else: p.defesa_forcada=.60; log+=f" ⭐ Progresso: {p.defesas_kirara}/2 defesas antes da proteção absoluta."
        elif p.nome_chave=="Maomao":
            r=random.random()
            if r<.50: p.defesa_forcada=.70; log+=" 🧪 Veneno protetor: 70% de redução."
            elif r<.80: p.defesa_forcada=0.0; log+=" 🧪 O veneno falhou; sem proteção adicional."
            else: p.defesa_forcada="imune"; p.imunidade_turnos=2; log+=" 🧪 Imunidade total por 2 turnos!"
        elif p.nome_chave=="Anya (Mouthwashing)":
            cura=round(p.hp_max*.50); p.hp=min(p.hp_max,p.hp+cura); p.defesa_forcada="imune"; log+=f" 💊 Recuperou até {cura} HP e ficou protegida nesta rodada."
        elif p.nome_chave=="Dante":
            p.royal_guard=True; p.royal_guard_dano=0; p.defesa_forcada=None; log+=" 🛡️ Royal Guard acumulará o dano para contra-atacar."
        elif p.nome_chave=="Itachi Uchiha" and p.yata_disponivel:
            p.status.clear(); log+=" 🔥 O Espelho Yata dissipou status negativos."
        elif p.nome_chave=="FIREFLY / SAM" and p.forma=="sam": p.defesa_forcada=.70
        elif p.nome_chave=="Sasuke Uchiha": p.ataque_chidori_bonus=5
        await interaction.response.defer()
        await self.finalizar_acao(interaction,log,imagem)

    @discord.ui.button(label="Trocar", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def trocar(self, interaction, button):
        if not await self.validar_turno(interaction): return
        lutador = self.turno_atual
        opcoes = []
        for i, p in enumerate(lutador.time):
            if i != lutador.indice_ativo and p.vivo():
                opcoes.append(discord.SelectOption(label=p.nome[:100], description=f"HP {p.hp}/{p.hp_max} · Mana {p.mana}", value=str(i), emoji=p.dados.get("emoji", "⚔️")))
        if not opcoes:
            await interaction.response.send_message("Não há outros personagens vivos para trocar.", ephemeral=True)
            return
        view = TrocarPersonagemView(self, lutador, opcoes)
        await interaction.response.send_message("Escolha o personagem que entrará em campo:", view=view, ephemeral=True)

    @discord.ui.button(label="Desistir", style=discord.ButtonStyle.secondary, emoji="🏳️")
    async def desistir(self, interaction, button):
        if self.encerrada:
            await interaction.response.send_message("A batalha já terminou.", ephemeral=True)
            return
        if interaction.user.id not in (self.p1.usuario.id, self.p2.usuario.id):
            await interaction.response.send_message("Você não participa deste duelo.", ephemeral=True)
            return
        perdedor = self.p1 if interaction.user.id == self.p1.usuario.id else self.p2
        vencedor = self.p2 if perdedor is self.p1 else self.p1
        self.encerrada = True
        obter_perfil(vencedor.usuario.id)["vitorias"] += 1
        obter_perfil(perdedor.usuario.id)["derrotas"] += 1
        obter_perfil(vencedor.usuario.id)["moedas"] += 100
        salvar_dados()
        for item in self.children: item.disabled = True
        await interaction.response.edit_message(embed=self.criar_embed(f"🏳️ **{perdedor.nome_user}** desistiu. **{vencedor.nome_user}** venceu e recebeu 100 moedas!"), view=self)
        self.stop()


class TrocarPersonagemView(discord.ui.View):
    def __init__(self, batalha, lutador, opcoes):
        super().__init__(timeout=60)
        self.batalha = batalha
        self.lutador = lutador
        self.select = discord.ui.Select(placeholder="Escolha o novo personagem", min_values=1, max_values=1, options=opcoes)
        self.select.callback = self.callback_select
        self.add_item(self.select)

    async def callback_select(self, interaction):
        if interaction.user.id != self.lutador.usuario.id:
            await interaction.response.send_message("Esta troca pertence ao outro jogador.", ephemeral=True)
            return
        indice = int(self.select.values[0])
        anterior = self.lutador.ativo.nome
        if anterior == "Cyrene" and self.lutador.cyrene_buff_ativo:
            self.lutador.cyrene_turnos = 2
        self.lutador.indice_ativo = indice
        self.lutador.ativo._inicio_turno_processado = False
        self.lutador.ativo.defendendo = False
        self.batalha.turno_atual = self.batalha.oponente(self.lutador)
        self.batalha.turno_atual.ativo.defendendo = False
        await interaction.response.edit_message(content=f"Você trocou **{anterior}** por **{self.lutador.ativo.nome}**. O turno passou para {self.batalha.turno_atual.nome_user}.", view=None)
        # Atualiza a mensagem principal do combate.
        try:
            await self.batalha.message.edit(embed=self.batalha.criar_embed(f"🔄 {self.lutador.nome_user} trocou para **{self.lutador.ativo.nome}**."), view=self.batalha)
        except (discord.HTTPException, AttributeError):
            pass
        self.stop()

# Guardamos as mensagens das batalhas para atualizar depois de uma troca feita em resposta efêmera.
bot._duelos_pendentes = {}

# -------------------- COMANDOS --------------------
@bot.command(name="gacha", aliases=["invocar", "sorteio"])
@commands.cooldown(1, 2, commands.BucketType.user)
async def gacha(ctx):
    perfil = obter_perfil(ctx.author.id)
    if perfil["moedas"] < CUSTO_GACHA:
        await ctx.send(f"Você precisa de **{CUSTO_GACHA} moedas** para invocar. Saldo: {perfil['moedas']}.")
        return
    perfil["moedas"] -= CUSTO_GACHA
    nome, categoria, motivo = sortear_personagem(perfil)
    repetido = nome in perfil["inventario"]
    if repetido:
        perfil["moedas"] += REEMBOLSO_DUPLICADO
    else:
        perfil["inventario"].append(nome)
    salvar_dados()
    embed = discord.Embed(title=f"🎰 Gacha — {nome}", description=f"{PERSONAGENS[nome].get('emoji', '🎭')} **{nome}**\n{emoji_raridade(categoria)}\n\n{motivo}", color={"5_estrelas": discord.Color.gold(), "4_estrelas": discord.Color.purple(), "3_estrelas": discord.Color.blue(), "2_estrelas": discord.Color.light_grey()}.get(categoria, discord.Color.blurple()))
    if repetido:
        embed.add_field(name="Duplicado", value=f"Você já tinha esse personagem e recebeu {REEMBOLSO_DUPLICADO} moedas de reembolso.", inline=False)
    else:
        embed.add_field(name="Novo personagem!", value="Adicionado à sua coleção.", inline=False)
    embed.add_field(name="Saldo", value=f"🪙 {perfil['moedas']} moedas")
    imagem = PERSONAGENS[nome].get("gif")
    if imagem and str(imagem).startswith("http"): embed.set_image(url=imagem)
    await ctx.send(embed=embed)

@gacha.error
async def gacha_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"Aguarde {error.retry_after:.1f}s antes de usar o gacha novamente.")
    else:
        raise error

@bot.command(name="colecao", aliases=["inventario"])
async def colecao(ctx, membro: discord.Member = None):
    membro = membro or ctx.author
    perfil = obter_perfil(membro.id)
    nomes = perfil["inventario"]
    embed = discord.Embed(title=f"📚 Coleção de {membro.display_name}", description=f"Personagens: **{len(nomes)} / {len(PERSONAGENS)}**\n🪙 Moedas: **{perfil['moedas']}**", color=discord.Color.blurple())
    if nomes:
        linhas = [f"{PERSONAGENS[n].get('emoji', '🎭')} **{n}** — {PERSONAGENS[n].get('raridade', 'Comum')}" for n in nomes if n in PERSONAGENS]
        texto = "\n".join(linhas)
        for inicio in range(0, len(texto), 1000):
            embed.add_field(name="Personagens" if inicio == 0 else "Personagens (continuação)", value=texto[inicio:inicio+1000], inline=False)
    else:
        embed.add_field(name="Coleção vazia", value="Use `!gacha` para conseguir personagens.", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="diario", aliases=["daily"])
async def diario(ctx):
    perfil = obter_perfil(ctx.author.id)
    hoje = date.today().isoformat()
    if perfil.get("ultimo_diario") == hoje:
        await ctx.send(f"Você já resgatou a recompensa diária de hoje. Saldo: **{perfil['moedas']} moedas**.")
        return
    perfil["ultimo_diario"] = hoje
    perfil["moedas"] += RECOMPENSA_DIARIA
    salvar_dados()
    embed = discord.Embed(title="🎁 Recompensa diária", description=f"Você recebeu **{RECOMPENSA_DIARIA} moedas**!\nSaldo: **{perfil['moedas']} moedas**.", color=discord.Color.green())
    await ctx.send(embed=embed)

@bot.command(name="evento", aliases=["eventos"])
async def evento(ctx):
    hoje = date.today()
    if not (HALLOWEEN_INICIO <= hoje <= HALLOWEEN_FIM):
        await ctx.send(f"🎃 O Evento de Halloween está programado para **{HALLOWEEN_INICIO.strftime('%d/%m')} a {HALLOWEEN_FIM.strftime('%d/%m/%Y')}**. Volte durante o evento!")
        return
    perfil = obter_perfil(ctx.author.id)
    resgatado = perfil.get("ultimo_halloween") == hoje.isoformat()
    embed = discord.Embed(
        title="🎃👻 Evento de Halloween: Noite das Almas",
        description=(f"**Evento ativo até {HALLOWEEN_FIM.strftime('%d/%m/%Y')}!**\n"
                     "Complete o desafio diário `!halloween` para ganhar moedas e Doces Assombrados. "
                     "Troque os doces por itens em `!loja_halloween`.\n\n"
                     f"🍬 Seus Doces Assombrados: **{perfil.get('doces_halloween', 0)}**\n"
                     f"📅 Desafio de hoje: **{'já concluído' if resgatado else 'disponível'}**"),
        color=discord.Color.orange()
    )
    embed.set_footer(text="Evento temporário • os doces ficam na sua conta")
    await ctx.send(embed=embed)


@bot.command(name="halloween", aliases=["desafio_halloween"])
async def halloween(ctx):
    hoje = date.today()
    if not (HALLOWEEN_INICIO <= hoje <= HALLOWEEN_FIM):
        await ctx.send(f"🎃 O desafio de Halloween só fica disponível de {HALLOWEEN_INICIO.strftime('%d/%m')} a {HALLOWEEN_FIM.strftime('%d/%m/%Y')}.")
        return
    perfil = obter_perfil(ctx.author.id)
    if perfil.get("ultimo_halloween") == hoje.isoformat():
        await ctx.send("👻 Você já completou o desafio de Halloween hoje! Volte amanhã ou confira `!loja_halloween`.")
        return
    moedas = random.randint(75, 125)
    doces = random.randint(2, 4)
    bonus = random.random() < 0.20
    if bonus:
        doces += 2
    perfil["ultimo_halloween"] = hoje.isoformat()
    perfil["moedas"] = int(perfil.get("moedas", 0)) + moedas
    perfil["doces_halloween"] = int(perfil.get("doces_halloween", 0)) + doces
    salvar_dados()
    extra = "\n🦇 Um espírito brincalhão apareceu: **+2 Doces Assombrados!**" if bonus else ""
    await ctx.send(f"🎃 **Desafio de Halloween concluído!**\nVocê espantou os monstros da vila e recebeu:\n🪙 **+{moedas} moedas**\n🍬 **+{doces} Doces Assombrados**{extra}\nSaldo: **{perfil['moedas']} moedas** | Doces: **{perfil['doces_halloween']}**")


@bot.command(name="loja_halloween", aliases=["loja_evento"])
async def loja_halloween(ctx):
    hoje = date.today()
    if not (HALLOWEEN_INICIO <= hoje <= HALLOWEEN_FIM):
        await ctx.send(f"🎃 A loja de Halloween está fechada. Ela funciona de {HALLOWEEN_INICIO.strftime('%d/%m/%Y')} a {HALLOWEEN_FIM.strftime('%d/%m/%Y')}.")
        return
    await ctx.send("🎃 **Loja da Noite das Almas**\n"
                   "🍬 **5 Doces Assombrados** → 1 Livro de Experiência\n"
                   "🍬 **8 Doces Assombrados** → 1 Chave da Fenda\n"
                   "🍬 **3 Doces Assombrados** → 50 moedas\n"
                   "Use `!trocar_doces livro [qtd]`, `!trocar_doces chave [qtd]` ou `!trocar_doces moedas [qtd]`. "
                   "A quantidade é de recompensas que deseja resgatar.")


@bot.command(name="trocar_doces", aliases=["trocar_halloween"])
async def trocar_doces(ctx, recompensa: str, quantidade: int = 1):
    hoje = date.today()
    if not (HALLOWEEN_INICIO <= hoje <= HALLOWEEN_FIM):
        await ctx.send(f"🎃 As trocas de Halloween só ficam disponíveis de {HALLOWEEN_INICIO.strftime('%d/%m/%Y')} a {HALLOWEEN_FIM.strftime('%d/%m/%Y')}.")
        return
    if quantidade < 1 or quantidade > 20:
        await ctx.send("Escolha uma quantidade entre 1 e 20.")
        return
    recompensa = recompensa.casefold()
    custos = {"livro": 5, "chave": 8, "moedas": 3}
    if recompensa not in custos:
        await ctx.send("Recompensa inválida. Escolha `livro`, `chave` ou `moedas`. Consulte `!loja_halloween`.")
        return
    perfil = obter_perfil(ctx.author.id)
    custo_total = custos[recompensa] * quantidade
    doces = int(perfil.get("doces_halloween", 0))
    if doces < custo_total:
        await ctx.send(f"Você precisa de **{custo_total} Doces Assombrados**, mas possui **{doces}**.")
        return
    perfil["doces_halloween"] = doces - custo_total
    if recompensa == "livro":
        itens = perfil.setdefault("itens", {})
        itens["livro_experiencia"] = int(itens.get("livro_experiencia", 0)) + quantidade
        nome_recompensa = f"{quantidade} Livro(s) de Experiência"
    elif recompensa == "chave":
        perfil["chaves_fenda"] = int(perfil.get("chaves_fenda", 0)) + quantidade
        nome_recompensa = f"{quantidade} Chave(s) da Fenda"
    else:
        perfil["moedas"] = int(perfil.get("moedas", 0)) + 50 * quantidade
        nome_recompensa = f"{50 * quantidade} moedas"
    salvar_dados()
    await ctx.send(f"🎃 Troca realizada! Você recebeu **{nome_recompensa}** por **{custo_total} Doces Assombrados**. Doces restantes: **{perfil['doces_halloween']}**.")


@bot.command(name="perfil")
async def perfil_comando(ctx, membro: discord.Member = None):
    membro = membro or ctx.author
    perfil_jogador = obter_perfil(membro.id)
    embed = discord.Embed(title=f"👤 Perfil de {membro.display_name}", color=discord.Color.blurple())
    embed.add_field(name="🪙 Moedas", value=str(perfil_jogador["moedas"]), inline=True)
    embed.add_field(name="📚 Personagens", value=str(len(perfil_jogador["inventario"])), inline=True)
    embed.add_field(name="🎰 Pity", value=f"{perfil_jogador['pity']}/{LIMITE_PITY}", inline=True)
    embed.add_field(name="🏆 Vitórias", value=str(perfil_jogador["vitorias"]), inline=True)
    embed.add_field(name="🗺️ Fase liberada", value=str(perfil_jogador.get("fase_desbloqueada", 1)), inline=True)
    embed.add_field(name="🔑 Chaves da Fenda", value=str(perfil_jogador.get("chaves_fenda", 0)), inline=True)
    embed.add_field(name="💔 Derrotas", value=str(perfil_jogador["derrotas"]), inline=True)
    selecionado = perfil_jogador.get("personagem_selecionado") or "Nenhum"
    embed.add_field(name="⭐ Personagem selecionado", value=selecionado, inline=False)
    await ctx.send(embed=embed)


@bot.command(name="pity")
async def pity(ctx):
    perfil = obter_perfil(ctx.author.id)
    await ctx.send(f"🎰 Seu pity está em **{perfil['pity']}/{LIMITE_PITY}**. Ao atingir o limite, você recebe um personagem lendário garantido (se houver no catálogo).")

def _normalizar_busca(texto):
    texto = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode("ascii")
    return " ".join(texto.casefold().replace("_", " ").split())


def _categoria_filtro(termo):
    chave = _normalizar_busca(termo)
    mapa = {
        "comum": "2_estrelas", "comuns": "2_estrelas", "2 estrelas": "2_estrelas",
        "rara": "3_estrelas", "raro": "3_estrelas", "raros": "3_estrelas", "raras": "3_estrelas", "3 estrelas": "3_estrelas",
        "epica": "4_estrelas", "epico": "4_estrelas", "epicos": "4_estrelas", "epicas": "4_estrelas", "4 estrelas": "4_estrelas",
        "lendaria": "5_estrelas", "lendario": "5_estrelas", "lendarios": "5_estrelas", "lendarias": "5_estrelas", "5 estrelas": "5_estrelas",
        "mitico": "mitico", "mitica": "mitico", "miticos": "mitico", "miticas": "mitico", "mythic": "mitico",
    }
    return mapa.get(chave)


@bot.command(name="personagens", aliases=["lista", "catalogo"])
async def personagens(ctx, *, raridade: str = None):
    """Lista o catálogo inteiro ou filtra por raridade: !personagens Mítico."""
    todos = list(PERSONAGENS)
    categoria = _categoria_filtro(raridade) if raridade else None
    if raridade and categoria is None:
        await ctx.send("Raridade não reconhecida. Use `!personagens Comum`, `Rara`, `Épica`, `Lendária` ou `Mítico`.")
        return
    nomes = [n for n in todos if categoria is None or raridade_gacha(n) == categoria]
    titulo_filtro = f" — {raridade.title()}" if raridade else ""
    embed = discord.Embed(title=f"📖 Catálogo de personagens{titulo_filtro}", description=f"Encontrados: **{len(nomes)}**. Use `!ver NOME` para abrir a ficha completa.", color=discord.Color.blurple())
    if not nomes:
        embed.description += "\n\nAinda não há personagens cadastrados nessa categoria."
    else:
        grupos = [
            ("🌌 Míticos — exclusivos do Portal", "mitico"),
            ("⭐⭐⭐⭐⭐ Lendários", "5_estrelas"),
            ("⭐⭐⭐⭐ Épicos", "4_estrelas"),
            ("⭐⭐⭐ Raros", "3_estrelas"),
            ("⭐⭐ Comuns", "2_estrelas"),
        ]
        for nome_grupo, cat in grupos:
            lista = [n for n in nomes if raridade_gacha(n) == cat]
            if lista:
                linhas = [f"{PERSONAGENS[n].get('emoji', '🎭')} **{n}** — {PERSONAGENS[n].get('anime', 'Anime desconhecido')}" for n in lista]
                # Campos do Discord têm limite de 1024 caracteres.
                bloco = ""
                parte = 1
                for linha in linhas:
                    if len(bloco) + len(linha) + 1 > 1000:
                        embed.add_field(name=nome_grupo if parte == 1 else f"{nome_grupo} (continuação)", value=bloco, inline=False)
                        bloco = ""
                        parte += 1
                    bloco += ("\n" if bloco else "") + linha
                if bloco:
                    embed.add_field(name=nome_grupo if parte == 1 else f"{nome_grupo} (continuação)", value=bloco, inline=False)
    embed.set_footer(text="Dica: !personagens Mítico filtra os exclusivos do Portal • !ver Nome abre a ficha com imagem/GIF e habilidades.")
    await ctx.send(embed=embed)


@bot.command(name="raridades", aliases=["raridade", "tiers"])
async def raridades(ctx):
    """Mostra o catálogo agrupado por raridade, incluindo a categoria Mítica."""
    grupos = [
        ("🌌 Míticos — exclusivos do Portal", "mitico"),
        ("⭐⭐⭐⭐⭐ Lendária", "5_estrelas"),
        ("⭐⭐⭐⭐ Épica", "4_estrelas"),
        ("⭐⭐⭐ Rara", "3_estrelas"),
        ("⭐⭐ Comum", "2_estrelas"),
    ]
    embed = discord.Embed(title="🌟 Raridades dos personagens", color=discord.Color.blurple())
    for titulo, categoria in grupos:
        nomes = [nome for nome in PERSONAGENS if raridade_gacha(nome) == categoria]
        embed.add_field(name=f"{titulo} ({len(nomes)})", value="\n".join(nomes) if nomes else "Nenhum personagem cadastrado", inline=False)
    embed.set_footer(text="Míticos são exclusivos do Portal e não podem sair no gacha normal.")
    await ctx.send(embed=embed)


@bot.command(name="ver", aliases=["pesquisar", "buscar", "ficha"])
async def ver(ctx, *, nome: str):
    pedido = _normalizar_busca(nome)
    nomes = list(PERSONAGENS)
    encontrado = next((n for n in nomes if _normalizar_busca(n) == pedido), None)
    if encontrado is None:
        correspondencias = [n for n in nomes if pedido and pedido in _normalizar_busca(n)]
        if len(correspondencias) == 1:
            encontrado = correspondencias[0]
        elif len(correspondencias) > 1:
            sugestoes = "\n".join(f"• {n}" for n in correspondencias[:10])
            await ctx.send(f"Encontrei mais de um personagem parecido com **{nome}**. Escolha um nome completo:\n{sugestoes}\n\nDepois use `!ver NOME`.")
            return
    if encontrado is None:
        sugestoes = difflib.get_close_matches(nome, nomes, n=5, cutoff=0.35)
        mensagem = "Não encontrei esse personagem. Use `!personagens` para ver o catálogo."
        if sugestoes:
            mensagem += "\nVocê quis dizer?\n" + "\n".join(f"• {n}" for n in sugestoes)
        await ctx.send(mensagem)
        return
    await ctx.send(embed=embed_personagem(encontrado))

@bot.command(name="escolher")
async def escolher(ctx, *, nome: str):
    perfil = obter_perfil(ctx.author.id)
    encontrado = next((n for n in perfil["inventario"] if n.casefold() == nome.casefold()), None)
    if not encontrado:
        await ctx.send("Você não possui esse personagem. Use `!colecao` para consultar sua coleção.")
        return
    perfil["personagem_selecionado"] = encontrado
    salvar_dados()
    await ctx.send(f"✅ **{encontrado}** foi definido como seu personagem selecionado.")

@bot.command(name="farm")
@commands.cooldown(1, 20, commands.BucketType.user)
async def farm(ctx, fase: int = 1, *, equipe: str = None):
    """Combate PvE automático com desbloqueio sequencial e recompensa apenas na vitória."""
    fases = {
        1: {"nome":"Treino Inicial", "inimigo":"Slime", "hp":70, "dano":7, "ondas":1, "moedas":20, "xp":45},
        2: {"nome":"Floresta Sombria", "inimigo":"Lobo Sombrio", "hp":100, "dano":10, "ondas":1, "moedas":35, "xp":65},
        3: {"nome":"Ruínas Antigas", "inimigo":"Guardião Antigo", "hp":115, "dano":12, "ondas":2, "moedas":50, "xp":85},
        4: {"nome":"Fortaleza Abissal", "inimigo":"Cavaleiro Abissal", "hp":150, "dano":15, "ondas":2, "moedas":70, "xp":110},
        5: {"nome":"Portal Lendário", "inimigo":"Dragão Astral", "hp":210, "dano":18, "ondas":2, "moedas":90, "xp":140},
        6: {"nome":"Fenda Dimensional", "inimigo":"Guardião do Multiverso", "hp":260, "dano":21, "ondas":3, "moedas":120, "xp":170, "especial":True},
    }
    if fase not in fases:
        await ctx.send("Escolha uma fase de 1 a 6: `!farm 1` até `!farm 6`.")
        return
    perfil = obter_perfil(ctx.author.id)
    desbloqueada = max(1, int(perfil.get("fase_desbloqueada", 1)))
    if fase > desbloqueada:
        await ctx.send(f"🔒 Essa fase está bloqueada. Vença a fase **{desbloqueada}** primeiro.")
        return
    if fase == 6 and int(perfil.get("chaves_fenda", 0)) < 1:
        await ctx.send(f"🔑 A Fenda Dimensional exige **1 Chave da Fenda**. Compre na loja com `!comprar_chave` por **{CUSTO_CHAVE_FENDA} moedas**. Consulte `!loja`.")
        return

    # Valida a equipe antes de consumir chave ou iniciar a batalha.
    if equipe:
        pedidos = [x.strip() for x in equipe.replace(';', ',').replace('|', ',').split(',') if x.strip()]
        if not 1 <= len(pedidos) <= 4:
            await ctx.send("Escolha de 1 a 4 personagens, separados por vírgula.")
            return
        equipe_nomes = []
        for pedido in pedidos:
            encontrado = next((n for n in perfil["inventario"] if n.casefold() == pedido.casefold()), None)
            if not encontrado or encontrado not in PERSONAGENS:
                await ctx.send(f"Você não possui **{pedido}**. Consulte `!colecao`.")
                return
            if encontrado in equipe_nomes:
                await ctx.send(f"**{encontrado}** está repetido na equipe.")
                return
            equipe_nomes.append(encontrado)
    else:
        selecionado = perfil.get("personagem_selecionado")
        if selecionado not in perfil["inventario"] or selecionado not in PERSONAGENS:
            await ctx.send("Selecione um personagem com `!escolher NOME` ou informe sua equipe: `!farm 1 Nome, Nome2`.")
            return
        equipe_nomes = [selecionado]

    dados = fases[fase]
    if fase == 6:
        perfil["chaves_fenda"] = int(perfil.get("chaves_fenda", 0)) - 1
        salvar_dados()

    # Combate automático: personagens e inimigos têm HP, causam dano e podem vencer/perder.
    time = []
    for nome in equipe_nomes:
        ficha_p = PERSONAGENS[nome]
        prog = obter_dados_progressao(perfil, nome)
        hp_base = int(ficha_p.get("hp_max", ficha_p.get("hp", 100))) + (prog["nivel"] - 1) * 2
        ataque_base = int(ficha_p.get("ataque_normal", {}).get("dano", 15)) + (prog["nivel"] - 1) // 5
        time.append({"nome":nome, "hp":hp_base, "hp_max":hp_base, "ataque":ataque_base, "mana":int(ficha_p.get("mana", 40))})

    linhas = [f"⚔️ **Fase {fase}: {dados['nome']}**", f"👥 Equipe: {', '.join(equipe_nomes)}"]
    venceu = True
    total_rodadas = 0
    for onda in range(1, dados["ondas"] + 1):
        inimigo_hp = dados["hp"] + (onda - 1) * int(dados["hp"] * 0.35) + max(0, len(time)-1) * 20
        inimigo_hp_max = inimigo_hp
        linhas.append(f"\n👹 **Onda {onda}/{dados['ondas']} — {dados['inimigo']}** ({inimigo_hp} HP)")
        while inimigo_hp > 0 and any(c["hp"] > 0 for c in time) and total_rodadas < 30:
            total_rodadas += 1
            for char in time:
                if char["hp"] <= 0 or inimigo_hp <= 0:
                    continue
                dano = max(1, char["ataque"] + random.randint(-3, 4))
                inimigo_hp = max(0, inimigo_hp - dano)
                if total_rodadas <= 3:
                    linhas.append(f"⚔️ {char['nome']} causa **{dano}** de dano. Inimigo: {inimigo_hp}/{inimigo_hp_max} HP.")
            if inimigo_hp > 0:
                vivos = [c for c in time if c["hp"] > 0]
                alvo = random.choice(vivos)
                dano_inimigo = max(1, dados["dano"] + random.randint(-3, 3) - (alvo["hp_max"] // 100))
                alvo["hp"] = max(0, alvo["hp"] - dano_inimigo)
                if total_rodadas <= 3:
                    linhas.append(f"💥 {dados['inimigo']} atinge **{alvo['nome']}** por {dano_inimigo} (HP {alvo['hp']}/{alvo['hp_max']}).")
        if not any(c["hp"] > 0 for c in time) or total_rodadas >= 30 and inimigo_hp > 0:
            venceu = False
            break
        linhas.append(f"✅ Onda {onda} concluída!")

    if not venceu:
        perfil["derrotas"] = int(perfil.get("derrotas", 0)) + 1
        # A chave é devolvida em caso de derrota; não se cobra por uma tentativa perdida.
        if fase == 6:
            perfil["chaves_fenda"] = int(perfil.get("chaves_fenda", 0)) + 1
        salvar_dados()
        linhas.append("\n💀 **Derrota!** Sem recompensa desta vez. Seus personagens não perdem níveis nem são removidos. Tente uma equipe mais forte.")
        await ctx.send("\n".join(linhas))
        return

    perfil["vitorias"] = int(perfil.get("vitorias", 0)) + 1
    perfil["moedas"] = int(perfil.get("moedas", 0)) + dados["moedas"]
    resultados_xp = []
    for nome in equipe_nomes:
        subiu, nivel = conceder_xp(perfil, nome, dados["xp"])
        progresso = obter_dados_progressao(perfil, nome)
        xp_texto = "nível máximo" if nivel >= NIVEL_MAXIMO else f"{progresso['xp']}/{xp_necessario(nivel)} XP"
        resultados_xp.append(f"• **{nome}**: +{dados['xp']} XP (nível {nivel}, {xp_texto})" + (f" — subiu {subiu} nível(is)!" if subiu else ""))

    # Desbloqueio sequencial permanente; repetir fases anteriores continua permitido.
    perfil["fases_concluidas"] = sorted(set(perfil.get("fases_concluidas", [])) | {fase})
    if fase == desbloqueada and fase < 6:
        perfil["fase_desbloqueada"] = fase + 1
    extra = ""
    chance_livro = 0.10 if fase < 5 else 0.15
    if random.random() < chance_livro:
        perfil.setdefault("itens", {})["livro_experiencia"] = int(perfil.setdefault("itens", {}).get("livro_experiencia", 0)) + 1
        extra += "\n📖 Encontrou **1 Livro de Experiência**!"
    if fase == 6:
        faltantes = [n for n in ["Dante", "Cyrene", "Robin", "Medusa", "Bayonetta"] if n in PERSONAGENS and n not in perfil["inventario"]]
        if faltantes and random.random() < 0.20:
            obtido = random.choice(faltantes)
            perfil["inventario"].append(obtido)
            extra += f"\n🌌 Recrutamento dimensional: **{obtido}**!"
        elif faltantes:
            extra += "\n🌌 Nenhum personagem foi recrutado desta vez."
    salvar_dados()
    linhas.append(f"\n🏆 **Vitória!** +{dados['moedas']} moedas.")
    linhas.append("✨ **XP recebido:**\n" + "\n".join(resultados_xp))
    linhas.append(f"🔓 Próxima fase desbloqueada: **{perfil.get('fase_desbloqueada', 6)}**" if fase < 6 and perfil.get("fase_desbloqueada", 1) > fase else "🌌 Você concluiu a fase final!")
    linhas.append(f"🪙 Saldo: **{perfil['moedas']} moedas** | 🔑 Chaves: **{perfil.get('chaves_fenda', 0)}**{extra}")
    await ctx.send("\n".join(linhas))

@farm.error
async def farm_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Aguarde {error.retry_after:.1f}s antes de iniciar outro farm.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Use `!farm 1` até `!farm 6`, informando o número da fase.")
    else:
        raise error


# -------------------- FENDA DIMENSIONAL COOPERATIVA --------------------
# Uma sala por vez no canal oficial. A sala fica em memória e é reiniciada
# quando o processo do bot reinicia; os dados permanentes dos jogadores não são alterados.
FENDAS_COOP = {}


def _nomes_equipe(perfil, texto):
    pedidos = [x.strip() for x in texto.replace(';', ',').replace('|', ',').split(',') if x.strip()]
    if not pedidos or len(pedidos) > 4:
        return None, 'Informe de 1 a 4 personagens separados por vírgula.'
    equipe = []
    for pedido in pedidos:
        nome = next((n for n in perfil.get('inventario', []) if n.casefold() == pedido.casefold()), None)
        if not nome or nome not in PERSONAGENS:
            return None, f'Você não possui **{pedido}**. Confira com `!colecao`.'
        if nome in equipe:
            return None, f'**{nome}** foi informado mais de uma vez.'
        equipe.append(nome)
    return equipe, None


async def _resolver_rodada_fenda(ctx, sala):
    linhas = [f'🌌 **Rodada {sala["rodada"]} — resolução simultânea**']
    chefe = sala['chefe']
    acoes = list(sala['participantes'].items())
    random.shuffle(acoes)
    for uid, dados in acoes:
        acao = dados.get('acao')
        if not acao:
            continue
        nome = acao['personagem']
        estado = dados['estado'][nome]
        if estado['hp'] <= 0:
            linhas.append(f'💫 {dados["membro"].mention}: **{nome}** está fora de combate.')
            continue
        if acao['tipo'] == 'defender':
            estado['defesa'] = 0.5
            linhas.append(f'🛡️ {dados["membro"].mention}: **{nome}** se prepara para defender (50% de redução neste ataque do chefe).')
        elif acao['tipo'] == 'ataque':
            dano = max(1, int(PERSONAGENS[nome].get('ataque_normal', {}).get('dano', 15)))
            chefe['hp'] = max(0, chefe['hp'] - dano)
            linhas.append(f'⚔️ {dados["membro"].mention}: **{nome}** causa **{dano}** de dano ao Guardião.')
        elif acao['tipo'] == 'especial':
            especial = PERSONAGENS[nome].get('especial', {})
            custo = int(especial.get('custo_mana', 20))
            if estado['mana'] < custo:
                linhas.append(f'🔹 {dados["membro"].mention}: **{nome}** não tinha mana suficiente; a ação virou ataque normal.')
                dano = max(1, int(PERSONAGENS[nome].get('ataque_normal', {}).get('dano', 15)))
            else:
                estado['mana'] -= custo
                dano = max(0, int(especial.get('dano', 25)))
            chefe['hp'] = max(0, chefe['hp'] - dano)
            linhas.append(f'✨ {dados["membro"].mention}: **{nome}** usa especial e causa **{dano}** de dano. Mana: {estado["mana"]}.')
        dados['acao'] = None
        if chefe['hp'] <= 0:
            break

    if chefe['hp'] <= 0:
        linhas.append('\n🏆 **O Guardião do Multiverso foi derrotado!** Todos os participantes recebem recompensas.')
        for uid, dados in sala['participantes'].items():
            perfil = obter_perfil(int(uid))
            perfil['moedas'] += 100
            xp_linhas = []
            for nome in dados['equipe']:
                subiu, nivel = conceder_xp(perfil, nome, 150)
                xp_linhas.append(f'{nome} +150 XP (nível {nivel})' + (f', subiu {subiu} nível(is)' if subiu else ''))
            extra = ''
            faltantes = [n for n in ['Dante', 'Cyrene', 'Robin', 'Medusa', 'Bayonetta'] if n in PERSONAGENS and n not in perfil['inventario']]
            if faltantes and random.random() < 0.15:
                obtido = random.choice(faltantes)
                perfil['inventario'].append(obtido)
                extra = f'\n🌠 Personagem recrutado: **{obtido}**!'
            if random.random() < 0.15:
                perfil.setdefault('itens', {})['livro_experiencia'] = int(perfil.setdefault('itens', {}).get('livro_experiencia', 0)) + 1
                extra += '\n📖 Você também recebeu 1 Livro de Experiência.'
            salvar_dados()
            try:
                await dados['membro'].send('🏆 **Vitória na Fenda Dimensional!**\n' + '\n'.join('• ' + x for x in xp_linhas) + f'\n🪙 +100 moedas e +150 XP por personagem.{extra}')
            except (discord.Forbidden, discord.HTTPException):
                linhas.append(f'\n📬 Não consegui enviar a recompensa por DM para {dados["membro"].display_name}; os dados foram salvos.')
        await ctx.send('\n'.join(linhas))
        FENDAS_COOP.pop(ctx.channel.id, None)
        return

    vivos = []
    for uid, dados in sala['participantes'].items():
        for nome in dados['equipe']:
            if dados['estado'][nome]['hp'] > 0:
                vivos.append((uid, dados, nome))
    if not vivos:
        linhas.append('\n💀 **Todos os grupos foram derrotados.** A Fenda se fechou sem recompensas.')
        await ctx.send('\n'.join(linhas))
        FENDAS_COOP.pop(ctx.channel.id, None)
        return

    # O chefe contra-ataca depois de todas as escolhas dos jogadores.
    uid, dados_alvo, nome_alvo = random.choice(vivos)
    estado_alvo = dados_alvo['estado'][nome_alvo]
    dano_base = random.randint(22, 34) + 4 * (len(sala['participantes']) - 1)
    reducao = estado_alvo.get('defesa', 0)
    dano_recebido = max(1, int(dano_base * (1 - reducao)))
    estado_alvo['defesa'] = 0
    estado_alvo['hp'] = max(0, estado_alvo['hp'] - dano_recebido)
    linhas.append(f'\n👁️ O Guardião contra-ataca **{dados_alvo["membro"].display_name}**: **{nome_alvo}** recebe {dano_recebido} de dano (HP {estado_alvo["hp"]}/{estado_alvo["hp_max"]}).')
    ainda_vivos = any(
        estado_personagem['hp'] > 0
        for dados_jogador in sala['participantes'].values()
        for estado_personagem in dados_jogador['estado'].values()
    )
    if not ainda_vivos:
        linhas.append('\n💀 **Todos os personagens foram derrotados.** A Fenda se fechou sem recompensas.')
        await ctx.send('\n'.join(linhas))
        FENDAS_COOP.pop(ctx.channel.id, None)
        return
    sala['rodada'] += 1
    # Participantes sem personagens vivos não bloqueiam as próximas rodadas.
    for dados in sala['participantes'].values():
        if not any(dados['estado'][n]['hp'] > 0 for n in dados['equipe']):
            dados['acao'] = {'personagem': dados['equipe'][0], 'tipo': 'derrotado'}
    await ctx.send('\n'.join(linhas) + f'\n❤️ Guardião: **{chefe["hp"]}/{chefe["hp_max"]} HP**. Escolham a próxima ação com `!fenda acao NOME ataque`, `especial` ou `defender`.')


@bot.command(name='fenda')
async def fenda(ctx, operacao: str = 'ajuda', *, argumento: str = None):
    canal_id = ctx.channel.id
    op = operacao.casefold()
    sala = FENDAS_COOP.get(canal_id)
    if op == 'ajuda':
        await ctx.send('🌌 **Fenda Dimensional cooperativa (simultânea)**\n'
                       '`!fenda iniciar Nome1, Nome2` — abre uma sala e escolhe sua equipe (1–4 personagens).\n'
                       '`!fenda entrar Nome1, Nome2` — entra com sua equipe (2–4 jogadores no total).\n'
                       '`!fenda comecar` — líder inicia o combate.\n'
                       '`!fenda acao NOME ataque` — ataque normal.\n'
                       '`!fenda acao NOME especial` — especial (usa mana).\n'
                       '`!fenda acao NOME defender` — reduz em 50% o próximo ataque do chefe contra esse personagem.\n'
                       'Todos os jogadores ativos precisam escolher uma ação antes de cada rodada ser resolvida. Cada jogador escolhe 1 personagem por rodada; na vitória, todos os personagens de cada equipe recebem 150 XP.')
        return
    if op == 'iniciar':
        if sala:
            await ctx.send('Já existe uma Fenda aberta neste canal. Use `!fenda entrar` com uma equipe ou aguarde o fim da batalha.')
            return
        if not argumento:
            await ctx.send('Informe sua equipe: `!fenda iniciar Dante, Robin, Medusa, Bayonetta`.')
            return
        perfil = obter_perfil(ctx.author.id)
        equipe, erro = _nomes_equipe(perfil, argumento)
        if erro:
            await ctx.send(erro)
            return
        estado = {}
        for nome in equipe:
            hp = int(PERSONAGENS[nome].get('hp_max', PERSONAGENS[nome].get('hp', 100)))
            estado[nome] = {'hp': hp, 'hp_max': hp, 'mana': int(PERSONAGENS[nome].get('mana', 40)), 'defesa': 0}
        FENDAS_COOP[canal_id] = {'lider': ctx.author.id, 'rodada': 1, 'iniciada': False,
            'chefe': {'hp': 500, 'hp_max': 500}, 'participantes': {str(ctx.author.id): {'membro': ctx.author, 'equipe': equipe, 'estado': estado, 'acao': None}}}
        await ctx.send(f'🌌 {ctx.author.mention} abriu a **Fenda Dimensional** com {", ".join(equipe)}!\nOutros jogadores: `!fenda entrar Nome1, Nome2`. São necessários de 2 a 4 jogadores. O líder inicia com `!fenda comecar`.')
        return
    if op == 'entrar':
        if not sala or sala['iniciada']:
            await ctx.send('Não há sala aberta para entrar. Peça a alguém para usar `!fenda iniciar Nome1, Nome2`.')
            return
        if str(ctx.author.id) in sala['participantes']:
            await ctx.send('Você já está nesta Fenda.')
            return
        if len(sala['participantes']) >= 4:
            await ctx.send('A Fenda já está cheia: máximo de 4 jogadores.')
            return
        if not argumento:
            await ctx.send('Informe sua equipe: `!fenda entrar Nome1, Nome2, Nome3, Nome4`.')
            return
        perfil = obter_perfil(ctx.author.id)
        equipe, erro = _nomes_equipe(perfil, argumento)
        if erro:
            await ctx.send(erro)
            return
        estado = {}
        for nome in equipe:
            hp = int(PERSONAGENS[nome].get('hp_max', PERSONAGENS[nome].get('hp', 100)))
            estado[nome] = {'hp': hp, 'hp_max': hp, 'mana': int(PERSONAGENS[nome].get('mana', 40)), 'defesa': 0}
        sala['participantes'][str(ctx.author.id)] = {'membro': ctx.author, 'equipe': equipe, 'estado': estado, 'acao': None}
        await ctx.send(f'✅ {ctx.author.mention} entrou com **{", ".join(equipe)}**. Jogadores: {len(sala["participantes"])}/4.')
        return
    if op == 'comecar':
        if not sala or sala['iniciada']:
            await ctx.send('Não existe uma sala aguardando início.')
            return
        if ctx.author.id != sala['lider']:
            await ctx.send('Somente quem abriu a Fenda pode iniciar o combate.')
            return
        if len(sala['participantes']) < 2:
            await ctx.send('São necessários pelo menos **2 jogadores** para iniciar a Fenda cooperativa.')
            return
        sala['iniciada'] = True
        sala['chefe']['hp'] = sala['chefe']['hp_max'] = 500 + 220 * (len(sala['participantes']) - 1)
        jogadores = ', '.join(d['membro'].display_name for d in sala['participantes'].values())
        await ctx.send(f'⚔️ **A Fenda Dimensional começou!**\n👥 Jogadores: {jogadores}\n👁️ Guardião do Multiverso: **{sala["chefe"]["hp"]} HP**.\nCada jogador escolhe uma ação; a rodada resolve quando todos enviarem. Exemplo: `!fenda acao Dante ataque`.')
        return
    if op == 'acao':
        if not sala or not sala['iniciada']:
            await ctx.send('A Fenda ainda não começou. Use `!fenda iniciar`, convide jogadores e depois `!fenda comecar`.')
            return
        uid = str(ctx.author.id)
        dados = sala['participantes'].get(uid)
        if not dados:
            await ctx.send('Você não participa desta Fenda.')
            return
        if dados.get('acao'):
            await ctx.send('Você já enviou sua ação nesta rodada. Aguarde os demais jogadores.')
            return
        partes = (argumento or '').rsplit(' ', 1)
        if len(partes) != 2:
            await ctx.send('Formato: `!fenda acao NOME ataque`, `!fenda acao NOME especial` ou `!fenda acao NOME defender`.')
            return
        nome_pedido, tipo = partes[0].strip(), partes[1].casefold()
        nome = next((n for n in dados['equipe'] if n.casefold() == nome_pedido.casefold()), None)
        if not nome:
            await ctx.send('Escolha um personagem da sua equipe. Sua equipe: ' + ', '.join(dados['equipe']))
            return
        if tipo not in ('ataque', 'especial', 'defender'):
            await ctx.send('Ação inválida. Use `ataque`, `especial` ou `defender`.')
            return
        if dados['estado'][nome]['hp'] <= 0:
            await ctx.send(f'**{nome}** está fora de combate. Escolha outro personagem vivo.')
            return
        dados['acao'] = {'personagem': nome, 'tipo': tipo}
        aguardando = [d['membro'].mention for d in sala['participantes'].values() if d.get('acao') is None and any(d['estado'][n]['hp'] > 0 for n in d['equipe'])]
        if aguardando:
            await ctx.send(f'✅ Ação registrada para **{nome}**. A rodada será resolvida quando todos escolherem. Aguardando: {", ".join(aguardando)}.')
            return
        # Marca jogadores sem personagens vivos como prontos, para não travar a rodada.
        for d in sala['participantes'].values():
            if d.get('acao') is None and not any(d['estado'][n]['hp'] > 0 for n in d['equipe']):
                d['acao'] = {'personagem': d['equipe'][0], 'tipo': 'derrotado'}
        await _resolver_rodada_fenda(ctx, sala)
        return
    if op == 'status':
        if not sala:
            await ctx.send('Não há Fenda aberta neste canal.')
            return
        linhas = [f'🌌 **Fenda Dimensional** — ' + ('em combate' if sala['iniciada'] else 'aguardando jogadores'), f'Rodada: {sala["rodada"]}', f'Guardião: {sala["chefe"]["hp"]}/{sala["chefe"]["hp_max"]} HP']
        for d in sala['participantes'].values():
            vivos = [f'{n} {d["estado"][n]["hp"]}/{d["estado"][n]["hp_max"]} HP' for n in d['equipe']]
            linhas.append(f'• {d["membro"].display_name}: {", ".join(vivos)} — ' + ('ação enviada' if d.get('acao') else 'aguardando ação'))
        await ctx.send('\n'.join(linhas))
        return
    if op == 'cancelar':
        if not sala:
            await ctx.send('Não há Fenda aberta.')
            return
        if ctx.author.id != sala['lider']:
            await ctx.send('Somente o líder pode cancelar a Fenda.')
            return
        FENDAS_COOP.pop(canal_id, None)
        await ctx.send('🚪 A Fenda Dimensional foi encerrada pelo líder.')
        return
    await ctx.send('Operação desconhecida. Use `!fenda ajuda`.')


@bot.command(name="nivel", aliases=["nivelpersonagem", "xp"])
async def nivel_personagem(ctx, *, nome: str = None):
    perfil = obter_perfil(ctx.author.id)
    nome = nome or perfil.get("personagem_selecionado")
    encontrado = next((n for n in perfil["inventario"] if n.casefold() == str(nome).casefold()), None)
    if not encontrado or encontrado not in PERSONAGENS:
        await ctx.send("Informe um personagem que você possui. Exemplo: `!nivel Tohka Yatogami`.")
        return
    progresso = obter_dados_progressao(perfil, encontrado)
    if progresso["nivel"] >= NIVEL_MAXIMO:
        texto_xp = "Nível máximo alcançado!"
    else:
        texto_xp = f"{progresso['xp']}/{xp_necessario(progresso['nivel'])} XP para o próximo nível"
    await ctx.send(f"📈 **{encontrado}** — nível **{progresso['nivel']}/{NIVEL_MAXIMO}**\n✨ {texto_xp}\n❤️ Bônus de vida no nível atual: **+{(progresso['nivel']-1)*2} HP**\n⚔️ Bônus de dano: **+{(progresso['nivel']-1)//5}** por ação com dano fixo.")


@bot.command(name="itens", aliases=["mochila"])
async def itens(ctx):
    perfil = obter_perfil(ctx.author.id)
    livros = int(perfil.get("itens", {}).get("livro_experiencia", 0))
    chaves = int(perfil.get("chaves_fenda", 0))
    await ctx.send(f"🎒 **Sua mochila**\n📖 Livro de Experiência: **{livros}**\n🔑 Chave da Fenda: **{chaves}**\n🍬 Doces Assombrados: **{perfil.get('doces_halloween', 0)}**\nUse `!usar_livro NOME DO PERSONAGEM` para conceder {XP_LIVRO_EXP} XP.")


@bot.command(name="loja")
async def loja(ctx):
    await ctx.send(f"🛒 **Loja de itens**\n📖 **Livro de Experiência** — {CUSTO_LIVRO_EXP} moedas; concede {XP_LIVRO_EXP} XP a um personagem.\nCompre com `!comprar_livro [quantidade]`.\n🔑 **Chave da Fenda** — {CUSTO_CHAVE_FENDA} moedas; necessária para entrar na Fenda Dimensional (fase 6).\nCompre com `!comprar_chave [quantidade]`.")


@bot.command(name="comprar_livro")
async def comprar_livro(ctx, quantidade: int = 1):
    if quantidade < 1 or quantidade > 99:
        await ctx.send("Escolha uma quantidade entre 1 e 99.")
        return
    perfil = obter_perfil(ctx.author.id)
    custo = CUSTO_LIVRO_EXP * quantidade
    if perfil["moedas"] < custo:
        await ctx.send(f"Você precisa de **{custo} moedas** para comprar {quantidade} livro(s). Seu saldo é {perfil['moedas']}.")
        return
    perfil["moedas"] -= custo
    perfil.setdefault("itens", {})["livro_experiencia"] = int(perfil["itens"].get("livro_experiencia", 0)) + quantidade
    salvar_dados()
    await ctx.send(f"✅ Você comprou **{quantidade} Livro(s) de Experiência** por {custo} moedas. Saldo: {perfil['moedas']} moedas.")


@bot.command(name="comprar_chave", aliases=["comprar_chave_fenda"])
async def comprar_chave(ctx, quantidade: int = 1):
    if quantidade < 1 or quantidade > 99:
        await ctx.send("Escolha uma quantidade entre 1 e 99.")
        return
    perfil = obter_perfil(ctx.author.id)
    custo = CUSTO_CHAVE_FENDA * quantidade
    saldo = int(perfil.get("moedas", 0))
    if saldo < custo:
        await ctx.send(f"Você precisa de **{custo} moedas** para comprar {quantidade} Chave(s) da Fenda. Seu saldo é **{saldo} moedas**.")
        return
    perfil["moedas"] = saldo - custo
    perfil["chaves_fenda"] = int(perfil.get("chaves_fenda", 0)) + quantidade
    salvar_dados()
    await ctx.send(f"✅ Você comprou **{quantidade} Chave(s) da Fenda** por **{custo} moedas**. Chaves: **{perfil['chaves_fenda']}** | Saldo: **{perfil['moedas']} moedas**.")


@bot.command(name="usar_livro")
async def usar_livro(ctx, *, nome: str):
    perfil = obter_perfil(ctx.author.id)
    encontrado = next((n for n in perfil["inventario"] if n.casefold() == nome.casefold()), None)
    if not encontrado or encontrado not in PERSONAGENS:
        await ctx.send("Você não possui esse personagem. Exemplo: `!usar_livro Tohka Yatogami`.")
        return
    itens_perfil = perfil.setdefault("itens", {})
    livros = int(itens_perfil.get("livro_experiencia", 0))
    if livros < 1:
        await ctx.send("Você não tem Livros de Experiência. Use `!loja` ou jogue `!farm 1-5` para conseguir.")
        return
    progresso = obter_dados_progressao(perfil, encontrado)
    if progresso["nivel"] >= NIVEL_MAXIMO:
        await ctx.send(f"**{encontrado}** já está no nível máximo ({NIVEL_MAXIMO}). O livro não foi consumido.")
        return
    itens_perfil["livro_experiencia"] = livros - 1
    subiu, nivel = conceder_xp(perfil, encontrado, XP_LIVRO_EXP)
    salvar_dados()
    progresso = obter_dados_progressao(perfil, encontrado)
    estado = "nível máximo alcançado!" if nivel >= NIVEL_MAXIMO else f"{progresso['xp']}/{xp_necessario(nivel)} XP para o próximo nível"
    msg_subiu = f"🎉 Subiu {subiu} nível(is)!" if subiu else ""
    await ctx.send(f"📖 Livro usado em **{encontrado}**: +{XP_LIVRO_EXP} XP. Nível **{nivel}/{NIVEL_MAXIMO}** — {estado}. {msg_subiu}")

@bot.command(name="duelo", aliases=["batalha"])
async def duelo(ctx, oponente: discord.Member):
    if oponente.bot or oponente.id == ctx.author.id:
        await ctx.send("Escolha outro jogador humano para o duelo.")
        return
    p1 = obter_perfil(ctx.author.id)
    p2 = obter_perfil(oponente.id)
    n1 = [n for n in p1["inventario"] if n in PERSONAGENS]
    n2 = [n for n in p2["inventario"] if n in PERSONAGENS]
    if len(n1) < 4:
        await ctx.send("Você precisa ter pelo menos **4 personagens diferentes** na coleção para duelar. Use `!gacha` para conseguir mais.")
        return
    if len(n2) < 4:
        await ctx.send(f"{oponente.mention} precisa ter pelo menos **4 personagens diferentes** para aceitar o duelo.")
        return
    view = SelecaoTime(ctx, oponente, ctx.author)
    embed = discord.Embed(title="⚔️ Duelo PvP 4x4", description=f"{ctx.author.mention}, escolha **4 personagens diferentes** para sua equipe. Depois {oponente.mention} escolherá a equipe dele.", color=discord.Color.blurple())
    mensagem = await ctx.send(embed=embed, view=view)
    # Armazena a mensagem e será preenchida quando P1 selecionar.
    bot._duelos_pendentes[mensagem.id] = None
    bot._duelos_pendentes[str(ctx.author.id)] = None

class MenuPrincipal(discord.ui.View):
    """Menu interativo privado para quem abriu o comando !menu."""
    def __init__(self, owner_id: int):
        super().__init__(timeout=180)
        self.owner_id = owner_id
        opcoes = [
            discord.SelectOption(label="Perfil e progresso", description="Saldo, níveis e recompensa diária", emoji="👤", value="perfil"),
            discord.SelectOption(label="Personagens e coleção", description="Consultar coleção e catálogo", emoji="📚", value="colecao"),
            discord.SelectOption(label="Farm e fases", description="Fases, moedas, XP e desbloqueios", emoji="⚔️", value="farm"),
            discord.SelectOption(label="Loja e itens", description="Comprar livros e chaves", emoji="🛒", value="loja"),
            discord.SelectOption(label="Gacha", description="Invocar personagens e consultar pity", emoji="🎰", value="gacha"),
            discord.SelectOption(label="Evento de Halloween", description="Desafio e trocas de doces", emoji="🎃", value="halloween"),
            discord.SelectOption(label="Fenda cooperativa", description="Ajuda para jogar em coop", emoji="🌌", value="fenda"),
            discord.SelectOption(label="Batalhas PvP 4x4", description="Iniciar duelo contra outro jogador", emoji="🛡️", value="duelo"),
            discord.SelectOption(label="Recompensas", description="Diário e recompensas de farm", emoji="🎁", value="recompensas"),
        ]
        self.select = discord.ui.Select(placeholder="📜 Escolha uma categoria...", min_values=1, max_values=1, options=opcoes)
        self.select.callback = self.selecionar
        self.add_item(self.select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Esse menu pertence a outra pessoa. Use `!menu` para abrir o seu.", ephemeral=True)
            return False
        return True

    async def selecionar(self, interaction: discord.Interaction):
        opcao = self.select.values[0]
        if opcao == "farm":
            texto = ("**⚔️ FASES DE FARM**\nUse `!farm N` para jogar uma fase já desbloqueada. "
                     "Você pode informar de 1 a 4 personagens próprios, separados por vírgula. "
                     "A vitória concede moedas e XP; derrotas não dão recompensa.\n" + "\n".join([
                "`!farm 1` — Treino Inicial: **20 moedas** e **45 XP** por personagem",
                "`!farm 2` — Floresta Sombria: **35 moedas** e **65 XP** por personagem",
                "`!farm 3` — Ruínas Antigas: **50 moedas** e **85 XP** por personagem",
                "`!farm 4` — Fortaleza Abissal: **70 moedas** e **110 XP** por personagem",
                "`!farm 5` — Portal Lendário: **90 moedas** e **140 XP** por personagem",
                f"`!farm 6` — Fenda Dimensional: **120 moedas** e **170 XP** por personagem; exige 1 chave. Há 20% de chance de recrutar personagem especial.",
            ]) + "\n\nHá um intervalo de 20 segundos entre tentativas. Use `!fenda ajuda` para o modo cooperativo.")
        elif opcao == "perfil":
            texto = "**👤 PERFIL E PROGRESSO**\n`!perfil` — saldo, vitórias e estatísticas\n`!diario` — resgatar recompensa diária de " + str(RECOMPENSA_DIARIA) + " moedas\n`!nivel NOME` — consultar nível e XP\n`!escolher NOME` — selecionar personagem"
        elif opcao == "colecao":
            texto = "**📚 PERSONAGENS E COLEÇÃO**\n`!colecao` — seus personagens\n`!personagens` — catálogo completo\n`!ver NOME` — detalhes de um personagem\n`!gacha` — tentar conseguir novos personagens"
        elif opcao == "loja":
            texto = "**🛒 LOJA E ITENS**\n`!loja` — consultar preços\n`!itens` — ver sua mochila\n`!comprar_livro [qtd]` — comprar livros de experiência\n`!comprar_chave [qtd]` — comprar chaves da Fenda"
        elif opcao == "gacha":
            texto = f"**🎰 SISTEMA DE GACHA**\n`!gacha` custa {CUSTO_GACHA} moedas. Personagem repetido devolve {REEMBOLSO_DUPLICADO} moedas. O sistema de pity garante um lendário em {LIMITE_PITY} tentativas.\n`!pity` — consultar seu progresso de garantia."
        elif opcao == "halloween":
            texto = "**🎃 EVENTO DE HALLOWEEN**\n`!evento` — ver informações do evento\n`!halloween` — realizar desafio\n`!loja_halloween` — ver trocas disponíveis\n`!trocar_doces livro/chave/moedas [qtd]` — trocar doces por recompensas. O evento está programado para 31/10/2026 a 30/11/2026."
        elif opcao == "fenda":
            texto = "**🌌 FENDA COOPERATIVA**\n`!fenda ajuda` — ver instruções\nUse os comandos `!fenda` indicados pela ajuda para criar/participar da sala e enfrentar o Guardião do Multiverso com outros jogadores."
        elif opcao == "recompensas":
            texto = f"**🎁 RECOMPENSAS**\n`!diario` — receber {RECOMPENSA_DIARIA} moedas uma vez por dia\n`!farm 1` a `!farm 6` — ganhar moedas e XP ao vencer fases desbloqueadas\nNo farm, pode haver chance de receber um Livro de Experiência; a fase 6 também tem chance de recrutar personagem especial."
        else:
            texto = "**🛡️ BATALHAS PvP 4x4**\nUse `!duelo @jogador`. Cada jogador precisa ter pelo menos 4 personagens diferentes. Durante a batalha, use os botões para atacar, usar especial, defender, trocar de personagem ou desistir."
        await interaction.response.send_message(texto, ephemeral=True)


@bot.command(name="menu")
async def menu(ctx):
    await ctx.send("📜 **Menu principal** — escolha uma categoria abaixo:", view=MenuPrincipal(ctx.author.id))


@bot.command(name="ajuda", aliases=["comandos"])
async def ajuda(ctx):
    embed = discord.Embed(title="📜 Menu do bot", description="Comandos disponíveis", color=discord.Color.blurple())
    embed.add_field(name="🎰 Gacha", value="`!gacha` — invocar personagem\n`!pity` — ver garantia\n`!personagens` — lista do catálogo\n`!ver NOME` — detalhes do personagem", inline=False)
    embed.add_field(name="👤 Perfil", value="`!perfil` — estatísticas e saldo\n`!colecao` — coleção\n`!diario` — recompensa diária\n`!escolher NOME` — selecionar personagem", inline=False)
    embed.add_field(name="🎃 Evento", value="`!evento` — ver evento de Halloween\n`!halloween` — desafio diário\n`!loja_halloween` — trocar doces por itens\n`!trocar_doces livro/chave/moedas [qtd]` — resgatar recompensas", inline=False)
    embed.add_field(name="⚔️ Jogo", value="`!duelo @jogador` — batalha PvP 4x4\n`!farm 1-6` — farmar moedas e XP; fase 6 tem personagens especiais, XP e chance de livro\n`!nivel NOME` — ver nível e XP\n`!loja` / `!comprar_livro [qtd]` / `!comprar_chave [qtd]` — comprar itens\n`!itens` — ver mochila\n`!usar_livro NOME` — usar livro em personagem", inline=False)
    embed.add_field(name="🛠️ Administração", value="`!dar_moedas @jogador quantidade`\n`!dar_personagem @jogador nome`\n`!tirarmoedas @jogador quantidade`\n`!tirarpersonagem @jogador nome`", inline=False)
    await ctx.send(embed=embed)

async def exigir_admin(ctx):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("Você precisa ser administrador para usar esse comando.")
        return False
    return True

@bot.command(name="dar_moedas")
async def dar_moedas(ctx, membro: discord.Member, quantidade: int):
    if not await exigir_admin(ctx): return
    if quantidade <= 0:
        await ctx.send("A quantidade precisa ser maior que zero."); return
    perfil = obter_perfil(membro.id); perfil["moedas"] += quantidade; salvar_dados()
    await ctx.send(f"🪙 Foram adicionadas {quantidade} moedas a {membro.mention}.")

@bot.command(name="tirarmoedas")
async def tirar_moedas(ctx, membro: discord.Member, quantidade: int):
    if not await exigir_admin(ctx): return
    if quantidade <= 0:
        await ctx.send("A quantidade precisa ser maior que zero."); return
    perfil = obter_perfil(membro.id); perfil["moedas"] = max(0, perfil["moedas"] - quantidade); salvar_dados()
    await ctx.send(f"🪙 Foram removidas até {quantidade} moedas de {membro.mention}.")

@bot.command(name="dar_personagem")
async def dar_personagem(ctx, membro: discord.Member, *, nome: str):
    if not await exigir_admin(ctx): return
    encontrado = next((n for n in PERSONAGENS if n.casefold() == nome.casefold()), None)
    if not encontrado:
        await ctx.send("Personagem não encontrado. Use `!personagens`."); return
    perfil = obter_perfil(membro.id)
    if encontrado in perfil["inventario"]:
        await ctx.send(f"{membro.mention} já possui **{encontrado}**."); return
    perfil["inventario"].append(encontrado); salvar_dados()
    await ctx.send(f"✅ **{encontrado}** foi adicionado à coleção de {membro.mention}.")

@bot.command(name="tirarpersonagem")
async def tirar_personagem(ctx, membro: discord.Member, *, nome: str):
    if not await exigir_admin(ctx): return
    perfil = obter_perfil(membro.id)
    encontrado = next((n for n in perfil["inventario"] if n.casefold() == nome.casefold()), None)
    if not encontrado:
        await ctx.send(f"{membro.mention} não possui esse personagem."); return
    perfil["inventario"].remove(encontrado)
    if perfil.get("personagem_selecionado") == encontrado:
        perfil["personagem_selecionado"] = perfil["inventario"][0] if perfil["inventario"] else None
    salvar_dados()
    await ctx.send(f"🗑️ **{encontrado}** foi removido da coleção de {membro.mention}.")

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user} (ID: {bot.user.id})")
    print(f"Catálogo carregado: {len(PERSONAGENS)} personagens")
    if GAME_CHANNEL_ID > 0:
        print(f"Canal oficial do jogo: {GAME_CHANNEL_ID}")
    else:
        print("ATENÇÃO: GAME_CHANNEL_ID não configurado; comandos do jogo ficarão bloqueados.")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound): return
    if isinstance(error, commands.CheckFailure):
        mensagem = str(error) or "Este comando não pode ser usado aqui."
        try:
            await ctx.author.send(f"🎮 {mensagem}")
        except (discord.Forbidden, discord.HTTPException):
            # Não polui canais que não são o canal oficial do jogo.
            pass
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Faltou um argumento. Use `!ajuda` para consultar os comandos. Detalhe: `{error.param.name}`.")
        return
    if isinstance(error, commands.BadArgument):
        await ctx.send("Não consegui interpretar os argumentos. Confira a menção e os valores e tente novamente.")
        return
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"Aguarde {error.retry_after:.1f}s para usar esse comando novamente.")
        return
    print(f"Erro no comando {getattr(ctx.command, 'name', 'desconhecido')}: {error}")
    await ctx.send("Ocorreu um erro ao executar o comando. O erro foi registrado no console.")

if __name__ == "__main__":
    if not TOKEN:
        try:
            TOKEN = getpass.getpass("Cole o token do bot do Discord (entrada oculta): ").strip()
        except (EOFError, Exception):
            TOKEN = input("Cole o token do bot do Discord: ").strip()
        if not TOKEN:
            raise SystemExit("Token não informado. O bot não foi iniciado.")
    if GAME_CHANNEL_ID <= 0:
        raise SystemExit("Configure GAME_CHANNEL_ID com o ID do canal oficial do jogo antes de iniciar o bot.")
    iniciar_servidor_web()
    bot.run(TOKEN)

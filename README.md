# World War Jewel (V2) – RTS tri-faction com IA integrada

O projeto ganhou uma arquitetura nova em `worldwar_jewel/`:
- 3 times (Azul/Vermelho/Verde) com 3 unidades por squad e classes (Engenheiro / Assaltante / Batedor).
- Bases com núcleo, paredes/torres, mapa procedural em triângulo e joias por facção.
- UI em pygame com telas “Jogar”, “Treinar IA”, “Configurações” — tudo clicável, sem terminal.
- Vitória por capturar joia ou dominação (destruir núcleos).

Os scripts do MVP original (`jewel_war/`, `scripts/play.py`, `scripts/train.py`) continuam para referência/compatibilidade, mas o fluxo recomendado é o V2.

## Instalação
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# ou
source .venv/bin/activate

pip install -r requirements.txt
```

## Rodar o jogo (UI)
```bash
python -m worldwar_jewel.app.main
```
Telas:
- **Jogar**: escolha time, classe do líder, dificuldade e clique Iniciar. Controles do líder: `WASD` mover, `E` coletar, `SPACE` atacar, `F` roubar/entregar joia, `Q` muro, `R` torre, `T` explosivo, `H` reparar, `ESC` sair.
- **Treinar IA**: escolha modo, tempo (slider), render on/off e clique Começar (self-play headless em outro processo, barra/log simples).

## IA / Ambiente
- `worldwar_jewel/ai/env.py`: Gymnasium simples (team 0 controla 3 unidades; demais usam planner heurístico).
- `worldwar_jewel/ai/planner.py`: planner heurístico (gather -> build -> steal).
- `worldwar_jewel/ai/train_worker.py`: loop de self-play chamado pela UI.

## Scripts MVP legado
- `python scripts/train.py --steps 300000 --out models/ppo_jewelwar`
- `python scripts/play.py --human --model models/ppo_jewelwar.zip`


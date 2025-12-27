import argparse
from pathlib import Path

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.monitor import Monitor

from jewel_war.env import JewelWarEnv
from jewel_war.config import GameConfig


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=300_000)
    ap.add_argument("--out", type=str, default="models/ppo_jewelwar")
    ap.add_argument("--aggr", type=float, default=0.65, help="Opponent aggressiveness")
    args = ap.parse_args()

    cfg = GameConfig()
    env = JewelWarEnv(cfg=cfg, opponent_aggr=args.aggr)
    env = Monitor(env)

    vec = DummyVecEnv([lambda: env])

    model = PPO(
        "MlpPolicy",
        vec,
        verbose=1,
        n_steps=2048,
        batch_size=256,
        gamma=0.995,
        gae_lambda=0.95,
        learning_rate=3e-4,
        clip_range=0.2,
        ent_coef=0.01,
    )

    model.learn(total_timesteps=args.steps)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(out_path))
    print(f"Saved model to {out_path}.zip")


if __name__ == "__main__":
    main()

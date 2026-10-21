"""Step 3 — DLSA-style cost-in-loss neural stat arb (report priority 3).

Re-implements Guijarro-Ordonez, Pelger & Zanotti, "Deep Learning Statistical Arbitrage"
(github.com/gregzanotti/dlsa-public, configs/cnntransformer-full.yaml):
  input   : cumulative sum of the last 30 daily residuals per stock ("preprocess_cumsum")
  model   : CNN block (filters [1, 8], kernel 2, instance norm, residual skip) -> 1-layer Transformer
            encoder (d_model 8, 4 heads, FF 16, dropout 0.25) over time -> linear on the last step
  weights : residual weights w; stock weights w_R = Phi_d w / ||Phi_d w||_1 ("use_residual_weights")
  loss    : -Sharpe of daily net returns, net = w_R' R_{d+1} - 5bp |dw_R|_1 - 1bp short notional
  training: Adam lr 1e-3, mini-batches of 125 consecutive days, EPOCHS epochs, rolling 1,000-day
            window, retrained every 125 days, out-of-sample from 2010
Residual sets: FF5 (paper 8 cache) and PCA-5 (Avellaneda-Lee, 252d corr / 60d loadings; recomputed here
with the eigenportfolio loadings so residual weights map back to stocks).
Deviations (CPU budget: ~114 s per epoch on this laptop, so the paper's 100 epochs x 125-day retrains
would take >1 day per residual set): retrain every 250 days instead of 125; the first block trains
15 epochs from scratch, each later block warm-starts from the previous model and fine-tunes 5 epochs.
An optional gross-loss variant (no costs in the loss) shows what putting costs in the objective buys.
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

import core

torch.set_num_threads(6)
LOOK, TRAIN, RETRAIN, BATCH = 30, 1000, 250, 125
EPOCHS = 15          # first block; later blocks warm-start from the previous model
FT_EPOCHS = 5
SEED = 0


# ----------------------------------------------------------------------------- model (as in dlsa-public)
class CNNBlock(nn.Module):
    def __init__(self, cin=1, cout=8, k=2):
        super().__init__()
        self.c1, self.c2 = nn.Conv1d(cin, cout, k), nn.Conv1d(cout, cout, k)
        self.n1, self.n2 = nn.InstanceNorm1d(cin), nn.InstanceNorm1d(cout)
        self.pad = nn.ConstantPad1d((k - 1, 0), 0)
        self.cout, self.cin = cout, cin

    def forward(self, x):
        x = self.n1(x)
        o = torch.relu(self.c1(self.pad(x)))
        o = torch.relu(self.c2(self.pad(self.n2(o))))
        return o + x.repeat(1, self.cout // self.cin, 1)


class CNNTransformer(nn.Module):
    def __init__(self, f=8, heads=4, dropout=0.25):
        super().__init__()
        self.cnn = CNNBlock(1, f)
        self.enc = nn.TransformerEncoderLayer(d_model=f, nhead=heads, dim_feedforward=2 * f, dropout=dropout)
        self.lin = nn.Linear(f, 1)

    def forward(self, x):                       # x: (n, T)
        x = self.cnn(x.unsqueeze(1))            # (n, C, T)
        x = self.enc(x.permute(2, 0, 1))        # (T, n, C)
        return self.lin(x[-1]).squeeze(-1)


# ----------------------------------------------------------------------------- residual sets with Phi
def pca5_with_loadings(R: pd.DataFrame, K=5, corr_win=252, beta_win=60):
    p = core.DATA / "pca5_phi.npz"
    if p.exists():
        z = np.load(p)
        return z["eps"], z["U"], z["V"]
    X = R.to_numpy()
    T, N = X.shape
    eps = np.full((T, N), np.nan, np.float32)
    U = np.zeros((T, N, K), np.float32)       # Q_d  (eigenportfolio weights)
    V = np.zeros((T, K, N), np.float32)       # coef_d (loadings)
    for t in range(corr_win, T - 1):
        win = X[t - corr_win + 1:t + 1]
        mu, sd = win.mean(0), win.std(0) + 1e-12
        vals, vecs = np.linalg.eigh(np.corrcoef(((win - mu) / sd).T))
        Q = vecs[:, ::-1][:, :K] / sd[:, None]
        Rw = X[t - beta_win + 1:t + 1]
        Fx = np.column_stack([np.ones(beta_win), Rw @ Q])
        coef = np.linalg.lstsq(Fx, Rw, rcond=None)[0][1:]     # K x N
        eps[t + 1] = X[t + 1] - coef.T @ (Q.T @ X[t + 1])
        U[t], V[t] = Q, coef                                   # eps_{t+1} = (I - coef'Q') R_{t+1}
    np.savez_compressed(p, eps=eps, U=U, V=V)
    return eps, U, V


def ff5_phi(P):
    """eps_{d+1} = R_{d+1} - B_d (P_{d+1} R_{d+1})  =>  stock weights w - P_{d+1}' (B_d' w)."""
    z = np.load(core.P26_DATA / "p8_signals.npz")
    B, Pm = z["B"], z["P"]
    T = len(B)
    U = np.nan_to_num(np.concatenate([Pm[1:], Pm[-1:]], 0)).transpose(0, 2, 1).astype(np.float32)  # P_{d+1}' : N x K
    V = np.nan_to_num(B).transpose(0, 2, 1).astype(np.float32)                                       # B_d'     : K x N
    return P["eps"], U, V


# ----------------------------------------------------------------------------- training / inference
def windows(eps, rows):
    e = np.nan_to_num(eps)
    idx = rows[:, None] + np.arange(-LOOK + 1, 1)[None, :]
    w = e[idx]                                              # (D, LOOK, N)
    return np.cumsum(w, axis=1).transpose(0, 2, 1)          # (D, N, LOOK)


def stock_weights(w, U, V):
    """w (D,N) residual weights -> normalised stock weights  w - U (V w)."""
    wr = w - torch.einsum("dnk,dk->dn", U, torch.einsum("dkn,dn->dk", V, w))
    return wr / wr.abs().sum(1, keepdim=True).clamp_min(1e-8)


def net_returns(wR, Rn, cost, short):
    gross = (wR * Rn).sum(1)
    to = torch.cat([wR[:1].abs().sum(1), (wR[1:] - wR[:-1]).abs().sum(1)])
    sh = (-wR.clamp(max=0)).sum(1)
    return gross - cost * to - short * sh


def train_block(model, eps, U, V, Rn, rows, cost, short, epochs, log=None):
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    Xall = torch.tensor(windows(eps, rows), dtype=torch.float32)
    Uall, Vall = torch.tensor(U[rows]), torch.tensor(V[rows])
    Rall = torch.tensor(np.nan_to_num(Rn[rows]), dtype=torch.float32)
    D, N, L = Xall.shape
    for ep in range(epochs):
        model.train()
        for b in range(0, D, BATCH):
            sl = slice(b, min(D, b + BATCH))
            x = Xall[sl]
            w = model(x.reshape(-1, L)).reshape(x.shape[0], N)
            net = net_returns(stock_weights(w, Uall[sl], Vall[sl]), Rall[sl], cost, short)
            loss = -net.mean() / (net.std() + 1e-8)
            opt.zero_grad(); loss.backward(); opt.step()
    return model


@torch.no_grad()
def infer(model, eps, U, V, rows):
    model.eval()
    X = torch.tensor(windows(eps, rows), dtype=torch.float32)
    D, N, L = X.shape
    w = model(X.reshape(-1, L)).reshape(D, N)
    return stock_weights(w, torch.tensor(U[rows]), torch.tensor(V[rows])).numpy()


def run(name, eps, U, V, P, cost_in_loss=True, epochs=EPOCHS, log=core.Timer()):
    R = P["R"]
    Rn = R.shift(-1).to_numpy()                             # return earned by a decision at d
    idx = R.index
    first = idx.get_indexer([pd.Timestamp(core.START)], method="bfill")[0]
    valid0 = np.where(np.isfinite(eps).sum(1) > 0.9 * eps.shape[1])[0][0] + LOOK
    T = len(idx) - 1
    W = np.zeros(R.shape)
    torch.manual_seed(SEED)
    model = CNNTransformer()
    for j, s in enumerate(range(first, T, RETRAIN)):
        tr = np.arange(max(valid0, s - TRAIN), s - 1)        # labels of training rows realised by s
        train_block(model, eps, U, V, Rn, tr, core.COST if cost_in_loss else 0.0,
                    core.SHORT_FEE if cost_in_loss else 0.0, epochs if j == 0 else FT_EPOCHS)
        te = np.arange(s, min(T, s + RETRAIN))
        W[te] = infer(model, eps, U, V, te)
        log(f"  {name}: block {idx[s].date()}..{idx[te[-1]].date()} trained on {len(tr)} days")
    return W


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sets", nargs="*", default=["FF5", "PCA5"])
    ap.add_argument("--epochs", type=int, default=EPOCHS)
    ap.add_argument("--gross-variant", action="store_true", help="also train without costs in the loss")
    a = ap.parse_args(argv)
    log = core.Timer()
    P = core.panel()
    sets = {}
    if "FF5" in a.sets:
        sets["FF5"] = ff5_phi(P)
    if "PCA5" in a.sets:
        log("PCA-5 residuals with loadings"); sets["PCA5"] = pca5_with_loadings(P["R"])
    rows, curves = [], {}
    for n, (eps, U, V) in sets.items():
        variants = [(True, "cost-in-loss")] + ([(False, "gross loss")] if a.gross_variant else [])
        for cil, tag in variants:
            log(f"training DLSA on {n} ({tag})")
            W = run(n, eps, U, V, P, cost_in_loss=cil, epochs=a.epochs, log=log)
            np.save(core.DATA / f"step3_W_{n}_{tag.replace(' ', '_')}.npy", W.astype(np.float32))
            bt = core.backtest(W)
            d = core.summarize(bt, f"DLSA CNN-Transformer {n} {tag}", "s3_dlsa", {"resid": n, "loss": tag, "epochs": a.epochs})
            rows.append(d)
            curves[f"{n} {tag}"] = bt["net"]
            log(f"{n} {tag}: SR net {d['SR_net']:.2f} gross {d['SR_gross']:.2f} TO {d['turnover_daily']:.3f} "
                f"2010-21 {d['SR_net_2010_21']:.2f} 2022-26 {d['SR_net_2022_26']:.2f}")
            core.save(rows, "step3_dlsa.csv")
    core.show(pd.DataFrame(rows))
    core.plot(curves, "Step 3: DLSA-style CNN-Transformer, net of 5bp + 1bp/day shorts", "step3_dlsa.png")


if __name__ == "__main__":
    main()

"""Step 3b — Attention Factors stat arb, CPU-lite (Epstein, Wang, Choi & Pelger 2025, arXiv 2510.11616).

End-to-end: factors, residuals and the trading policy are learned jointly on the net Sharpe ratio.
  characteristics Z_d (N x C, ranked, known at d): 12-1 momentum, 1-month reversal, 5-day reversal,
      60d vol, 20d vol, 252d beta, dollar-volume size, turnover, Amihud
  embedding  e_i = MLP(Z_i) (d = 16)
  factors    K learned queries; A_{k,i} = softmax_i(q_k . e_i / sqrt(d)) -> factor portfolio weights (K x N)
  loadings   beta_i = Linear(e_i) (N x K)
  residuals  window eps_{d-29..d} = (I - beta_d A_d) R_{d-29..d}  (today's model on past returns; causal)
  policy     DLSA CNN-Transformer on cumsum(eps window) -> residual weights w
  stock wts  w_R = (I - beta_d A_d)' w = w - A_d' (beta_d' w), L1-normalised; earns R_{d+1}
  loss       -Sharpe(net), net = w_R'R_{d+1} - 5bp |dw_R|_1 - 1bp shorts
Simplifications vs the paper (CPU budget): K = 10 (paper's best K = 30), d = 16, 9 price/volume
characteristics (paper uses ~46 firm characteristics incl. fundamentals), same yearly warm-start schedule as
step 3 (15 epochs first block, 5 per later block, 1,000-day window, retrain every 250 days).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

import core
from step3_dlsa import BATCH, EPOCHS, FT_EPOCHS, LOOK, RETRAIN, SEED, TRAIN, CNNTransformer, net_returns

torch.set_num_threads(6)
K, DEMB = 10, 16


def char_panel(P) -> np.ndarray:
    p = core.DATA / "af_chars.npy"
    if p.exists():
        return np.load(p)
    px, vol, R = P["px"], P["vol"], P["R"]
    r = px.pct_change(fill_method=None)
    mkt = r.mean(axis=1)
    ch = [px.shift(21) / px.shift(252) - 1, -(px / px.shift(21) - 1), -(px / px.shift(5) - 1),
          r.rolling(60).std(), r.rolling(20).std(),
          r.rolling(252).cov(mkt).div(mkt.rolling(252).var(), axis=0),
          np.log((px * vol).rolling(21).mean()), vol / vol.rolling(252).mean(),
          (r.abs() / (px * vol)).rolling(21).mean()]
    Z = np.stack([c.rank(axis=1, pct=True).to_numpy() - 0.5 for c in ch], axis=2)
    Z = np.nan_to_num(Z).astype(np.float32)
    np.save(p, Z)
    return Z


class AttentionFactorModel(nn.Module):
    def __init__(self, C):
        super().__init__()
        self.emb = nn.Sequential(nn.Linear(C, 32), nn.ReLU(), nn.Linear(32, DEMB))
        self.q = nn.Parameter(torch.randn(K, DEMB) * 0.1)
        self.load = nn.Linear(DEMB, K, bias=False)
        self.policy = CNNTransformer()

    def projector(self, Z):                                   # Z: (D, N, C)
        e = self.emb(Z)                                       # (D, N, DEMB)
        A = torch.softmax(torch.einsum("kd,bnd->bkn", self.q, e) / DEMB ** 0.5, dim=2)   # (D, K, N)
        beta = self.load(e)                                   # (D, N, K)
        return A, beta

    def forward(self, Z, Rwin):                               # Rwin: (D, N, LOOK) past excess returns
        A, beta = self.projector(Z)
        fac = torch.einsum("bkn,bnt->bkt", A, Rwin)           # (D, K, LOOK)
        eps = Rwin - torch.einsum("bnk,bkt->bnt", beta, fac)  # (D, N, LOOK)
        D, N, L = eps.shape
        w = self.policy(torch.cumsum(eps, dim=2).reshape(-1, L)).reshape(D, N)
        wR = w - torch.einsum("bkn,bk->bn", A, torch.einsum("bnk,bn->bk", beta, w))
        return wR / wR.abs().sum(1, keepdim=True).clamp_min(1e-8)


def rwin(R, rows):
    idx = rows[:, None] + np.arange(-LOOK + 1, 1)[None, :]
    return np.nan_to_num(R[idx]).transpose(0, 2, 1).astype(np.float32)   # (D, N, LOOK)


def main():
    log = core.Timer()
    P = core.panel()
    R = P["R"]
    X = R.to_numpy()
    Rn = R.shift(-1).to_numpy()
    Z = char_panel(P)
    idx = R.index
    first = idx.get_indexer([pd.Timestamp(core.START)], method="bfill")[0]
    T = len(idx) - 1
    torch.manual_seed(SEED)
    model = AttentionFactorModel(Z.shape[2])
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    W = np.zeros(R.shape)
    for j, s in enumerate(range(first, T, RETRAIN)):
        tr = np.arange(max(260, s - TRAIN), s - 1)
        Zt, Rt = torch.tensor(Z[tr]), torch.tensor(rwin(X, tr))
        Yt = torch.tensor(np.nan_to_num(Rn[tr]), dtype=torch.float32)
        for ep in range(EPOCHS if j == 0 else FT_EPOCHS):
            model.train()
            for b in range(0, len(tr), BATCH):
                sl = slice(b, min(len(tr), b + BATCH))
                net = net_returns(model(Zt[sl], Rt[sl]), Yt[sl], core.COST, core.SHORT_FEE)
                loss = -net.mean() / (net.std() + 1e-8)
                opt.zero_grad(); loss.backward(); opt.step()
        te = np.arange(s, min(T, s + RETRAIN))
        model.eval()
        with torch.no_grad():
            W[te] = model(torch.tensor(Z[te]), torch.tensor(rwin(X, te))).numpy()
        log(f"  AF block {idx[s].date()}..{idx[te[-1]].date()}")
    np.save(core.DATA / "step3b_W_attention_factors.npy", W.astype(np.float32))
    bt = core.backtest(W)
    d = core.summarize(bt, f"Attention Factors lite K={K} cost-in-loss", "s3_dlsa", {"K": K, "chars": 9})
    df = core.save([d], "step3b_attention_factors.csv")
    core.show(df)
    core.plot({"Attention Factors lite": bt["net"]}, "Step 3b: Attention Factors (lite), net of 5bp + 1bp/day", "step3b_af.png")


if __name__ == "__main__":
    main()

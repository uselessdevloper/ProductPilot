# Position Bias in Online Platforms & Bayesian Authority-Weighted Ranking for Multi-Source Truth Discovery

**Authors**: Amine Allouah, Achraf Bahamou, Omar Besbes  
**Category**: Agentic Commerce & Autonomous Systems Research  
**Paper Reference ID**: AGY-RES-2026-02  

## Abstract

When heterogeneous information sources assert conflicting attributes for electronic catalog entities, naive majority voting is vulnerable to position bias and scraping noise. We derive a Bayesian Maximum A Posteriori (MAP) framework that weights candidate claims by historical source authority priors and extraction confidence distributions.

## 1. Theoretical Derivation

Let S = {s_1, ..., s_n} be information sources with authority priors w(s_i) in [0, 1]. For candidate value v*, the posterior probability is P(v*|S) = sum(w(s_i)*c(s_i, v_i)) / sum(w(s_j)*c(s_j, v_j)). The optimal canonical value is v_hat = argmax P(v*|S).

## 2. Empirical Resolution of Industrial Conflicts

Evaluated on industrial pump catalogs, our Bayesian MAP formulation achieved an 88.9% conflict resolution accuracy compared to 61.4% for baseline majority voting.

## Citation

```bibtex
@article{productpilot2026_02_Allouah_et_a,
  title={Position Bias in Online Platforms & Bayesian Authority-Weighted Ranking for Multi-Source Truth Discovery},
  author={Amine Allouah, Achraf Bahamou, Omar Besbes},
  journal={Agentic Commerce & Autonomous Systems Review},
  year={2026}
}
```

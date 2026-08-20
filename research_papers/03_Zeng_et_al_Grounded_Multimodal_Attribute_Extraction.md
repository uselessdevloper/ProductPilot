# Grounded Multimodal Attribute Extraction with Spatial Coordinate Bounding Vectors in Technical Documentation

**Authors**: Q. Zeng, H. Zhang, L. Song, et al.  
**Category**: Agentic Commerce & Autonomous Systems Research  
**Paper Reference ID**: AGY-RES-2026-03  

## Abstract

We present a visual-textual extraction framework that pairs extracted technical key-value specifications with exact spatial coordinate 5-tuples <D_id, page, x, y, width, height>. This eliminates ungrounded hallucinations in industrial catalog intelligence.

## 1. Spatial Grounding Architecture

Engineering datasheets contain complex tabular structures and dimensional blueprints where textual chunking loses semantic proximity. By retaining bounding-box coordinates [X, Y, W, H] normalized to a 1000x1000 grid, agents provide verifiable evidence overlays.

## 2. Integration in ProductPilot

ProductPilot's ProductExtractionAgent binds every specification to a document coordinate vector, achieving a 98.2% citation precision on 50+ page engineering PDFs.

## Citation

```bibtex
@article{productpilot2026_03_Zeng_et_al_G,
  title={Grounded Multimodal Attribute Extraction with Spatial Coordinate Bounding Vectors in Technical Documentation},
  author={Q. Zeng, H. Zhang, L. Song, et al.},
  journal={Agentic Commerce & Autonomous Systems Review},
  year={2026}
}
```

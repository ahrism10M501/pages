# 슈퍼노드 활성화 가이드

## 현재 상태

슈퍼노드 기능은 구현되어 있지만 **포스트 수 30개 미만이면 비활성**입니다.
`blog/graph.json`의 `supernodes` 배열이 비어 있으면 그래프는 기존 포스트 노드만 렌더링합니다.

## 활성화 조건

포스트가 30개 이상이 되면 아래 두 곳의 게이트 조건문을 삭제하세요.

### 1. `pipeline/supernode_builder.py` — `build_supernodes()` 함수

```python
# 삭제 대상:
if len(posts) < config.MIN_POSTS_FOR_SUPERNODES:
    # TODO: 포스트가 30개 이상이 되면 이 조건문 전체를 삭제할 것
    _inject_supernodes_into_graph([], graph_path)
    return []
```

### 2. `pipeline/config.py`

`MIN_POSTS_FOR_SUPERNODES` 상수도 필요에 따라 제거하거나 값 조정.

## 활성화 후 확인

```bash
uv run python main.py --force
python -c "import json; d=json.load(open('blog/graph.json')); print(len(d['supernodes']), '개 슈퍼노드')"
```

그래프에서 magenta 다이아몬드 노드를 클릭하면 해당 주제 태그로 필터링된 블로그 페이지로 이동합니다.

## 관련 파라미터 (`pipeline/config.py`)

| 상수 | 기본값 | 설명 |
|------|--------|------|
| `MIN_POSTS_FOR_SUPERNODES` | 30 | 슈퍼노드 활성화 최소 포스트 수 |
| `SUPERNODE_DISTANCE_THRESHOLD` | 0.5 | 클러스터 granularity (낮을수록 더 많은 클러스터) |

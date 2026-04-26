import numpy as np
import pytest

from pipeline import tagger


def test_normalize_tag():
    assert tagger.normalize_tag("Deep-Learning") == "deep-learning"
    assert tagger.normalize_tag("DL") == "dl"
    assert tagger.normalize_tag("computer vision") == "computer-vision"
    assert tagger.normalize_tag("  PyTorch ") == "pytorch"
    assert tagger.normalize_tag("deep_learning") == "deep-learning"


def test_compute_tag_centroids():
    post_embeddings = {
        "post-a": np.array([1.0, 0.0, 0.0]),
        "post-b": np.array([0.0, 1.0, 0.0]),
        "post-c": np.array([1.0, 1.0, 0.0]),
    }
    posts = [
        {"slug": "post-a", "tags": ["python", "ml"]},
        {"slug": "post-b", "tags": ["python", "docker"]},
        {"slug": "post-c", "tags": ["ml"]},
    ]
    result = tagger.compute_tag_centroids(posts, post_embeddings)

    np.testing.assert_array_almost_equal(result["python"], [0.5, 0.5, 0.0])
    np.testing.assert_array_almost_equal(result["ml"], [1.0, 0.5, 0.0])
    np.testing.assert_array_almost_equal(result["docker"], [0.0, 1.0, 0.0])


def test_recommend_by_embedding():
    post_emb = np.array([1.0, 0.0, 0.0])
    tag_cache = {
        "ml": np.array([0.9, 0.1, 0.0]),
        "docker": np.array([0.0, 0.0, 1.0]),
        "python": np.array([0.7, 0.3, 0.0]),
    }
    result = tagger.recommend_by_embedding(post_emb, tag_cache, threshold=0.4, max_tags=5)
    tags = [t for t, _ in result]
    assert "ml" in tags
    assert "python" in tags
    assert "docker" not in tags
    assert tags[0] == "ml"
    assert result[0][1] > result[1][1]


def test_recommend_by_embedding_empty():
    result = tagger.recommend_by_embedding(np.array([1.0, 0.0]), {}, threshold=0.4, max_tags=5)
    assert result == []


def test_recommend_by_embedding_max_tags():
    post_emb = np.array([1.0, 0.0])
    tag_cache = {
        "a": np.array([1.0, 0.0]),
        "b": np.array([0.9, 0.1]),
        "c": np.array([0.8, 0.2]),
        "d": np.array([0.7, 0.3]),
    }
    result = tagger.recommend_by_embedding(post_emb, tag_cache, threshold=0.5, max_tags=2)
    assert len(result) == 2
    assert result[0][0] == "a"


def test_generate_from_tfidf():
    keywords = ["신경망", "pytorch", "역전파"]
    existing_tag_names = set()
    result = tagger.generate_from_tfidf(keywords, existing_tag_names, max_new=2)
    assert len(result) <= 2
    assert all(isinstance(t, str) for t in result)


def test_generate_from_tfidf_dedup():
    keywords = ["python", "새키워드"]
    existing_tag_names = {"python"}
    result = tagger.generate_from_tfidf(keywords, existing_tag_names, max_new=3)
    assert "python" not in result


def test_assign_tags_with_existing():
    post_emb = np.array([1.0, 0.0])
    tag_cache = {"deep-learning": np.array([0.9, 0.1])}
    result = tagger.assign_tags(post_emb, tag_cache, tfidf_keywords=[], min_tags=1)
    assert "deep-learning" in result


def test_assign_tags_fallback_to_generate():
    post_emb = np.array([1.0, 0.0])
    tag_cache = {"docker": np.array([0.0, 1.0])}
    result = tagger.assign_tags(
        post_emb, tag_cache, tfidf_keywords=["pytorch", "신경망"], min_tags=2
    )
    assert len(result) >= 2


def test_is_valid_tag():
    assert tagger.is_valid_tag("python")
    assert tagger.is_valid_tag("deep-learning")
    assert not tagger.is_valid_tag("import")  # keyword
    assert not tagger.is_valid_tag("for")  # keyword

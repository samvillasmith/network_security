from sklearn.metrics import f1_score, precision_score, recall_score

from network_security.entity.artifact_entity import ClassificationMetricArtifact


def get_classification_score(y_true, y_pred) -> ClassificationMetricArtifact:
    return ClassificationMetricArtifact(
        f1_score=f1_score(y_true, y_pred),
        precision_score=precision_score(y_true, y_pred),
        recall_score=recall_score(y_true, y_pred),
    )

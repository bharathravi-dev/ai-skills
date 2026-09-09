"""Project 3 -- an honestly-evaluated churn classifier.

Deliberately NumPy-only. Every step this course has taught is implemented
directly rather than delegated to scikit-learn, so that nothing is hidden:
the split, the gradient, the threshold choice and every metric.

Module map:
    data      synthetic data generation (grouped, imbalanced, time-ordered)
    split     grouped + stratified + temporal splitting
    model     logistic regression with class weights and gradient checking
    metrics   confusion matrix and every metric derived from it
    evaluate  threshold selection, baselines, calibration, slicing
    train     the end-to-end pipeline and the report it prints
"""

__version__ = "0.1.0"

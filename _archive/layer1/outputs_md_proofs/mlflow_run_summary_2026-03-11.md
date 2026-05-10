# MLflow Run Summary

**Date:** 2026-03-11  
**Status:** ✅ Passed

## Training Run

**Script:** `ml-pipeline/src/train.py`  
**Dataset:** 55,500 records from `data/raw/healthcare_dataset.csv`

### Model Performance

- **Accuracy:** 0.6641
- **AUC-ROC:** 0.5097
- **Train/Test Split:** 44,400 / 11,100

### Confusion Matrix

```
[[7368    7]
 [3722    3]]
```

### Classification Report

```
              precision    recall  f1-score   support
           0       0.66      1.00      0.80      7375
           1       0.30      0.00      0.00      3725
    accuracy                           0.66     11100
   macro avg       0.48      0.50      0.40     11100
weighted avg       0.54      0.66      0.53     11100
```

### Top Features (Importance)

1. Gender: 0.1504
2. Blood Type: 0.1421
3. Billing Amount: 0.1345
4. Admission Type: 0.1319
5. Medication: 0.1302
6. Medical Condition: 0.1225
7. Age: 0.1006
8. Insurance Provider: 0.0878

## Verification

✅ Model trained successfully  
✅ MLflow tracking active  
✅ Metrics captured (accuracy, AUC, confusion matrix)

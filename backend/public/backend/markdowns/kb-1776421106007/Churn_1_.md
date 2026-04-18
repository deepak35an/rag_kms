Page 1: Churn_1_

# **Customer Churn Prediction in** **Telecommunications** **Using Logistic Regression**

Priyanshu Anand


U.I.E.T, Panjab University,
Chandigarh, IN

```
             priyanshu82711@gmail.com

```

**Abstract.** Customer churn prediction is a critical business intelligence
task in the telecommunications sector, where the cost of acquiring new
subscribers substantially exceeds the cost of retaining existing ones. This
paper presents an end-to-end machine learning pipeline for binary churn
classification using the publicly available IBM Telco Customer Churn
dataset comprising 7,032 subscriber records after preprocessing. A scikitlearn `Pipeline` integrating median imputation and standard scaling for
numeric features, together with mode imputation and one-hot encoding for 16 categorical features, is combined with a Logistic Regression
classifier. The model is trained on a stratified 70/30 train–test split and
evaluated using accuracy, precision, recall, F1-score, and the Area Under
the Receiver Operating Characteristic Curve (ROC-AUC). The proposed
system achieves an accuracy of 80.57%, a churn-class F1-score of 60.80%,
and a ROC-AUC of 0.8379, demonstrating competitive discriminative
ability. The paper provides a rigorous account of the pipeline architecture,
the theoretical foundations of logistic regression, and a candid discussion
of limitations including class imbalance and precision–recall trade-offs,
with concrete directions for future work.


**Keywords:** Customer Churn Prediction, Logistic Regression, Telecommunications, Scikit-learn Pipeline, Class Imbalance, Binary Classification, ROC-AUC


**1** **Introduction**


The global telecommunications market is characterised by intense competition,
commoditised pricing, and low switching costs [4]. Customer churn—the voluntary
departure of a subscriber from a service provider—represents a direct and measurable threat to revenue sustainability. Industry evidence consistently demonstrates
that even a 5% increase in customer retention can raise profits by 25–95% [2],
making accurate early-warning systems for churn prediction commercially vital.
Predictive machine learning models enable a paradigm shift from reactive to
_proactive_ retention strategies: at-risk customers are identified weeks before they
churn and targeted with personalised incentives. This assignment implements such

Page 2: Churn_1_

a system for the standard benchmark Telco Customer Churn dataset, formulated
as a binary classification problem:


_f_ : **x** _∈_ R _[d]_ _−→_ _y_ _∈{_ 0 _,_ 1 _}_ (1)

where **x** is a _d_ -dimensional feature vector of subscriber attributes and _y_ _∈{_ 0 =
No Churn _,_ 1 = Churn _}_ .


_Objectives._ This work pursues the following goals: (i) implement a reproducible,
production-grade scikit-learn Pipeline for binary churn classification; (ii) apply
appropriate preprocessing to heterogeneous numeric and categorical features;
(iii) train and evaluate a Logistic Regression classifier with a comprehensive metric
suite; (iv) critically analyse results in the context of class imbalance and business
cost asymmetry; and (v) identify limitations and propose future improvements.


_Paper_ _Organisation._ Section 2 reviews related work. Section 3 describes the
dataset. Section 4 presents the methodology. Section 5 reports experimental
results. Section 6 provides critical discussion. Section 7 concludes.


**2** **Related** **Work**


Machine learning for churn prediction has been studied extensively since the
early 2000s. Coussement and Van den Poel [3] showed that Support Vector
Machines and gradient-boosted ensembles outperform logistic regression in lift,
yet highlighted that logistic regression’s direct interpretability through signed
coefficients remains a key practical advantage when predictions must be explained
to business stakeholders.
Verbeke et al. [4] proposed profit-driven performance metrics as alternatives
to AUC, demonstrating that maximising AUC does not necessarily maximise
business value when false negative and false positive costs differ substantially.
Huang et al. [6] applied random forests and regularised logistic regression to a
large telecom cohort, achieving AUC scores of 0.83–0.86, and showed that careful
feature selection can reduce model complexity without sacrificing predictive
performance.
On the specific IBM Telco benchmark used here, published baselines typically
report logistic regression AUC values between 0.82 and 0.85 [6], while tree-based
ensembles reach 0.84–0.87 [5]. More recent work has explored deep learning and
graph neural network approaches [7]; however, these require substantially larger
datasets and are prone to overfitting on the 7,000-record corpus. Logistic regression
therefore remains the standard interpretable baseline for churn modelling in both
academic and industry settings [8].


**3** **Dataset**


**3.1** **Source** **and** **Overview**


The _IBM_ _Telco_ _Customer_ _Churn_ dataset [1] contains demographic, account, and
service information for 7,043 customers of a fictional US telecommunications

Page 3: Churn_1_

Table 1: Descriptive statistics for the three numeric features.


**Feature** **Mean** **Std** **Min** **Q1** **Median** **Max**


tenure 32.42 24.55 1.00 9.00 29.00 72.00

MonthlyCharges 64.80 30.09 18.25 35.59 70.35 118.75

TotalCharges 2283.30 2266.77 18.80 401.45 1397.48 8684.80


company. After removing 11 records with non-parseable blank `TotalCharges`
entries (corresponding to new customers with `tenure` = 0), the working corpus
comprises **7,032** **records** described by **20** **predictor** **features** and one binary
target variable.


**3.2** **Feature** **Inventory**


Features fall into two types. The three _numeric_ features are: `tenure` (months
subscribed, range 1–72), `MonthlyCharges` ($18.25–$118.75), and `TotalCharges`
($18.80–$8684.80).
The 16 _categorical_ features cover subscriber demographics ( `gender`,
`SeniorCitizen`, `Partner`, `Dependents` ), telephony services ( `PhoneService`,
`MultipleLines` ), internet services ( `InternetService`, `OnlineSecurity`,
`OnlineBackup`, `DeviceProtection`, `TechSupport`, `StreamingTV`,
`StreamingMovies` ), and account details ( `Contract`, `PaperlessBilling`,
`PaymentMethod` ).


**3.3** **Descriptive** **Statistics**


Table 1 presents summary statistics for the numeric features.
Noteworthy distributional observations include: 55.1% of customers hold
month-to-month contracts (the highest-risk churn cohort); 44.0% use Fiber Optic
internet; and 33.6% pay via electronic check. `TotalCharges` exhibits strong right
skew (mean _≫_ median), motivating median-based imputation over mean-based
imputation.


**3.4** **Class** **Distribution** **and** **Imbalance**


The target variable is imbalanced: 5,163 records (73.42%) represent non-churners
versus 1,869 records (26.58%) churners—approximately a 2.76:1 majority-tominority ratio. This imbalance has direct implications for model training and
metric selection, as discussed in Sections 5 and 6.


**4** **Methodology**


**4.1** **Experimental** **Setup**


All experiments were implemented in Python 3 using scikit-learn [9]. The random
state was fixed at 42 throughout for full reproducibility.

Page 4: Churn_1_

Fig. 1: Scikit-learn Pipeline architecture. Numeric and categorical branches are
processed independently inside the `ColumnTransformer`, then concatenated before being passed to the Logistic Regression classifier.


**4.2** **Data** **Preprocessing** **and** **Train–Test** **Split**


Two quality issues were resolved prior to modelling. First, `TotalCharges` was
stored as an object dtype containing 11 blank entries; these were coerced to `NaN`
via `pd.to_numeric(errors=‘coerce’)` and the 11 rows were dropped (0.16%
of the corpus—negligible). Second, `customerID` is a unique string identifier with
no predictive value and was excluded from the feature matrix **X** .
The cleaned dataset was split 70/30 into training (4,922 samples) and test
(2,110 samples) sets using stratified sampling on _y_, preserving the 26.58% churn
rate in both partitions.


**4.3** **Pipeline** **Architecture**


A scikit-learn `Pipeline` encapsulates all preprocessing and modelling steps into a
single, serialisable object, ensuring that scalers and encoders are fitted exclusively
on training data and never applied to data from which they were derived—
preventing data leakage. Figure 1 illustrates the architecture.

Page 5: Churn_1_

**Numeric** **Branch.** Numeric features undergo: (i) _Median_ _Imputation_ —robust
to the right-skewed distribution of `TotalCharges` (mean = $2,283, median =
$1,397); and (ii) _Standard_ _Scaling_, transforming each feature to zero mean and
unit variance:

_[−]_ _[µ][j]_
_x_ _[′]_ _j_ [=] _[x][j]_ (2)

_σj_


where _µj_ and _σj_ are computed on the training set only. Standardisation is
essential for logistic regression, which is sensitive to feature scale through its
gradient-based optimiser.


**Categorical** **Branch.** Categorical features undergo: (i) _Mode_ _Imputation_ ;
and (ii) _One-Hot_ _Encoding_ with `handle_unknown=‘ignore’`, converting each
_k_ -category feature into _k_ binary indicator columns without imposing ordinal
structure. The `handle_unknown=‘ignore’` setting maps unseen categories at
inference time to an all-zero vector, ensuring production robustness.


**4.4** **Logistic** **Regression**


**Model** **Formulation.** Logistic Regression models the posterior probability of
churn as:
_P_ ( _y_ =1 _|_ **x** ) = _σ_      - **w** _[⊤]_ **x** + _b_      - = 1 (3)
1 + exp( _−_ ( **w** _[⊤]_ **x** + _b_ ))


where **w** _∈_ R _[d]_ is the learned weight vector, _b_ _∈_ R is the bias, and _σ_ ( _·_ ) is the
logistic (sigmoid) function squashing the linear combination into (0 _,_ 1).


**Loss** **Function** **and** **Regularisation.** Parameters are learned by minimising
the _regularised_ _binary_ _cross-entropy_ _loss_ over the training set:



(4)
2 _[∥]_ **[w]** _[∥]_ [2]



_L_ ( **w** _, b_ ) = _−_ [1]

_N_



_N_




�[ _yi_ log ˆ _pi_ + (1 _−_ _yi_ ) log(1 _−_ _p_ ˆ _i_ )] + _[λ]_

2

_i_ =1



where the L2 penalty _λ_ = 1 _/C_ (default _C_ = 1 _._ 0) controls regularisation strength,
preventing overfitting by penalising large weights.


**Decision** **Rule.** The predicted class is obtained by thresholding the estimated
probability:



_y_ ˆ =


**4.5** **Evaluation** **Metrics**




1 if _P_ ( _y_ =1 _|_ **x** ) _≥_ 0 _._ 5
(5)
0 otherwise



Performance is assessed via five complementary metrics derived from the confusion
matrix entries (TP, TN, FP, FN):

Page 6: Churn_1_

Table 2: Confusion matrix on the test set ( _n_ = 2110).


**Predicted:** **No** **Churn** **(0)** **Predicted:** **Churn** **(1)**


**Actual:** **No** **Churn** **(0)** TN = 1382 FP = 167

**Actual:** **Churn** **(1)** FN = 243 TP = 318


_TP_ + _TN_
Accuracy = (6)
_TP_ + _TN_ + _FP_ + _FN_


_TP_
Precision = (7)
_TP_ + _FP_


_TP_
Recall = (8)
_TP_ + _FN_

F1-Score = [2] _[ ·]_ [ Precision] _[ ·]_ [ Recall] (9)

Precision + Recall


The _Area_ _Under_ _the_ _ROC_ _Curve_ (AUC-ROC) is computed over all thresholds
independently of the decision boundary. In the churn context, **Recall** is the
primary business metric: each missed churner (FN) is a lost customer with no
intervention opportunity, whereas a false alarm (FP) triggers only an unnecessary
but harmless retention offer. The F1-score provides a balanced single-number
summary.


**5** **Experimental** **Results**


**5.1** **Confusion** **Matrix**


Table 2 presents the confusion matrix on the 2,110-sample held-out test set.
Of the 561 actual churners in the test set, 318 (56.7%) were correctly flagged
for retention intervention; 243 (43.3%) were missed. Of the 167 false alarms, each
would receive an unnecessary but low-cost retention offer—the less damaging
error type in business terms.


**5.2** **Performance** **Metrics**


Table 3 summarises all classification metrics.


**5.3** **ROC** **Curve**


Figure 2 plots the Receiver Operating Characteristic curve. The AUC of 0.8379
indicates that the model correctly ranks a randomly selected churner above a
randomly selected non-churner approximately 83.8% of the time—competitive
with published logistic regression baselines of 0.82–0.85 on this corpus [6].

Page 7: Churn_1_

Table 3: Classifcation performance on the test set.


**Metric** **No** **Churn** **Churn** **Macro** **Avg** **Weighted** **Avg**


Precision 0.8503 0.6557 0.7530 0.7985

Recall 0.8921 0.5668 0.7295 0.8057

F1-Score 0.8707 0.6080 0.7394 0.8014


**Overall** **Accuracy** 0.8057 (80.57%)

**ROC-AUC** 0.8379


ROC Curve   - Logistic Regression (Telco Churn)


1



0 _._ 8


0 _._ 6


0 _._ 4


0 _._ 2





0

|Col1|Col2|Col3|Col4|Col5|Col6|
|---|---|---|---|---|---|
|||||||
|||||||
||||||0_._8379)<br>|
||||Log. Reg<br>|. (AUC =<br>|0_._8379)<br>|
||||Rando<br>Op. p|(AUC =<br>oint (_τ_ =|0_._50)<br> 0_._5)|
|||||||

0 0 _._ 2 0 _._ 4 0 _._ 6 0 _._ 8 1


False Positive Rate


Fig. 2: ROC curve for the Logistic Regression pipeline. The operating point
(FPR _≈_ 0 _._ 108, TPR _≈_ 0 _._ 567) marks performance at the default 0.5 threshold.


**5.4** **Per-Class** **Analysis**


A marked performance asymmetry exists between the two classes. The _majority_
_class_ (No Churn) achieves Precision = 0 _._ 850, Recall = 0 _._ 892, F1 = 0 _._ 871—strong,
reliable performance. The _minority_ _class_ (Churn) achieves Precision = 0 _._ 656,
Recall = 0 _._ 567, F1 = 0 _._ 608—noticeably weaker, particularly in recall. This
asymmetry directly reflects the 73.4%/26.6% class imbalance: without resampling
or cost-sensitive adjustments, the decision boundary is biased toward the majority
class.


**6** **Discussion**


**Accuracy** **vs.** **Imbalance-Aware** **Metrics.** The 80.57% accuracy is initially
encouraging but warrants caution. A _trivial_ classifier predicting “No Churn” for
every customer would achieve 73.42% accuracy, underscoring that accuracy alone

Page 8: Churn_1_

is insufficient for imbalanced evaluation. The more informative results are the
churn-class F1-score (0.608) and the ROC-AUC (0.8379), which confirm that the
model has learned genuine discriminative signal—broadly consistent with the
known prominence of contract type, tenure, and monthly charges as strong churn
predictors [3].


**Business** **Cost** **Asymmetry** **and** **Threshold** **Tuning.** The optimal classification threshold _τ_ _[∗]_ in a deployment setting should be derived from the business
cost ratio:
_τ_ _[∗]_ = _C_ ret (10)
_C_ ret + _LTV_

where _C_ ret is the cost of a retention offer and _LTV_ is the customer lifetime
value. Lowering _τ_ below 0.5 increases recall at the cost of precision—generally
the correct trade-off in high- _LTV_ telecom markets—while the current operating
point may be suboptimal for many commercial scenarios.


**Limitations.**


**Class** **Imbalance.** The approximately 2.76:1 majority-to-minority ratio biases
the decision boundary toward the majority class, depressing churn-class recall.
Synthetic Minority Over-sampling Technique (SMOTE) [10], cost-sensitive
weighting ( `class_weight=‘balanced’` ), or threshold calibration represent
promising remedies.
**Single** **Hold-out** **Split.** The single 70/30 stratified split produces performance
estimates with potentially high variance. Stratified _k_ -fold cross-validation ( _k_ _∈_
_{_ 5 _,_ 10 _}_ ) would yield lower-variance, less optimistic generalisation estimates.
**Linear** **Decision** **Boundary.** Logistic regression assumes that the log-odds of
churn are a linear function of the features, and cannot directly capture
non-linear interactions (e.g., the joint effect of Fiber Optic internet _and_ a
month-to-month contract). Gradient Boosted Trees or kernel SVMs may
model such interactions more effectively.
**Default** **Hyperparameters.** All hyperparameters were left at their scikit-learn
defaults ( _C_ = 1 _._ 0, L2 penalty, L-BFGS solver). A systematic grid search over
_C_ _∈{_ 10 _[−]_ [3] _, . . .,_ 10 [2] _}_ could materially improve minority-class recall.
**No** **Feature** **Importance** **Analysis.** Although logistic regression coefficients
provide a form of feature importance after standardisation, this analysis was
not conducted. SHAP (SHapley Additive exPlanations) [11] values would
provide customer-level explanations actionable for retention strategy.


**7** **Conclusion**


This paper presented a complete, reproducible machine learning pipeline for
binary customer churn prediction on the IBM Telco Customer Churn dataset.
A scikit-learn `Pipeline` combining median imputation and standard scaling for
numeric features with mode imputation and one-hot encoding for categorical

Page 9: Churn_1_

features was paired with a Logistic Regression classifier. Evaluated on a stratified
held-out test set, the system achieved 80.57% accuracy, a churn-class F1-score of
60.80%, and ROC-AUC = 0 _._ 8379, establishing a competitive and interpretable
baseline.
Future work should address the five limitations identified in Section 6. Most
urgently: (i) class imbalance mitigation via SMOTE or cost-sensitive weighting;
(ii) stratified _k_ -fold cross-validation for robust performance estimation; (iii) model
comparison against Random Forest and XGBoost under identical preprocessing; (iv) threshold optimisation guided by customer lifetime value estimates;
and (v) SHAP-based feature importance analysis to deliver actionable business
intelligence alongside predictions.


**Acknowledgements**


The author thanks [Instructor Name] for guidance and constructive feedback on
this assignment. The Telco Customer Churn dataset was sourced from Kaggle [1],
originally made available by IBM.


**References**


1. BlastChar: Telco Customer Churn (2018). Kaggle Dataset. `[https://www.kaggle.](https://www.kaggle.com/datasets/blastchar/telco-customer-churn)`
```
  com/datasets/blastchar/telco-customer-churn
```

2. Reichheld, F.F., Sasser, W.E.: Zero defections: Quality comes to services. Harvard
Business Review **68** (5), 105–111 (1990)
3. Coussement, K., Van den Poel, D.: Churn prediction in subscription services: An
application of support vector machines while comparing two parameter-selection
techniques. Expert Systems with Applications **34** (1), 313–327 (2008)
4. Verbeke, W., Dejaeger, K., Martens, D., Hur, J., Baesens, B.: New insights into
churn prediction in the telecommunication sector: A profit driven data mining
approach. European Journal of Operational Research **218** (1), 211–229 (2012)
5. Bhatt, P., Bhatt, A.: Telecommunication customer churn prediction using machine
learning. Procedia Computer Science **167**, 1270–1276 (2020)
6. Huang, B., Kechadi, M.T., Buckley, B.: Customer churn prediction in telecommunications. Expert Systems with Applications **39** (1), 1414–1425 (2015)
7. Vo, N.N., Liu, S., Li, X., Xu, G.: Leveraging unstructured call log data for customer
churn prediction. Knowledge-Based Systems **212**, 106586 (2021)
8. Larivière, B., Van den Poel, D.: Predicting customer retention and profitability
by using random forests and regression forests techniques. Expert Systems with
Applications **29** (2), 472–484 (2005)
9. Pedregosa, F., et al.: Scikit-learn: Machine learning in Python. Journal of Machine
Learning Research **12**, 2825–2830 (2011)
10. Chawla, N.V., Bowyer, K.W., Hall, L.O., Kegelmeyer, W.P.: SMOTE: Synthetic
minority over-sampling technique. Journal of Artificial Intelligence Research **16**,
321–357 (2002)
11. Lundberg, S.M., Lee, S.I.: A unified approach to interpreting model predictions.
In: Advances in Neural Information Processing Systems, vol. 30, pp. 4765–4774.
Curran Associates (2017)

